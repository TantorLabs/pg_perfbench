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


test_params = TestParams()


connection_params = {
    'image_name': test_params.cntr_image_name,
    'container_name': test_params.cntr_name,
    'tunnel': {
        'local': {'pg_host': '127.0.0.1', 'pg_port': int(test_params.cntr_forwarded_port)},
        'remote': {'docker_pg_host': '127.0.0.1', 'docker_pg_port': 5432},
    },
    'pg_data_path': test_params.cntr_cluster,
}

raw_db_params = {
    'pg_host': test_params.pg_host,
    'pg_port': f'{test_params.cntr_forwarded_port}',
    'pg_user': test_params.pg_user,
    'pg_database': test_params.pg_db_name,
    'pg_user_password': test_params.pg_user_password,
    'pg_data_path': test_params.cntr_cluster,
    'pg_bin_path': test_params.cntr_pg_bin
}


raw_default_workload_params = {
    'benchmark_type': 'default',
    'options': {'pgbench_clients': [5, 10, 15], 'pgbench_time': [5]},
    'init_command': 'ARG_PGBENCH_PATH -i --scale=10 --foreign-keys -p ARG_PG_PORT -h '
    'ARG_PG_HOST -U postgres ARG_PG_DATABASE',
    'workload_command': 'ARG_PGBENCH_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U postgres ARG_PG_DATABASE'
    ' -c ARG_PGBENCH_CLIENTS -j 4 -T ARG_PGBENCH_TIME --no-vacuum',
    'pgbench_path': '/usr/bin/pgbench',
    'psql_path': '/usr/bin/psql',
}


raw_custom_workload_params = {
    'benchmark_type': 'custom',
    'options': {'pgbench_clients': [5, 10, 15], 'pgbench_time': [5]},
    'workload_path': str(test_params.root_path / 'pg_perfbench' / 'workload' / 'tpc-e'),
    'init_command': 'cd ARG_WORKLOAD_PATH && ARG_PSQL_PATH -p ARG_PG_PORT '
    '-h ARG_PG_HOST -U postgres ARG_PG_DATABASE '
    '-f ARG_WORKLOAD_PATH/tpc-e_tables.sql',
    'workload_command': 'ARG_PGBENCH_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U postgres --no-vacuum '
    '--file=ARG_WORKLOAD_PATH/Broker_Volume_SELECT.sql '
    '--file=ARG_WORKLOAD_PATH/Customer_Position_SELECT.sql ARG_PG_DATABASE '
    '-c ARG_PGBENCH_CLIENTS -j 20 -T 10',
    'pgbench_path': '/usr/bin/pgbench',
    'psql_path': '/usr/bin/psql',
}


raw_context_default_wrkld = {}
raw_context_default_wrkld.update({'raw_args': {}})
raw_context_default_wrkld.update({'service': {'clear_logs': False}})
raw_context_default_wrkld.update({'connection': connection_params})
raw_context_default_wrkld.update({'db': raw_db_params})
raw_context_default_wrkld.update({'workload': raw_default_workload_params})

raw_context_custom_wrkld = {}
raw_context_custom_wrkld.update({'raw_args': {}})
raw_context_custom_wrkld.update({'service': {'clear_logs': False}})
raw_context_custom_wrkld.update({'connection': connection_params})
raw_context_custom_wrkld.update({'db': raw_db_params})
raw_context_custom_wrkld.update({'workload': raw_custom_workload_params})

ctx_default = Context(**raw_context_default_wrkld)
ctx_custom = Context(**raw_context_custom_wrkld)


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
        exceptions_compare_fields = ['args']
        try:
            report_expected = Report(**expected_result)
            report_test = Report(**test_result)
            for section in compare_sections_fields:
                for report in report_expected.sections[section].reports:
                    if report in exceptions_compare_fields:
                        continue
                    if (
                        report_expected.sections[section].reports[report]
                        != report_test.sections[section].reports[report]
                    ):
                        print(f'----------Error: sect: {section} report: {report}')
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
