import argparse
import unittest
from unittest.mock import MagicMock

from pg_perfbench.const import ConnectionType, WorkMode, WorkloadTypes
from pg_perfbench.context import Context, CollectInfoContext, JoinContext


class TestContext(unittest.TestCase):
    def setUp(self):
        self.logger = MagicMock()

    def test_context_ssh_ok(self):
        class Args:
            def __init__(self):
                self.connection_type = ConnectionType.SSH
                self.ssh_host = "192.168.0.10"
                self.ssh_port = "22"
                self.ssh_key = "my_ssh_key"
                self.remote_pg_host = "127.0.0.1"
                self.remote_pg_port = "5432"

                self.pg_host = "localhost"
                self.pg_port = "5439"
                self.pg_user = "postgres"
                self.pg_password = "pswd"
                self.pg_database = "testdb"
                self.pg_data_path = "/var/lib/postgresql/data"
                self.pg_bin_path = "/usr/lib/postgresql/bin"

                self.init_command = "init_cmd"
                self.workload_command = "work_cmd"
                self.pgbench_path = "pgbench"
                self.psql_path = "psql"
                self.benchmark_type = WorkloadTypes.DEFAULT
                self.workload_path = None
                self.pgbench_clients = [5, 10]
                self.pgbench_time = None
                self.pg_custom_config = None

                self.collect_pg_logs = False
                self.clear_logs = False
                self.log_level = "info"
                self.report_name = "test_report"

        args = Args()
        context_obj = Context(args, self.logger)
        self.assertIn("conn_conf", context_obj.structured_params)
        self.assertIn("db_conf", context_obj.structured_params)
        self.assertIn("workload_conf", context_obj.structured_params)
        self.assertEqual(context_obj.structured_params["conn_type"], ConnectionType.SSH)
        self.assertEqual(context_obj.structured_params["workload_conf"]["pgbench_iter_list"], [5, 10])

    def test_context_docker_ok(self):
        class Args:
            def __init__(self):
                self.connection_type = ConnectionType.DOCKER
                self.container_name = "my_container"

                self.ssh_host = None
                self.ssh_port = None
                self.ssh_key = None
                self.remote_pg_host = None
                self.remote_pg_port = None

                self.pg_host = "localhost"
                self.pg_port = "5433"
                self.pg_user = "postgres"
                self.pg_password = "pwd"
                self.pg_database = "db"
                self.pg_data_path = "/data"
                self.pg_bin_path = "/bin"

                self.init_command = "init_cmd"
                self.workload_command = "work_cmd"
                self.pgbench_path = "pgbench"
                self.psql_path = "psql"
                self.benchmark_type = WorkloadTypes.DEFAULT
                self.workload_path = None
                self.pgbench_clients = None
                self.pgbench_time = [60]
                self.pg_custom_config = None

                self.collect_pg_logs = True
                self.clear_logs = False
                self.log_level = "debug"
                self.report_name = "docker_report"

        args = Args()
        context_obj = Context(args, self.logger)
        self.assertEqual(context_obj.structured_params["conn_type"], ConnectionType.DOCKER)
        self.assertEqual(
            context_obj.structured_params["conn_conf"]["conn_params"]["container_name"],
            "my_container"
        )
        self.assertEqual(
            context_obj.structured_params["workload_conf"]["pgbench_iter_name"],
            "pgbench_time"
        )
        self.assertEqual(
            context_obj.structured_params["workload_conf"]["pgbench_iter_list"],
            [60]
        )

    def test_context_local_ok(self):
        class Args:
            def __init__(self):
                self.connection_type = ConnectionType.LOCAL
                self.ssh_host = None
                self.ssh_port = None
                self.ssh_key = None
                self.remote_pg_host = None
                self.remote_pg_port = None

                self.pg_host = "localhost"
                self.pg_port = "5434"
                self.pg_user = "postgres"
                self.pg_password = ""
                self.pg_database = "local_db"
                self.pg_data_path = "/local/data"
                self.pg_bin_path = "/local/bin"

                self.init_command = "init_local"
                self.workload_command = "work_local"
                self.pgbench_path = "local_pgbench"
                self.psql_path = "local_psql"
                self.benchmark_type = WorkloadTypes.CUSTOM
                self.workload_path = "/some/path"
                self.pgbench_clients = None
                self.pgbench_time = None
                self.pg_custom_config = None

                self.collect_pg_logs = False
                self.clear_logs = True
                self.log_level = "error"
                self.report_name = "local_report"

        args = Args()
        context_obj = Context(args, self.logger)
        self.assertEqual(context_obj.structured_params["conn_type"], ConnectionType.LOCAL)
        self.assertEqual(context_obj.structured_params["workload_conf"]["workload_path"], "/some/path")

    def test_context_parameters_missing_raises(self):
        class Args:
            def __init__(self):
                self.connection_type = ConnectionType.SSH
                self.ssh_host = "192.168.0.10"
                self.ssh_port = "22"
                self.ssh_key = "some_key"
                self.remote_pg_host = "127.0.0.1"
                self.remote_pg_port = "5432"

                self.pg_host = "localhost"
                self.pg_port = None  # Missing parameter
                self.pg_user = "postgres"
                self.pg_password = "pwd"
                self.pg_database = "db"
                self.pg_data_path = "/data"
                self.pg_bin_path = "/bin"

                self.init_command = "init"
                self.workload_command = "work"
                self.pgbench_path = "pgbench"
                self.psql_path = "psql"
                self.benchmark_type = WorkloadTypes.DEFAULT
                self.workload_path = None
                self.pgbench_clients = [5]
                self.pgbench_time = None
                self.pg_custom_config = None

                self.collect_pg_logs = False
                self.clear_logs = False
                self.log_level = "info"
                self.report_name = "missing_params"

        args = Args()
        with self.assertRaises(ValueError) as cm:
            _ = Context(args, self.logger)
        self.assertIn("Parameter \"--pg-port\" must be specified", str(cm.exception))


class TestCollectInfoContext(unittest.TestCase):
    def setUp(self):
        self.logger = MagicMock()

    def test_collect_info_ssh_ok(self):
        class Args:
            def __init__(self):
                self.mode = WorkMode.COLLECT_DB_INFO
                self.connection_type = ConnectionType.SSH
                self.ssh_host = "10.0.0.10"
                self.ssh_port = "22"
                self.ssh_key = "/path/to/key"
                self.remote_pg_host = "127.0.0.1"
                self.remote_pg_port = "5432"

                self.pg_host = "localhost"
                self.pg_port = "5439"
                self.pg_user = "postgres"
                self.pg_password = "pswd"
                self.pg_database = "db"
                self.pg_data_path = "/data"
                self.pg_bin_path = "/bin"

                self.pg_custom_config = None
                self.collect_pg_logs = True
                self.clear_logs = False
                self.log_level = "info"
                self.report_name = "report_ci"

        args = Args()
        ci_context = CollectInfoContext(args, self.logger)
        self.assertIn("conn_conf", ci_context.structured_params)
        self.assertIn("tunnel_params", ci_context.structured_params["conn_conf"])
        self.assertIn("report_name", ci_context.structured_params["report_conf"])

    def test_collect_info_missing_param(self):
        class Args:
            def __init__(self):
                self.mode = WorkMode.COLLECT_DB_INFO
                self.connection_type = ConnectionType.SSH
                # Missing SSH parameters and DB parameters.
                self.ssh_host = None
                self.ssh_port = None
                self.ssh_key = None
                self.remote_pg_host = None
                self.remote_pg_port = None

                self.pg_host = None
                self.pg_port = None
                self.pg_user = None
                self.pg_password = None
                self.pg_database = None
                self.pg_data_path = None
                self.pg_bin_path = None

                self.pg_custom_config = None
                self.collect_pg_logs = False
                self.clear_logs = False
                self.log_level = "info"
                self.report_name = "ci_report"

        with self.assertRaises(ValueError):
            _ = CollectInfoContext(Args(), self.logger)


class TestJoinContext(unittest.TestCase):
    def test_join_context_ok(self):
        class Args:
            def __init__(self):
                self.join_tasks = "/path/to/join_tasks.json"
                self.reference_report = "ref_report.json"
                self.input_dir = "./reports"
                self.report_name = "join_report"

        logger = MagicMock()
        ctx = JoinContext(Args(), logger)
        self.assertIn("join_tasks", ctx.structured_params)
        self.assertEqual(ctx.structured_params["report_name"], "join_report")

    def test_join_context_defaults(self):
        class Args:
            def __init__(self):
                self.join_tasks = None
                self.reference_report = None
                self.input_dir = None
                self.report_name = None

        logger = MagicMock()
        ctx = JoinContext(Args(), logger)
        self.assertIsNone(ctx.structured_params["join_tasks"])
        self.assertIsNone(ctx.structured_params["report_name"])


if __name__ == "__main__":
    unittest.main()
