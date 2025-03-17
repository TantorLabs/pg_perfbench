import argparse
import inspect
import unittest
from unittest.mock import MagicMock, patch

import asyncssh
from sshtunnel import SSHTunnelForwarder

from pg_perfbench.const import (
    LogLevel,
    WorkloadTypes,
    WorkMode,
    ConnectionType
)
from pg_perfbench.context import Context, CollectInfoContext, JoinContext
from pg_perfbench.connections import SSHConnection


class TestSSHConnectionFunctions(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        dummy_args = argparse.Namespace(
            connection_type=ConnectionType.SSH,
            ssh_host="127.0.0.1",
            ssh_port="22",
            ssh_key="/home/test/.ssh/id_rsa",
            pg_bin_path="/usr/lib/postgresql/12/bin",
            remote_pg_host="192.168.1.100",
            remote_pg_port="5432",
            pg_host="127.0.0.1",
            pg_port="5432",
            pg_user="postgres",
            pg_password="secret",
            pg_database="test_db",
            pg_data_path="/var/lib/postgresql/12/main",
            pgbench_path="/usr/bin/pgbench",
            psql_path="/usr/bin/psql",
            benchmark_type=WorkloadTypes.DEFAULT,
            workload_path="/home/test/workload",
            init_command="init_command_example",
            workload_command="workload_command_example",
            pgbench_clients="10,20,30",  # will be processed via parse_pgbench_options
            pgbench_time=None,
            pg_custom_config="/home/test/custom.conf",
            report_name="TestReport",
            collect_pg_logs=True,
            clear_logs=False,
            log_level="INFO"
        )

        mock_logger = MagicMock()

        # Instantiate Context with test arguments and the mock logger
        context = Context(dummy_args, mock_logger)

        cls.ssh_conn = SSHConnection(**context.structured_params['conn_conf'])

    async def test_01_conn_params_structure(self):
        sig = inspect.signature(asyncssh.connect)
        params = sig.parameters

        has_var_kw = any(
            param.kind == param.VAR_KEYWORD for param in params.values()
        )
        self.assertTrue(
            has_var_kw,
            "asyncssh.connect should accept additional keyword arguments (**kwargs)"
        )

        if not has_var_kw:
            for key in self.ssh_conn.conn_params:
                self.assertIn(key, params, f"asyncssh.connect missing expected parameter '{key}'")

    async def test_02_tunnel_params_structure(self):
        sig = inspect.signature(SSHTunnelForwarder)
        params = sig.parameters

        for key in self.ssh_conn.tunnel_params:
            self.assertIn(
                key,
                params,
                f"SSHTunnelForwarder signature is missing parameter '{key}'"
            )

    async def test_03_start_invalid_params(self):
        with patch("asyncssh.connect", side_effect=Exception("Test error")):
            with self.assertRaises(ConnectionError) as cm:
                await self.ssh_conn.start()
            self.assertIn("SSH connection failed", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
