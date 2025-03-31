import unittest
import asyncio
import subprocess
import os
import io
import sys
import copy
import json
import tarfile
from pathlib import Path

import asyncpg
from unittest.mock import patch, MagicMock, mock_open
from docker.errors import DockerException, NotFound

from pg_perfbench.connections.docker import DockerConnection
from pg_perfbench.db_operations import DBTasks
from pg_perfbench.log import setup_logger
from pg_perfbench.const import (
    LogLevel,
    WorkloadTypes,
    BENCHMARK_TEMPLATE_JSON_PATH,
    get_datetime_report
)
from pg_perfbench.report.processing import save_report, get_report_structure
from pg_perfbench.report.commands import fill_info_report
from pg_perfbench.benchmark import load_iterations_config, get_pgbench_results
from pg_perfbench.join import _merge_reports


def run_command(cmd_list, check=True):
    """
    Runs a shell command via subprocess.
    If check=True, raises an error on non-zero return code.
    """
    if isinstance(cmd_list, str):
        # If a string is passed, split it to handle arguments properly.
        cmd_list = cmd_list.split()

    result = subprocess.run(cmd_list, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed with code {result.returncode}: {cmd_list}\n"
            f"STDERR: {result.stderr}"
        )
    return result


class DataEnvTest:
    def __init__(self):
        self.pg_version_list = ["14", "15", "16", "17"]
        # self.pg_version_list = ["14"]
        self.cntr_name_list = [f"pg_perfbench_test_{pgv}" for pgv in self.pg_version_list]
        self.cntr_image_name_list = [f"postgres:{pgv}" for pgv in self.pg_version_list]

        self.cntr_forwarded_port = 5439
        self.db_params_list = [
            {
                "user": "postgres",
                "password": "pswd",
                "database": "tdb",
                "host": "127.0.0.1",
                "port": self.cntr_forwarded_port + idx
            }
            for idx in range(len(self.pg_version_list))
        ]
        self.workload = {
            "init_command": "ARG_PGBENCH_PATH -i --scale=10 --foreign-keys -p ARG_PG_PORT -h ARG_PG_HOST -U postgres ARG_PG_DATABASE",
            "workload_command": "ARG_PGBENCH_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U ARG_PG_USER ARG_PG_DATABASE -c ARG_PGBENCH_CLIENTS -j 10 -T 10 --no-vacuum",
            "pgbench_path": "pgbench",
            "benchmark_type": WorkloadTypes.DEFAULT,
            "pg_data_path": "/var/lib/postgresql/data",
            "pgbench_iter_name": "pgbench_clients",
            "pgbench_iter_list": [3]
        }
        self.db_env = [
            {
                "pg_bin_path": f"/usr/lib/postgresql/{pgv}/bin"
            }
            for pgv in self.pg_version_list
        ]

        self.DockerConnectionObjList = []
        # Paths for templates, results, etc.
        self.root_path = Path(os.environ.get("PYTHONPATH", ""))
        self.test_template_path = os.path.join(
            str(self.root_path), "tests", "integration", "test_template.json"
        )
        self.result_reports_path = os.path.join(
            str(self.root_path), "tests", "integration", "result"
        )
        self.expected_reports_path = os.path.join(
            str(self.root_path), "tests", "integration", "expected"
        )

        self.logger = setup_logger(LogLevel.INFO, False)

        self.join_tasks = [
            "sections.system.reports.etc_os_release.data",
            "sections.db.reports.version_major.data",
            "sections.db.reports.pg_available_extensions.data",
            "sections.benchmark.reports.options.data",
            "sections.benchmark.reports.custom_tables.data",
            "sections.benchmark.reports.custom_workload.data"
        ]


dataEnv = DataEnvTest()


class Test_01_LocalEnvironment(unittest.IsolatedAsyncioTestCase):
    """
    Basic checks to ensure local environment is ready:
    1) pgbench and psql are installed
    2) Docker is accessible
    """

    async def test_check_pg_utils_exists(self):
        """
        Verify that pgbench and psql are installed and accessible to the user's PATH.
        """
        try:
            result = run_command(["pgbench", "--version"])
            self.assertIn(
                "postgres",
                result.stdout.lower(),
                "pgbench not found. Install it (e.g., 'sudo apt install postgresql-contrib')."
            )
        except RuntimeError as e:
            self.fail(f"pgbench check failed: {e}")

        try:
            result = run_command(["psql", "--version"])
            self.assertIn(
                "postgres",
                result.stdout.lower(),
                "psql not found. Install it (e.g., 'sudo apt install postgresql-client')."
            )
        except RuntimeError as e:
            self.fail(f"psql check failed: {e}")

    async def test_docker_permissions(self):
        """
        Verify that the user has permissions to run Docker commands.
        In particular, checks 'docker ps' for any permission errors.
        """
        try:
            result = run_command(["docker", "ps"])
            self.assertIn(
                "CONTAINER ID",
                result.stdout,
                "Unexpected output from 'docker ps' – possibly Docker isn't working correctly."
            )
        except RuntimeError as e:
            self.fail(f"User does not have permissions to run Docker commands: {e}")


class Test_02_DockerConnection(unittest.IsolatedAsyncioTestCase):
    """
    Main test class to create Docker containers, run a minimal pgbench scenario,
    and optionally compare results with expected data.
    """

    @classmethod
    def setUpClass(cls):
        # Pull images and set up containers
        for container_name, image_name, db_params, db_env in zip(
                dataEnv.cntr_name_list,
                dataEnv.cntr_image_name_list,
                dataEnv.db_params_list,
                dataEnv.db_env
        ):
            dataEnv.logger.info(f"\n--> Pulling Docker image: {image_name}")
            run_command(["docker", "pull", image_name], check=True)

            dataEnv.logger.info(f"\n--> Stopping/removing any existing container '{container_name}'...")
            run_command(["docker", "stop", container_name], check=False)
            run_command(["docker", "rm", "-f", container_name], check=False)

            dataEnv.logger.info(f"\n--> Starting container '{container_name}' in trust mode...")
            run_command([
                "docker",
                "run",
                "-d",
                "--name", container_name,
                "-p", f"{db_params['port']}:5432",
                "-e", "POSTGRES_HOST_AUTH_METHOD=trust",
                "-e", f"POSTGRES_DB={db_params['database']}",
                "-e", f"POSTGRES_USER={db_params['user']}",
                image_name,
            ], check=True)

            conn_params = {"container_name": container_name}
            env_params = {
                "env": {
                    "ARG_PG_BIN_PATH": db_env["pg_bin_path"]
                }
            }
            DockerConnectionObj = DockerConnection(conn_params, env_params)
            dataEnv.DockerConnectionObjList.append(DockerConnectionObj)

    @classmethod
    def tearDownClass(cls):
        # Cleanup containers
        for i, container_name in enumerate(dataEnv.cntr_name_list):
            dataEnv.logger.info(f"\n--> Cleaning up container '{container_name}'...")
            run_command(["docker", "stop", container_name], check=False)
            run_command(["docker", "rm", "-f", container_name], check=False)

    def setUp(self):
        """
        Sanity check for DockerConnection objects existence.
        """
        if not dataEnv.DockerConnectionObjList:
            dataEnv.logger.warning("No DockerConnection objects found; tests may fail.")

    async def test_01_run_benchmarks(self):
        """
        Demonstrates a minimal pgbench scenario within each container.
        """
        for docker_conn, db_params, db_env_conf, pg_version in zip(
                dataEnv.DockerConnectionObjList,
                dataEnv.db_params_list,
                dataEnv.db_env,
                dataEnv.pg_version_list
        ):
            try:
                # 1) Start the Docker connection (container is already running, but start() may set up internal states)
                await docker_conn.start()

                # 2) Create a copy of the base workload configuration
                workload_conf = copy.deepcopy(dataEnv.workload)
                # Adjust 'pg_bin_path' from the environment
                workload_conf["pg_bin_path"] = db_env_conf["pg_bin_path"]

                # 3) Prepare the report_data and load a report template
                report_data = {
                    "args": {},
                    "workload_conf": workload_conf,
                    "report_conf": {
                        "report_name": f"result_test_pg_{pg_version}"
                    }
                }
                report = get_report_structure(dataEnv.test_template_path)

                report["description"] = get_datetime_report("%d/%m/%Y %H:%M:%S")
                report["report_name"] = f"result_test_pg_{pg_version}"

                dataEnv.logger.info("Report template loaded successfully.")

                # 4) Generate init_command/workload_command pairs
                load_iterations = load_iterations_config(db_params, workload_conf)
                if not load_iterations:
                    dataEnv.logger.error("No valid load iterations configured.")
                    continue

                # Take only the first pair [init_cmd, workload_cmd] as an example
                init_cmd, workload_cmd = load_iterations[0]

                dataEnv.logger.info(f"Initial command executing:\n {init_cmd}")
                init_result = run_command(init_cmd, check=True)  # synchronous
                dataEnv.logger.info(f"Initial command result:\n {init_result.stdout}")

                dataEnv.logger.info(f"Performance command executing:\n {workload_cmd}")
                perf_result = run_command(workload_cmd, check=True)
                dataEnv.logger.info(f"Performance command result:\n {perf_result.stdout}")

                # 5) Parse pgbench output
                parsed_perf = get_pgbench_results(perf_result.stdout)
                report_data["pgbench_outputs"] = [parsed_perf]

                # 6) Connect to PostgreSQL inside the container
                db_conn = await asyncpg.connect(**db_params)
                dataEnv.logger.info("Connected to DB successfully.")

                # fill_info_report is assumed to be an async function
                await fill_info_report(dataEnv.logger, docker_conn, db_conn, report_data, report)
                dataEnv.logger.info("Monitoring info collected successfully.")

                await db_conn.close()
                dataEnv.logger.info("DB connection closed.")

                # If you want to stop or close DockerConnection here
                docker_conn.close()

                # 7) Save the report to the results path
                save_report(dataEnv.logger, report, dataEnv.result_reports_path)
                dataEnv.logger.info(f"Report saved successfully for version {pg_version}.")

            except Exception as e:
                dataEnv.logger.error(f"Exception in container for pg_version '{pg_version}': {str(e)}")
                self.fail(f"Error during test benchmark for {pg_version}: {e}")


    async def test_02_join(self):
        """
        Demonstrates merging or comparing final reports with expected data.
        """
        for pg_version in dataEnv.pg_version_list:
            # Show the tasks that will be compared
            tasks_list = "\n".join(dataEnv.join_tasks)
            dataEnv.logger.info(f"Compare items:\n{tasks_list}")

            # Sample expected and result file naming
            expected_report_name = f"expected_test_pg_{pg_version}.json"
            result_report_name = f"result_test_pg_{pg_version}.json"

            expected_path = os.path.join(dataEnv.expected_reports_path, expected_report_name)
            result_path = os.path.join(dataEnv.result_reports_path, result_report_name)

            try:
                with open(expected_path, "r", encoding="utf-8") as f:
                    expected_data = json.load(f)

                with open(result_path, "r", encoding="utf-8") as f:
                    result_data = json.load(f)

            except FileNotFoundError as e:
                # If a file isn't found, the test fails
                self.fail(f"Could not find file {e.filename}: {str(e)}")
            except json.JSONDecodeError as e:
                self.fail(f"JSON decode error in file: {str(e)}")
            except Exception as e:
                self.fail(f"Unexpected error loading JSON data: {str(e)}")

            # For demonstration, use your custom _merge_reports function
            # or a similar approach to compare or unify data
            try:
                merged_data = _merge_reports(
                    dataEnv.logger,
                    [expected_report_name, result_report_name],
                    [expected_data, result_data],
                    dataEnv.join_tasks
                )
                self.assertIsInstance(merged_data, dict, "The merged report is not a dictionary.")
                dataEnv.logger.info(f"Reports merged successfully for pg_version '{pg_version}'.")
            except Exception as merge_err:
                self.fail(f"Error merging reports for '{pg_version}': {str(merge_err)}")


if __name__ == "__main__":
    # Optionally create a test suite so that Test_01_LocalEnvironment runs before Test_02_DockerConnection
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests([
        loader.loadTestsFromTestCase(Test_01_LocalEnvironment),
        loader.loadTestsFromTestCase(Test_02_DockerConnection),
    ])

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    # Exit code indicates success (0) or failure (1)
    sys.exit(not result.wasSuccessful())
