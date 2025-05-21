from .common import run_command


class LocalConnTasks:
    def __init__(self, db_conf, conn, logger):
        self.conn = conn
        self.pg_bin_path = db_conf['pg_bin_path']
        self.pg_data_path = db_conf['pg_data_path']
        self.logger = logger

    async def stop_db(self):
        try:
            res = await self.conn.run_command(
                f"su - postgres -c '{self.pg_bin_path}/pg_ctl stop -D {self.pg_data_path}'"
            )
            return res
        except Exception as e:
            raise RuntimeError(
                f"Database '{self.pg_data_path}' shutdown error:\n{str(e)}"
            )

    async def start_db(self):
        res = await self.conn.run_command(
            f"su - postgres -c '{self.pg_bin_path}/pg_ctl start -D {self.pg_data_path}'"
        )
        return res

    async def sync(self):
        self.logger.debug('Reset database host cache.')
        try:
            await run_command(self.logger, 'sync', True)
        except Exception as e:
            raise RuntimeError(
                f"Database '{self.pg_data_path}' shutdown error:\n{str(e)}"
            )

    async def drop_caches(self):
        cmd = (
            "sudo /bin/sh -c 'echo 3 | /usr/bin/tee /proc/sys/vm/drop_caches'"
        )
        await run_command(self.logger, cmd, True)
