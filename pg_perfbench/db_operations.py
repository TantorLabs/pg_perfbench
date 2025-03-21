import asyncpg
import asyncio
import time

from pg_perfbench.const import ConnectionType
from pg_perfbench.report.commands import collect_logs


async def run_command(logger, command: str, check: bool = True) -> str:
    # run shell command asynchronously
    if not command.strip():
        raise Exception("Attempting to run an empty command string.")

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True,
            limit=262144,
        )
    except Exception as e:
        raise Exception(f"Failed to start subprocess for command: {command}\nError:\n{str(e)} .")

    stdout, stderr = await process.communicate()

    # if return code != 0, log error if check is True
    if process.returncode != 0:
        logger.error(f"Command '{command}' failed with exit code {process.returncode}.")
        logger.error(f"STDERR: {stderr.decode('utf-8', errors='replace')} .")
        if check:
            # If we want to fail on error
            raise Exception(f"Command '{command}' - returned non-zero exit code.")
    await process.wait()

    return stdout.decode('utf-8')


async def collect_db_logs(logger, client, db_conn, report):
    try:
        logger.info("Collection of database logs.")
        log_dir = await db_conn.fetchval("show log_directory")
        # If log_dir doesn't contain a slash, fetch data_directory and join them.
        if "/" not in log_dir:
            data_dir = await db_conn.fetchval("show data_directory")
            log_dir = f"{data_dir}/{log_dir}"
        log_report = await collect_logs(logger, client, log_dir, report["report_name"])
        if log_report:
            report["sections"]["result"]["reports"].update(log_report)
            logger.info("DB logs collected successfully.")
    except Exception as e:
        logger.error(f"Failed to collect DB logs: {e}")


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

    async def check_user_db_access(self):
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

    async def check_db_access(self):
        for attempt in range(1, 11):  # Adjust the number of attempts as needed
            try:
                db_connection = await asyncpg.connect(
                    host=self.db_conf['host'],
                    port=self.db_conf['port'],
                    user=self.db_conf['user'],
                    database="postgres",
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
            raise ConnectionError("Failed to connect to the database after multiple attempts."
                                  "\nVerify the database connection parameters.")


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
        self.logger.debug("Reset database host cache.")
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
            self.conn.close()
            return True
        except Exception as e:
            raise RuntimeError(f"Database '{self.pg_data_path}' shutdown error:\n{str(e)}")

    async def start_db(self):
        await self.conn.start()
        await asyncio.sleep(0.2)
        return True

    async def sync(self):
        self.logger.debug("Reset database host cache.")
        await run_command(self.logger, "sync", True)

    async def drop_caches(self):
        cmd = "sudo /bin/sh -c 'echo 3 | /usr/bin/tee /proc/sys/vm/drop_caches'"
        await run_command(self.logger, cmd, True)


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
        self.logger.debug("Reset database host cache.")
        try:
            await run_command(self.logger, "sync", True)
        except Exception as e:
            raise RuntimeError(f"Database '{self.pg_data_path}' shutdown error:\n{str(e)}")

    async def drop_caches(self):
        cmd = "sudo /bin/sh -c 'echo 3 | /usr/bin/tee /proc/sys/vm/drop_caches'"
        await run_command(self.logger, cmd, True)


def get_conn_type_tasks(type):
    if type == ConnectionType.SSH:
        return SSHTasks
    if type == ConnectionType.DOCKER:
        return DockerTasks
    if type == ConnectionType.LOCAL:
        return LocalConnTasks
