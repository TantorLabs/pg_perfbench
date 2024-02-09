import unittest
from pg_perfbench.context.schemes.connections import RemoteNodeParams, SSHConnectionParams


class TestSSHConnectionParams(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print('\nTesting the SSH connection context scheme')

    def setUp(self):
        self.ssh_connection_params = {
            'ssh_host': '127.0.0.1',
            'ssh_port': 2222,
            'ssh_user': 'remote_user',
            'ssh_key': '/path/to/private_key.pem',
            'work_paths': {
                'pg_data_path': '/path/to/pg_data', 
                'pg_bin_path': '/path/to/pg_bin'
            },
            'tunnel': {
                'local': {'pg_host': '127.0.0.1', 'pg_port': 5423},
                'remote': {'remote_pg_host': '127.0.0.1', 'remote_pg_port': 5432},
                'custom_config': ''
            },
        }

    def test_ssh_tunnel_remote_node_with_default_params(self):
        params = RemoteNodeParams.model_validate(self.ssh_connection_params)
        self.assertNotEqual(params.host, '')
        self.assertIsInstance(params.port, int)

    def test_ssh_connection_construction_with_default_params(self):
        params = SSHConnectionParams(**self.ssh_connection_params)
        self.assertTrue(hasattr(params, 'tunnel'))
        self.assertTrue(hasattr(params.tunnel, 'local'))
        self.assertTrue(hasattr(params.tunnel, 'remote'))


class TestDockerConnectionParams(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print('\nTesting the SSH connection context scheme')

    def setUp(self):
        self.ssh_connection_params = {
            'ssh_host': '127.0.0.1',
            'ssh_port': 2222,
            'ssh_user': 'remote_user',
            'ssh_key': '/path/to/private_key.pem',
            'work_paths': {
                'pg_data_path': '/path/to/pg_data',
                'pg_bin_path': '/path/to/pg_bin'
            },
            'tunnel': {
                'local': {'pg_host': '127.0.0.1', 'pg_port': 5423},
                'remote': {'remote_pg_host': '127.0.0.1', 'remote_pg_port': 5432},
                'custom_config': ''
            },
        }

    def test_ssh_tunnel_remote_node_with_default_params(self):
        params = RemoteNodeParams.model_validate(self.ssh_connection_params)
        self.assertNotEqual(params.host, '')
        self.assertIsInstance(params.port, int)

    def test_ssh_connection_construction_with_default_params(self):
        params = SSHConnectionParams(**self.ssh_connection_params)
        self.assertTrue(hasattr(params, 'tunnel'))
        self.assertTrue(hasattr(params.tunnel, 'local'))
        self.assertTrue(hasattr(params.tunnel, 'remote'))

if __name__ == '__main__':
    unittest.main()
