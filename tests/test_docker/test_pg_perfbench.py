import subprocess
import unittest
import json
import logging
import os
from pathlib import Path


from pg_perfbench.__main__ import run_benchmark
from pg_perfbench.context import Context
from pg_perfbench.reports.schemas import Report
from pg_perfbench.reports.report import save_report
from pg_perfbench.exceptions import exception_helper


logging.basicConfig(level=logging.INFO)
logging.getLogger('asyncio').setLevel(logging.CRITICAL)
logging.getLogger('asyncpg').setLevel(logging.CRITICAL)
logging.getLogger('pydantic').setLevel(logging.CRITICAL)

compare_sections_fields = ['db', 'benchmark']


class TestParams:
    pg_version = '15'
    root_path = Path(os.environ.get('PYTHONPATH', ''))
    cntr_image_name = f'postgres:{pg_version}'
    cntr_name = 'cntr_test'
    cntr_forwarded_port = 5439

    cntr_cluster = '/var/lib/postgresql/data'
    cntr_pg_bin = '/usr/lib/postgresql/15/bin'

    pg_user = 'postgres'
    pg_user_password = 'pswd'
    pg_db_name = 'tdb'
    pg_host = '127.0.0.1'
    pg_port = cntr_forwarded_port

    pg_data_path = '/var/lib/postgresql/data'
    pg_bin_path = '/usr/lib/postgresql/15/bin'

    pgbench_path = 'pgbench'
    psql_path = 'psql'

    workload_path = str(root_path / 'pg_perfbench/workload/tpc-e')


test_params = TestParams()


raw_context_default_wrkld = {
    'mode': 'benchmark',
    'benchmark_type': 'default',
    'pgbench_clients': [5, 10, 15],
    'pgbench_time': [5],
    'init_command': 'ARG_PGBENCH_PATH -i --scale=10 --foreign-keys -p ARG_PG_PORT -h '
    'ARG_PG_HOST -U postgres ARG_PG_DATABASE',
    'workload_command': 'ARG_PGBENCH_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U postgres ARG_PG_DATABASE'
    ' -c ARG_PGBENCH_CLIENTS -j 4 -T ARG_PGBENCH_TIME --no-vacuum',
    'pgbench_path': test_params.pgbench_path,
    'psql_path': test_params.psql_path,
    'pg_host': '127.0.0.1',
    'pg_port': str(test_params.cntr_forwarded_port),
    'pg_user': test_params.pg_user,
    'pg_user_password': 'pswd',
    'pg_database': test_params.pg_db_name,
    'pg_data_path': test_params.pg_data_path,
    'pg_bin_path': test_params.pg_bin_path,
    'ssh_host': None,
    'ssh_port': None,
    'ssh_user': None,
    'ssh_key': None,
    'remote_pg_host': None,
    'remote_pg_port': None,
    'image_name': test_params.cntr_image_name,
    'docker_pg_host': '127.0.0.1',
    'docker_pg_port': '5432',
    'container_name': test_params.cntr_name,
}


raw_context_custom_wrkld = {
    'mode': 'benchmark',
    'benchmark_type': 'custom',
    'workload_path': '/home/nad/common/TPC_tests/pg_perfbench_github/pg_perfbench/workload/tpc-e', #test_params.workload_path,
    'pgbench_clients': [5, 10, 15],
    'pgbench_time': [5],
    'init_command': f'cd ARG_WORKLOAD_PATH && ARG_PSQL_PATH -p ARG_PG_PORT '
    '-h ARG_PG_HOST -U postgres ARG_PG_DATABASE '
    '-f ARG_WORKLOAD_PATH/tpc-e_tables.sql',
    'workload_command': 'ARG_PGBENCH_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U postgres --no-vacuum '
    '--file=ARG_WORKLOAD_PATH/Broker_Volume_SELECT.sql '
    '--file=ARG_WORKLOAD_PATH/Customer_Position_SELECT.sql ARG_PG_DATABASE '
    '-c ARG_PGBENCH_CLIENTS -j 20 -T 10',
    'pgbench_path': test_params.pgbench_path,
    'psql_path': test_params.psql_path,
    'pg_host': '127.0.0.1',
    'pg_port': str(test_params.cntr_forwarded_port),
    'pg_user': test_params.pg_user,
    'pg_user_password': 'pswd',
    'pg_database': test_params.pg_db_name,
    'pg_data_path': test_params.pg_data_path,
    'pg_bin_path': test_params.pg_bin_path,
    'ssh_host': None,
    'ssh_port': None,
    'ssh_user': None,
    'ssh_key': None,
    'remote_pg_host': None,
    'remote_pg_port': None,
    'image_name': test_params.cntr_image_name,
    'docker_pg_host': '127.0.0.1',
    'docker_pg_port': '5432',
    'container_name': test_params.cntr_name,
}

ctx_custom = Context.from_args_map(raw_context_custom_wrkld)
ctx_default = Context.from_args_map(raw_context_default_wrkld)


def compare_reports(report1, report2):
    if isinstance(report1, list) and isinstance(report2, list):
        if len(report1) != len(report2):
            print(f'List lengths differ: {len(report1)} != {len(report2)}')
            return False
        for i, (item1, item2) in enumerate(zip(report1, report2)):
            if item1 != item2:
                formatted_item1 = repr(item1)
                formatted_item2 = repr(item2)
                print(f'List items differ at index {i}: {formatted_item1} != {formatted_item2}')
                return False
        return True
    return report1 == report2


class Operations:
    @staticmethod
    def run_command(cmd, print_output=True):
        # print('='.join(['=' * 100]))
        # print(str(' '.join(cmd)))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if print_output:
            print('>>')
            if err.decode('utf-8') != '':
                print('ERROR:\n%s' % err.decode('utf-8'))
            for line in out.decode('utf-8').split('\n'):
                print('    ' + line)
        return out.decode('utf-8'), err.decode('utf-8')

    @staticmethod
    def compare_expected(expected_result, test_result) -> bool:
        exceptions_compare_fields = ['args', 'result']
        try:
            report_expected = Report(**expected_result)
            report_test = Report(**test_result)
            for section in compare_sections_fields:
                for report_key, report_value in report_expected.sections[section].reports.items():
                    if report_key in exceptions_compare_fields:
                        continue
                    report_test_value = report_test.sections[section].reports.get(report_key)
                    if not compare_reports(report_value.data, report_test_value.data):
                        print(f'----------Error: sect: {section} report: {report_key}')
                        return False
            return True
        except Exception as e:
            print(exception_helper())
            print(str(e))
            return False


class BasicUnitTest:
    async def pg_perfbench_running(self, ctx, expected_result_path) -> bool:
        test_result = await run_benchmark(ctx)
        if not isinstance(test_result, Report):
            return False

        save_report(test_result)
        with open(expected_result_path) as json_struct:
            exp_result = json.load(json_struct)
        test_result = test_result.model_dump()
        return Operations.compare_expected(exp_result, test_result)


class IntegralTest(unittest.IsolatedAsyncioTestCase, BasicUnitTest):
    @classmethod
    def setUpClass(cls):
        print('\nStart test_pg_perfbench module')
        Operations.run_command(['docker', 'stop', test_params.cntr_name], False)
        Operations.run_command(['docker', 'rm', '-f', test_params.cntr_name], False)

    async def test_01_running_benchmark_default(self):
        self.assertTrue(
            await self.pg_perfbench_running(
                ctx_default,
                str(test_params.root_path / 'tests' / 'test_docker' / 'exp_result_default.json'),
            )
        )

    async def test_02_running_benchmark_custom(self):
        self.assertTrue(
            await self.pg_perfbench_running(
                ctx_custom,
                str(test_params.root_path / 'tests' / 'test_docker' / 'exp_result_custom.json'),
            )
        )


if __name__ == '__main__':
    unittest.main(exit=False)
