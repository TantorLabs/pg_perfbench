import unittest
from pydantic import ValidationError

from pg_perfbench.context.schemes.connections import (
    SSHConnectionParams,
    DockerParams,
    TunnelParams,
    WorkPaths,
    ConnectionParameters,
    LocalNodeParams,
    RemoteNodeParams,
    DockerRemoteNodeParams,
)


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
            'tunnel': {
                'local': {'pg_host': '127.0.0.1', 'pg_port': 5423},
                'remote': {
                    'remote_pg_host': '127.0.0.1',
                    'remote_pg_port': 5432,
                },
            },
            'work_paths': {
                'pg_data_path': '/path/to/pg_data',
                'pg_bin_path': '/path/to/pg_bin',
                'custom_config': '',
            },
        }

    def test_ssh_connection_params_construction(self):
        params = SSHConnectionParams(**self.ssh_connection_params)
        self.assertEqual(params.host, '127.0.0.1')
        self.assertEqual(params.port, 2222)
        self.assertEqual(params.user, 'remote_user')
        self.assertEqual(params.key, '/path/to/private_key.pem')
        self.assertIsInstance(params.tunnel, TunnelParams)
        self.assertIsInstance(params.work_paths, WorkPaths)
        self.assertEqual(params.tunnel.local.host, '127.0.0.1')
        self.assertEqual(params.tunnel.local.port, 5423)
        self.assertEqual(params.tunnel.remote.host, '127.0.0.1')
        self.assertEqual(params.tunnel.remote.port, 5432)
        self.assertEqual(params.work_paths.pg_data_path, '/path/to/pg_data')
        self.assertEqual(params.work_paths.pg_bin_path, '/path/to/pg_bin')


class TestDockerConnectionParams(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print('\nTesting the Docker connection context scheme')

    def setUp(self):
        self.docker_connection_params = {
            'image_name': 'postgres:latest',
            'container_name': 'pg_perfbench',
            'tunnel': {
                'local': {'pg_host': '127.0.0.1', 'pg_port': 5423},
                'remote': {
                    'docker_pg_host': '127.0.0.1',
                    'docker_pg_port': 5432,
                },
            },
            'work_paths': {
                'pg_data_path': '/var/lib/postgresql/data',
                'pg_bin_path': '/usr/local/bin',
                'custom_config': '',
            },
        }

    def test_docker_params_construction_with_default_params(self):
        params = DockerParams(**self.docker_connection_params)
        self.assertEqual(params.image_name, 'postgres:latest')
        self.assertEqual(params.container_name, 'pg_perfbench')
        self.assertIsInstance(params.tunnel, TunnelParams)
        self.assertIsInstance(params.work_paths, WorkPaths)
        self.assertEqual(params.tunnel.local.host, '127.0.0.1')
        self.assertEqual(params.tunnel.local.port, 5423)
        self.assertEqual(params.tunnel.remote.host, '127.0.0.1')
        self.assertEqual(params.tunnel.remote.port, 5432)
        self.assertEqual(
            params.work_paths.pg_data_path, '/var/lib/postgresql/data'
        )
        self.assertEqual(params.work_paths.pg_bin_path, '/usr/local/bin')


class TestConnectionTypes(unittest.TestCase):
    def test_connection_type_identification(self):
        ssh_params = SSHConnectionParams(
            ssh_host='127.0.0.1',
            ssh_port=22,
            ssh_user='postgres',
            ssh_key='/path/to/private_key.pem',
            tunnel=TunnelParams(
                local=LocalNodeParams(pg_host='127.0.0.1', pg_port=5435),
                remote=RemoteNodeParams(
                    remote_pg_host='127.0.0.1', remote_pg_port=5432
                ),
            ),
            work_paths=WorkPaths(
                pg_data_path='/var/lib/postgresql/data',
                pg_bin_path='/usr/local/bin',
                custom_config='/var/lib/postgresql/data/postgresql.conf',
            ),
        )

        docker_params = DockerParams(
            image_name='postgres:latest',
            container_name='pg_perfbench',
            tunnel=TunnelParams(
                local=LocalNodeParams(pg_host='127.0.0.1', pg_port=5435),
                remote=DockerRemoteNodeParams(
                    docker_pg_host='127.0.0.1', docker_pg_port=5432
                ),
            ),
            work_paths=WorkPaths(
                pg_data_path='/var/lib/postgresql/data',
                pg_bin_path='/usr/local/bin',
                custom_config='/var/lib/postgresql/data/postgresql.conf',
            ),
        )

        self.assertTrue(
            isinstance(ssh_params, ConnectionParameters),
            'ssh_params should be an instance of ConnectionParameters',
        )
        self.assertTrue(
            isinstance(docker_params, ConnectionParameters),
            'docker_params should be an instance of ConnectionParameters',
        )

        wrong_params = {'some': 'data'}
        with self.assertRaises(ValidationError):
            _ = SSHConnectionParams(**wrong_params)


if __name__ == '__main__':
    unittest.main()
