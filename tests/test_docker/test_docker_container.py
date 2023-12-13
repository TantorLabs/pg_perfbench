import time
import unittest
import subprocess
import logging
import os
from pathlib import Path
import asyncio


import asyncpg
import uvloop


from pg_perfbench.connections.docker import DockerConnection
from pg_perfbench.context.schemas import connections, db
from pg_perfbench.context.schemas.workload import WorkloadDefault
from pg_perfbench.operations import db as db_operations
from pg_perfbench.pgbench_utils import get_pgbench_commands
from pg_perfbench.pgbench_utils import get_init_execution_command
from pg_perfbench.exceptions import exception_helper

logging.basicConfig(level=logging.INFO)
logging.getLogger('asyncio').setLevel(logging.CRITICAL)
logging.getLogger('pydantic').setLevel(logging.CRITICAL)


class TestParams:
    pg_version = '15'
    home_path = Path(os.environ.get('PYTHONPATH', ''))
    cntr_image_name = f'postgres:{pg_version}'
    cntr_name = 'pg_default_workload'
    cntr_forwarded_port = 5438

    cntr_cluster = '/var/lib/postgresql/data'
    cntr_pg_bin = '/usr/lib/postgresql/15/bin'
    cntr_mount_path = f'/tmp/data/{cntr_name}_data'

    pg_user = 'postgres'
    pg_user_password = 'passwd'
    pg_db_name = 'tdb'
    pg_host = '127.0.0.1'
    pg_port = cntr_forwarded_port


test_params = TestParams()


connection_params_ = {
    'image_name': test_params.cntr_image_name,
    'container_name': test_params.cntr_name,
    'tunnel': {
        'local': {'pg_host': '127.0.0.1', 'pg_port': int(test_params.cntr_forwarded_port)},
        'remote': {'docker_pg_host': '127.0.0.1', 'docker_pg_port': 5432},
    },
    'pg_data_path': test_params.cntr_cluster,
}

raw_db_params = {
    'pg_host': '127.0.0.1',
    'pg_port': f'{test_params.cntr_forwarded_port}',
    'pg_user': test_params.pg_user,
    'pg_database': test_params.pg_db_name,
    'pg_user_password': test_params.pg_user_password,
    'pg_data_path': '/etc/postgresql/15/main',
    'pg_bin_path': '/usr/lib/postgresql/15/bin'
}

raw_workload_params = {
    'benchmark_type': 'default',
    'options': {'pgbench_clients': [10, 15, 20], 'pgbench_time': [6]},
    'init_command': 'ARG_PGBENCH_PATH -i --scale=10 --foreign-keys -p ARG_PG_PORT -h ARG_PG_HOST -U'
    ' postgres ARG_PG_DATABASE',
    'workload_command': 'ARG_PGBENCH_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U postgres ARG_PG_DATABASE'
    ' -c ARG_PGBENCH_CLIENTS -j 20 -T 5 --no-vacuum',
    'pgbench_path': '/usr/bin/pgbench',
    'psql_path': '/usr/bin/psql',
}

db_params = db.DBParameters(**raw_db_params)
conn_params = connections.DockerParams(**connection_params_)
workload_params = WorkloadDefault(**raw_workload_params)


class Operations:
    @staticmethod
    def run_command(cmd, print_output=True):
        print(str(' '.join(cmd)))
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
    def wait_for_database_availability(cls):

        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        cls.loop = loop

        for attempt in range(1, cls.MAX_CONNECTION_ATTEMPTS + 1):
            connection_params = {
                'host': test_params.pg_host,
                'port': test_params.pg_port,
                'user': test_params.pg_user,
                'password': test_params.pg_user_password,
                'database': "postgres",
            }

            try:
                connection = cls.loop.run_until_complete(asyncpg.connect(**connection_params))
                print(f"Connected to the database: {test_params.pg_db_name}")
                cls.loop.run_until_complete(connection.close())
                break
            except Exception as e:
                print(f"Failed to connect to the database. Error: {e}")
                time.sleep(1)
        else:
            raise RuntimeError("Failed to connect to the database after multiple attempts")

    @classmethod
    async def check_database_connection(cls):
        connection_params = {
            'host': test_params.pg_host,
            'port': test_params.pg_port,
            'user': test_params.pg_user,
            'password': test_params.pg_user_password,
            'database': test_params.pg_db_name,
        }

        try:
            connection = await asyncpg.connect(**connection_params)
            print(f"Connected to the database: {test_params.pg_db_name}")
            await connection.close()
        except Exception as e:
            print(f"Failed to connect to the database. Error: {e}")


class BasicUnitTest:
    async def drop_cache(self) -> bool:
        try:
            cntr_conn = DockerConnection(conn_params)
            await cntr_conn.drop_cache()
            return True
        except Exception as e:
            print(exception_helper())
            print(str(e))
            return False

    async def init_db(self) -> bool:
        try:
            await db_operations.init_db(db_params)
            return True
        except Exception as e:
            print(exception_helper())
            print(str(e))
            return False

    async def load_table_schema(self) -> bool:
        try:
            init_command = get_init_execution_command(db_params, workload_params)
            Operations.run_command(init_command.split())
            return True
        except Exception as e:
            print(exception_helper())
            print(str(e))
            return False

    async def workload(self) -> bool:
        try:
            workload_command = get_pgbench_commands(db_params, workload_params)
            Operations.run_command(workload_command[0].split())
            return True
        except Exception as e:
            print(exception_helper())
            print(str(e))
            return False

    async def simple_query(self) -> bool:
        try:
            dbconn = await asyncpg.connect(
                host=test_params.pg_host,
                port=test_params.pg_port,
                user=test_params.pg_user,
                database='postgres',
                # TODO: Should use dedicated user intended for benchmark purpose
                password=test_params.pg_user_password,
            )
            data = await dbconn.fetchval('SELECT version();')
            await dbconn.close()
            print(f'\n{str(data)}')
            return True
        except Exception as e:
            print(exception_helper())
            print(str(e))
            return False


class UnitTest(unittest.IsolatedAsyncioTestCase, BasicUnitTest):
    MAX_CONNECTION_ATTEMPTS = 10
    CONNECTION_RETRY_INTERVAL = 1

    @classmethod
    def setUpClass(cls):
        print('\nStart test_docker_container module')
        print('\n----> Initializing a docker container')
        Operations.run_command(['mkdir', '-p', test_params.cntr_mount_path])
        Operations.run_command(['docker', 'pull', test_params.cntr_image_name], True)
        Operations.run_command(['docker', 'stop', test_params.cntr_name], False)
        Operations.run_command(['docker', 'rm', '-f', test_params.cntr_name], False)
        Operations.run_command(
            [
                'docker',
                'run',
                '-p',
                f'{test_params.cntr_forwarded_port}:5432',
                '--name',
                test_params.cntr_name,
                '-v',
                f'{test_params.cntr_mount_path}:{str(test_params.cntr_cluster)}:rw',
                '-e',
                'POSTGRES_HOST_AUTH_METHOD=trust',
                '-d',
                test_params.cntr_image_name,
            ],
            True,
        )
        Operations.wait_for_database_availability(cls=cls)

    async def test_01_drop_cache(self):
        print('\n----> Test drop cache of host')
        Operations.run_command(['docker', 'stop', test_params.cntr_name], True)
        Operations.run_command(['docker', 'rm', '-f', test_params.cntr_name], True)
        self.assertTrue(await self.drop_cache())
        self.assertTrue(await db_operations.wait_for_database_availability(db_params))

    async def test_02_sql_simple_queries(self):
        print('\n----> Testing asyncpg connection - ' '"SELECT VERSION();"')
        self.assertTrue(await self.simple_query())

    async def test_03_load_testing_steps(self):
        print('\n----> Testing the main stages of the benchmark')
        self.assertTrue(await self.init_db())
        self.assertTrue(await self.load_table_schema())
        self.assertTrue(await self.workload())

    @classmethod
    def tearDownClass(cls):
        cls.loop.close()
        asyncio.set_event_loop(None)
        print('\n----> Terminating a docker container')
        Operations.run_command(['docker', 'stop', test_params.cntr_name], False)
        Operations.run_command(['docker', 'rm', '-f', test_params.cntr_name], False)
        print('\n----> Tearing down resources (e.g., stopping Docker container)')


if __name__ == '__main__':
    unittest.main(exit=False)
