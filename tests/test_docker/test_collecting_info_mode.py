import subprocess
import unittest
import json
import logging
import os
from pathlib import Path

from pg_perfbench.__main__ import collect_info
from pg_perfbench.context import CollectSysInfoContext, CollectDBInfoContext
from pg_perfbench.const import WorkMode, LogLevel
from pg_perfbench.reports.schemas import SysInfoReport, DBInfoReport, AllInfoReport
from pg_perfbench.reports.report import save_report
from pg_perfbench.exceptions import exception_helper


logging.basicConfig(level=logging.INFO)
logging.getLogger('asyncio').setLevel(logging.CRITICAL)
logging.getLogger('asyncpg').setLevel(logging.CRITICAL)
logging.getLogger('pydantic').setLevel(logging.CRITICAL)




class TestParams:
    pg_version = '15.5'
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


test_params = TestParams()


raw_context_collect_sys_info = {
    'mode': 'collect-sys-info',
    'benchmark_type': 'default',
    'report_name': 'collect-sys-info-report',
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


raw_context_collect_db_info = {
    'mode': 'collect-db-info',
    'benchmark_type': 'default',
    'report_name': 'collect-db-info-report',
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

ctx_collect_sys_info = CollectSysInfoContext.from_args_map(raw_context_collect_sys_info)
ctx_collect_db_info = CollectDBInfoContext.from_args_map(raw_context_collect_db_info)
ctx_collect_all_info = CollectDBInfoContext.from_args_map(raw_context_collect_db_info)


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
    def compare_expected(expected_result, ReportClass, test_result) -> bool:
        compare_sections_fields = list(expected_result['sections'].keys())
        try:
            report_expected = ReportClass(**expected_result)
            report_test = ReportClass(**test_result)
            for section in compare_sections_fields:
                for report_key, report_value in report_expected.sections[section].reports.items():
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
    async def collect_info_checking(self, ctx, mode: WorkMode, expected_result_path) -> bool:
        mode_rprtcls = {
            WorkMode.COLLECT_SYS_INFO: SysInfoReport,
            WorkMode.COLLECT_DB_INFO: DBInfoReport,
            WorkMode.COLLECT_ALL_INFO: AllInfoReport
        }
        test_result = await collect_info(ctx, mode, LogLevel.DEBUG)
        if not isinstance(test_result, mode_rprtcls[mode]):
            return False

        save_report(test_result, mode)
        with open(expected_result_path) as json_struct:
            exp_result = json.load(json_struct)
        test_result = test_result.model_dump()
        return Operations.compare_expected(exp_result, mode_rprtcls[mode], test_result)

class IntegralTest(unittest.IsolatedAsyncioTestCase, BasicUnitTest):
    @classmethod
    def setUpClass(cls):
        print('\nStart test_pg_perfbench module')
        Operations.run_command(['docker', 'stop', test_params.cntr_name], False)
        Operations.run_command(['docker', 'rm', '-f', test_params.cntr_name], False)


    async def test_01_collect_sys_info(self):
        self.assertTrue(
            await self.collect_info_checking(
                ctx_collect_sys_info,
                WorkMode.COLLECT_SYS_INFO,
                str(test_params.root_path / 'tests' / 'test_docker' / 'exp_sys_info_report_struct.json'),
            )
        )

    async def test_02_collect_db_info(self):
        self.assertTrue(
            await self.collect_info_checking(
                ctx_collect_db_info,
                WorkMode.COLLECT_DB_INFO,
                str(test_params.root_path / 'tests' / 'test_docker' / 'exp_db_info_report_struct.json'),
            )
        )

    async def test_03_collect_all_info(self):
        ctx_collect_db_info.report.report_name = 'collect-all-info-report'
        self.assertTrue(
            await self.collect_info_checking(
                ctx_collect_db_info,
                WorkMode.COLLECT_ALL_INFO,
                str(test_params.root_path / 'tests' / 'test_docker' / 'exp_all_info_report_struct.json'),
            )
        )


if __name__ == '__main__':
    unittest.main(exit=False)
