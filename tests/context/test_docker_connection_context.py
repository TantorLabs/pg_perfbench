import argparse
import unittest
from unittest.mock import MagicMock

from pg_perfbench.const import (
    WorkloadTypes,
    ConnectionType,
)
from pg_perfbench.context import Context
from pg_perfbench.connections import DockerConnection


class TestDockerConnectionFunctions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dummy_args = argparse.Namespace(
            connection_type=ConnectionType.DOCKER,
            container_name='test_container',
            pg_bin_path='/usr/lib/postgresql/12/bin',
            remote_pg_host='192.168.1.100',
            remote_pg_port='5432',
            pg_host='127.0.0.1',
            pg_port='5432',
            pg_user='postgres',
            pg_password='secret',
            pg_database='test_db',
            pg_data_path='/var/lib/postgresql/12/main',
            pgbench_path='/usr/bin/pgbench',
            psql_path='/usr/bin/psql',
            benchmark_type=WorkloadTypes.DEFAULT,
            workload_path='/home/test/workload',
            init_command='init_command_example',
            workload_command='workload_command_example',
            pgbench_clients='10,20,30',
            pgbench_time=None,
            pg_custom_config='/home/test/custom.conf',
            report_name='TestReport',
            collect_pg_logs=True,
            clear_logs=False,
            log_level='INFO',
        )

        cls.mock_logger = MagicMock()

        cls.context = Context(dummy_args, cls.mock_logger)

    def test_conn_conf_matches(self):
        conn_conf = self.context.structured_params['conn_conf']

        expected_conn_params = {'container_name': 'test_container'}
        expected_env = {'ARG_PG_BIN_PATH': '/usr/lib/postgresql/12/bin'}

        self.assertEqual(
            conn_conf.get('conn_params'),
            expected_conn_params,
            'DockerConnection conn_params do not match expected values.',
        )
        self.assertEqual(
            conn_conf.get('env'),
            expected_env,
            'DockerConnection env does not match expected values.',
        )

        docker_conn = DockerConnection(
            conn_conf['conn_params'], conn_conf['env']
        )
        self.assertEqual(
            docker_conn.conn_params,
            expected_conn_params,
            'DockerConnection.conn_params do not match expected dictionary.',
        )
        self.assertEqual(
            docker_conn.env,
            expected_env,
            'DockerConnection.env do not match expected dictionary.',
        )


if __name__ == '__main__':
    unittest.main()
