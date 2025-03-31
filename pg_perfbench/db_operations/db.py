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