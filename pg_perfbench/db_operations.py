from pg_perfbench.const import ConnectionType
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

        try:
            db = await asyncpg.connect(
                host=self.db_conf["host"],
                port=self.db_conf["port"],
                user=self.db_conf["user"],
                database="postgres",
                password=self.db_conf["password"],
            )
        except Exception as e:
            raise ConnectionError(
                f"Error connecting to the 'postgres' database for creating the load testing database:\n{e}")

        self.logger.debug("Creating pristine test DB.")
        try:
            await db.execute(create_test_db_sql)
        except Exception as e:
            raise RuntimeError(f"Error executing the query to create the database:\n{e}")
        finally:
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
        try:
            db = await asyncpg.connect(
                host=self.db_conf["host"],
                port=self.db_conf["port"],
                user=self.db_conf["user"],
                database="postgres",
                password=self.db_conf["password"],
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to the database for dropping test DB: {e}")

        self.logger.debug(f"Terminating other sessions to the test DB: \"{self.db_conf['database']}\".")
        try:
            await db.execute(terminate_db_pid_sql)
        except Exception as e:
            raise RuntimeError(f"Failed to terminate sessions for test DB \"{self.db_conf['database']}\": {e}")

        self.logger.debug(f"Dropping test DB: \"{self.db_conf['database']}\".")
        try:
            await db.execute(drop_database_db_sql)
        except Exception as e:
            raise RuntimeError(f"Failed to drop test DB \"{self.db_conf['database']}\": {e}")
        finally:
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
                self.logger.debug(f"Database \'{self.db_conf['database']}\' is available.")
                return True
            except (asyncpg.PostgresError, ConnectionError) as e:
                self.logger.warning(
                    f"Database not yet available. Attempt {attempt}/10. Error: {e}."
                )
                time.sleep(1)
        else:
            raise ConnectionError("Failed to connect to the database after multiple attempts.")


class SSHTasks:
    def __init__(self, db_conf, conn, logger):
        self.pg_bin_path = db_conf['pg_bin_path']
        self.pg_data_path = db_conf['pg_data_path']
        self.conn = conn
        self.logger = logger

    async def stop_db(self):
        try:
            res = await self.conn.run_command(f"{self.pg_bin_path}/pg_ctl stop -D {self.pg_data_path}", check=True)
            return res
        except Exception as e:
            raise RuntimeError(f"Database '{self.pg_data_path}' shutdown error:\n{str(e)}")

    async def start_db(self):
        res = await self.conn.run_command(f"{self.pg_bin_path}/pg_ctl start -D {self.pg_data_path}")
        return res

    async def sync(self):
        res = await self.conn.run_command("sync", check=False)
        return res

    async def drop_caches(self):
        res = await self.conn.run_command("sudo /bin/sh -c 'echo 3 | /usr/bin/tee /proc/sys/vm/drop_caches'",
                                          check=False)
        return res


class DockerTasks:
    def __init__(self, db_conf, conn, logger):
        self.conn = conn
        self.pg_bin_path = db_conf['pg_bin_path']
        self.pg_data_path = db_conf['pg_data_path']
        self.logger = logger

    async def stop_db(self):
        try:
            res = await self.conn.run_command(f"{self.pg_bin_path}/pg_ctl stop -D {self.pg_data_path}")
            self.conn.close()
            return res
        except Exception as e:
            raise RuntimeError(f"Database '{self.pg_data_path}' shutdown error:\n{str(e)}")

    async def start_db(self):
        await self.conn.start()
        res = await self.conn.run_command(f"{self.pg_bin_path}/pg_ctl start -D {self.pg_data_path}")
        return res

    async def sync(self):
        ...

    async def drop_caches(self):
        ...


class LocalConnTasks:
    def __init__(self, db_conf, conn, logger):
        self.conn = conn
        self.pg_bin_path = db_conf['pg_bin_path']
        self.pg_data_path = db_conf['pg_data_path']
        self.logger = logger

    async def stop_db(self):
        try:
            res = await self.conn.run_command(
                f"su - postgres -c '{self.pg_bin_path}/pg_ctl stop -D {self.pg_data_path}'")
            return res
        except Exception as e:
            raise RuntimeError(f"Database '{self.pg_data_path}' shutdown error:\n{str(e)}")

    async def start_db(self):
        res = await self.conn.run_command(f"su - postgres -c '{self.pg_bin_path}/pg_ctl start -D {self.pg_data_path}'")
        return res

    async def sync(self):
        ...

    async def drop_caches(self):
        ...


def get_conn_type_tasks(type):
    if type == ConnectionType.SSH:
        return SSHTasks
    if type == ConnectionType.DOCKER:
        return DockerTasks
    if type == ConnectionType.LOCAL:
        return LocalConnTasks


async def collect_db_logs(client, db_conn, log_conf, logger, report):
    """
    If DB info was collected and log collection is enabled,
    fetch the log directory and call collect_logs.
    """
    if db_conn and log_conf.get("collect_pg_logs"):
        try:
            log_dir = await db_conn.fetchval("show log_directory")
            await collect_logs(client, log_dir, report["report_name"])
        except Exception as e:
            logger.warning(f"Error collecting logs: {str(e)}")
