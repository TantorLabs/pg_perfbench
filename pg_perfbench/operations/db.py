import asyncio
import logging
import os
import re
import subprocess
from typing import Any
import time

import asyncpg

from pg_perfbench.connections.common import Runnable
from pg_perfbench.const import DEFAULT_REPORT_NAME
from pg_perfbench.context.schemes.db import DBParameters
from pg_perfbench.exceptions import exception_helper


log = logging.getLogger(__name__)


async def init_db(db: DBParameters) -> None:
    terminate_db_pid_sql = f"""
        SELECT pg_terminate_backend(pid)
          FROM pg_stat_activity
         WHERE pid <> pg_backend_pid()
               AND datname = '{db.pg_database}'
    """
    create_test_db_sql = f"""
        CREATE DATABASE {db.pg_database}
               WITH
               OWNER = {db.pg_user}
               ENCODING = 'UTF8'
               LC_COLLATE = 'en_US.UTF-8'
               LC_CTYPE = 'en_US.UTF-8'
               template = template0
    """
    drop_database_db_sql = f"""
            DROP DATABASE IF EXISTS {db.pg_database}
    """
    db = await asyncpg.connect(
        host=db.pg_host,
        port=db.pg_port,
        user=db.pg_user,
        database='postgres',
        password=db.pg_password,
    )
    log.info('Terminating other sessions to the test DB')
    await db.execute(terminate_db_pid_sql)
    log.info('Dropping test DB')
    await db.execute(drop_database_db_sql)
    log.info('Creating pristine test DB')
    await db.execute(create_test_db_sql)
    await db.close()


async def load_dbobj(program: str) -> str:
    try:
        result = await run_command(program)
        return result
    except Exception as e:
        log.error(str(e))
        log.error(exception_helper(show_traceback=True))
        raise Exception


async def drop_cache(connection: Runnable, db_params: DBParameters) -> None:
    await connection.run(
        f'{db_params.pg_bin_path}/pg_ctl stop -D {db_params.pg_data_directory_path}',
    )
    await connection.run('sync')
    await connection.run('sudo /bin/sh -c "echo 3 | /usr/bin/tee /proc/sys/vm/drop_caches"')
    await connection.run(
        f'{db_params.pg_bin_path}/pg_ctl start -D '
        f'{db_params.pg_data_directory_path}'
    )


async def run_command(program: str, args: list[str]) -> str:

    process = await asyncio.create_subprocess_exec(
        program,
        *args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        log.error('Standard Error: %s', stderr.decode('utf-8', errors='replace'))
        raise Exception

    await process.wait()  # Wait for the process to exit if it hasn't yet

    return stdout.decode('utf-8')


async def run_command(command: str, check: bool = True) -> str:
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        shell=True,  # Important for running a shell command
        limit=262144,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0 and check:
        log.error(
            'Standard Error: %s', stderr.decode('utf-8', errors='replace')
        )
        raise Exception

    await process.wait()  # Wait for the process to exit if it hasn't yet

    return stdout.decode('utf-8')


# fmt: off
# TODO: enable formatting after cleaning this function
def get_pgbench_results(pgbench_output: str) -> dict[str, Any]:
    def get_val(str_v, t):
        for m in str_v:
            sub_str = pgbench_output[m.span()[0]: m.span()[1]]
            val = re.finditer(r'\d+([.,]\d+)?', sub_str)

            for vv in val:
                if t == 'float':
                    val = sub_str[vv.span()[0]: vv.span()[1]]
                    return float(sub_str[vv.span()[0]: vv.span()[1]])
                if t == 'int':
                    val = sub_str[vv.span()[0]: vv.span()[1]]
                    return int(sub_str[vv.span()[0]: vv.span()[1]])

    return {
        'clients': get_val(
            re.finditer(r'number\sof\sclients\:\s(\d+)', pgbench_output),
            'int',
        ),
        'number of transactions actually processed': get_val(
            re.finditer(
                r'number\sof\stransactions\sactually\sprocessed\:\s((\d+)/\d+|\d+)',
                pgbench_output,
            ),
            'int',
        ),
        'latency average': get_val(
            re.finditer(r'latency\saverage\s=\s\d+((.|,)\d+)?\sms', pgbench_output),
            'float',
        ),
        'initial connection time': get_val(
            re.finditer(r'initial\sconnection\stime\s=\s\d+((.|,)\d+)?\sms', pgbench_output),
            'float',
        ),
        'tps': get_val(
            re.finditer(r'tps\s=\s\d+((.|,)\d+)?', pgbench_output),
            'float',
        ),
    }
# fmt: on


async def wait_for_database_availability(db: DBParameters) -> bool:
    for attempt in range(1, 11):  # Adjust the number of attempts as needed
        try:
            db_connection = await asyncpg.connect(
                host=db.pg_host,
                port=db.pg_port,
                user=db.pg_user,
                database='postgres',
                password=db.pg_password,
            )
            await db_connection.fetchval('SELECT 1')
            await db_connection.close()
            print('Database is available.')
            return True
        except (asyncpg.PostgresError, ConnectionError) as e:
            log.warning(
                f'Database not yet available. Attempt {attempt}/10. Error: {e}'
            )
            time.sleep(1)
    else:
        print('Failed to connect to the database after multiple attempts.')
        raise Exception('Database not available.')
