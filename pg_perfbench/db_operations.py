from const import ConnectionType
import asyncpg
import time

class DBTasks:
    def __init__(self, db_conf, logger):
        self.db_conf = db_conf
        self.logger = logger

    async def init_db(self):
        create_test_db_sql = f"""
            CREATE DATABASE {self.db_conf['database']}
                   WITH
                   OWNER = {self.db_conf['user']}
                   ENCODING = 'UTF8'
                   LC_COLLATE = 'en_US.UTF-8'
                   LC_CTYPE = 'en_US.UTF-8'
                   template = template0
        """

        db = await asyncpg.connect(
            host=self.db_conf['host'],
            port=self.db_conf['port'],
            user=self.db_conf['user'],
            database='postgres',
            password=self.db_conf['password'],
        )
        self.logger.info('Creating pristine test DB')
        await db.execute(create_test_db_sql)
        await db.close()

    async def drop_db(self):
        terminate_db_pid_sql = f"""
            SELECT pg_terminate_backend(pid)
              FROM pg_stat_activity
             WHERE pid <> pg_backend_pid()
                   AND datname = '{self.db_conf['database']}'
        """
        drop_database_db_sql = f"""
                DROP DATABASE IF EXISTS {self.db_conf['database']}
        """
        db = await asyncpg.connect(
            host=self.db_conf['host'],
            port=self.db_conf['port'],
            user=self.db_conf['user'],
            database='postgres',
            password=self.db_conf['password'],
        )
        self.logger.info('Terminating other sessions to the test DB')
        await db.execute(terminate_db_pid_sql)
        self.logger.info('Dropping test DB')
        await db.execute(drop_database_db_sql)
        await db.close()


    async def check_db_access(self):
        for attempt in range(1, 11):  # Adjust the number of attempts as needed
            try:
                db_connection = await asyncpg.connect(
                    host=self.db_conf['host'],
                    port=self.db_conf['port'],
                    user=self.db_conf['user'],
                    database=self.db_conf['database'],
                    password=self.db_conf['password'],
                )
                await db_connection.fetchval('SELECT 1')
                await db_connection.close()
                self.logger.info('Database is available.')
                return True
            except (asyncpg.PostgresError, ConnectionError) as e:
                self.logger.warning(
                    f'Database not yet available. Attempt {attempt}/10. Error: {e}'
                )
                time.sleep(1)
        else:
            print('Failed to connect to the database after multiple attempts.')
            raise Exception('Database not available.')


class SSHTasks:
    def __init__(self, db_conf, conn):
        self.pg_bin_path = db_conf['pg_bin_path']
        self.pg_data_path = db_conf['pg_data_path']
        self.conn = conn

    async def stop_db(self):
        res = await self.conn.run_command(f"{self.pg_bin_path}/pg_ctl stop -D {self.pg_data_path}")
        return res

    async def start_db(self):
        res = await self.conn.run_command(f"{self.pg_bin_path}/pg_ctl start -D {self.pg_data_path}")
        return res

    async def sync(self):
        res = await self.conn.run_command("sync")
        return res

    async def drop_caches(self):
        res = await self.conn.run_command("sudo /bin/sh -c 'echo 3 | /usr/bin/tee /proc/sys/vm/drop_caches'")
        return res

class DockerTasks:
    def __init__(self, db_conf, conn):
        self.conn = conn
        self.pg_bin_path = db_conf['pg_bin_path']
        self.pg_data_path = db_conf['pg_data_path']

    async def stop_db(self):
        # res = await self.conn.run_command(f"su - postgres -c '{self.pg_bin_path}/pg_ctl stop -D {self.pg_data_path}'")
        res = await self.conn.run_command(f"{self.pg_bin_path}/pg_ctl stop -D {self.pg_data_path}")
        self.conn.close()
        return res

    async def start_db(self):
        await self.conn.start()
        # res = await self.conn.run_command(f"su - postgres -c '{self.pg_bin_path}/pg_ctl start -D {self.pg_data_path}'")
        res = await self.conn.run_command(f"{self.pg_bin_path}/pg_ctl start -D {self.pg_data_path}")
        return res

    async def sync(self):
        ...

    async def drop_caches(self):
        ...



TASK_FACTORIES = {
    ConnectionType.SSH: lambda **kwargs: SSHTasks(
        db_conf=kwargs["db_conf"],
        conn=kwargs["conn"]
    ),
     ConnectionType.DOCKER: lambda **kwargs: DockerTasks(
        conn=kwargs["conn"],
        db_conf=kwargs["db_conf"],
    ),
}