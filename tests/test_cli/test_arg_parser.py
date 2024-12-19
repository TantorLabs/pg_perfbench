import unittest
from argparse import Namespace
from typing import Any

from pg_perfbench.cli.args_parser import get_args_parser
from pg_perfbench.const import WorkMode, LogLevel


class TestArgParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print('\ntest_arg_parser module')

    def assertArgEqual(self, result: Namespace, expected: dict[str, Any]) -> None:
        for key, value in expected.items():
            self.assertEqual(getattr(result, key), value)

    def test_arg_parser_with_empty_input(self) -> None:
        result = get_args_parser().parse_args(['--mode', str(WorkMode.BENCHMARK)])
        expected = {
            'clear_logs': False,
            'log_level': str(LogLevel.INFO),
            'report_name': None,
            'mode': str(WorkMode.BENCHMARK),
            'benchmark_type': None,
            'workload_path': None,
            'pgbench_clients': None,
            'pgbench_time': None,
            'init_command': None,
            'workload_command': None,
            'pg_host': None,
            'pg_port': None,
            'pg_user': None,
            'pg_user_password': None,
            'pg_database': None,
            'pg_data_path': None,
            'pg_bin_path': None,
            'pgbench_path': None,
            'psql_path': None,
            'ssh_host': None,
            'ssh_port': None,
            'ssh_user': None,
            'ssh_key': None,
            'remote_pg_host': None,
            'remote_pg_port': None,
            'image_name': None,
            'docker_pg_host': None,
            'docker_pg_port': None,
            'container_name': None,
        }

        self.assertArgEqual(result, expected)

    def test_arg_parser_values_handling(self) -> None:
        test_cases = [
            (['--log-level', 'info'], {'log_level': 'info'}),
            (['--clear-logs'], {'clear_logs': True}),
            # Add more test cases for other arguments...
        ]

        for args, expected in test_cases:
            with self.subTest(args=args, expected=expected):
                result = get_args_parser().parse_args(args)
                self.assertArgEqual(result, expected)

    def test_arg_parser_handling_pack_of_arguments(self) -> None:
        args = [
            '--mode',
            str(WorkMode.BENCHMARK),
            '--log-level',
            'info',
            '--report-name',
            'report-name',
            '--clear-logs',
            '--ssh-host',
            'test_user@test_host',
            '--ssh-user',
            'test_ssh_user',
            '--ssh-key',
            'test_ssh_key',
            '--ssh-port',
            '22',
            '--remote-pg-host',
            '127.0.0.1',
            '--remote-pg-port',
            '7890',
            '--pg-host',
            '127.0.0.1',
            '--pg-port',
            '2345',
            '--pg-user',
            'test_user',
            '--pg-user-password',
            'test_password',
            '--pg-database',
            'test_db',
            '--pg-data-path',
            '/tmp/path/to/cluster',
            '--pg-bin-path',
            '/tmp/path/to/utilities',
            '--pgbench-path',
            '/usr/bin/pgbench',
            '--psql-path',
            '/usr/bin/psql',
            '--benchmark-type',
            'custom',
            '--workload-path',
            '/tmp/path/workload.sql',
            '--init-command',
            'cd ARG_WORKLOAD_PATH && ARG_PSQL_PATH -p ARG_PG_PORT -h ARG_PG_HOST '
            ' -U postgres ARG_PG_DATABASE -f ARG_WORKLOAD_PATH/tpc-e_tables.sql',
            '--workload-command',
            'ARG_PGBENCH_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U postgres '
            '--no-vacuum --file=ARG_WORKLOAD_PATH/Broker_Volume_SELECT.sql '
            '--file=ARG_WORKLOAD_PATH/Customer_Position_SELECT.sql '
            'ARG_PG_DATABASE -c ARG_PGBENCH_CLIENTS -j 20 -T 10',
            '--pgbench-clients',
            '1, 12, 25',
            '--pgbench-time',
            '15',
        ]

        result = get_args_parser().parse_args(args)

        expected = {
            'mode': str(WorkMode.BENCHMARK),
            'log_level': 'info',
            'report_name': 'report-name',
            'clear_logs': True,
            'ssh_host': 'test_user@test_host',
            'ssh_user': 'test_ssh_user',
            'ssh_key': 'test_ssh_key',
            'ssh_port': '22',
            'remote_pg_host': '127.0.0.1',
            'remote_pg_port': '7890',
            'pg_host': '127.0.0.1',
            'pg_port': '2345',
            'pg_user': 'test_user',
            'pg_user_password': 'test_password',
            'pg_database': 'test_db',
            'pg_data_path': '/tmp/path/to/cluster',
            'pg_bin_path': '/tmp/path/to/utilities',
            'pgbench_path': '/usr/bin/pgbench',
            'psql_path': '/usr/bin/psql',
            'benchmark_type': 'custom',
            'workload_path': '/tmp/path/workload.sql',
            'init_command': 'cd ARG_WORKLOAD_PATH && ARG_PSQL_PATH -p ARG_PG_PORT -h ARG_PG_HOST '
            ' -U postgres ARG_PG_DATABASE -f ARG_WORKLOAD_PATH/tpc-e_tables.sql',
            'workload_command': 'ARG_PGBENCH_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U postgres '
            '--no-vacuum --file=ARG_WORKLOAD_PATH/Broker_Volume_SELECT.sql '
            '--file=ARG_WORKLOAD_PATH/Customer_Position_SELECT.sql '
            'ARG_PG_DATABASE -c ARG_PGBENCH_CLIENTS -j 20 -T 10',
            'pgbench_clients': [1, 12, 25],
            'pgbench_time': [15],
        }

        self.assertArgEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
