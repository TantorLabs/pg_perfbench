import asyncio
import logging
import sys
from typing import Any

import asyncpg

from pg_perfbench.cli.args_parser import get_args_parser
from pg_perfbench.connections import common as connection_common, get_connection
from pg_perfbench.const import VERSION, WorkMode
from pg_perfbench.context import Context, RawArgs, JoinContext, utils as context_utils
from pg_perfbench.env_data import JsonMethods
from pg_perfbench.exceptions import exception_helper, PerformTestError
from pg_perfbench.logs import clear_logs, set_logger_level, setup_logger
from pg_perfbench.operations import db as db_operations
from pg_perfbench.pgbench_utils import get_init_execution_command, get_pgbench_commands
from pg_perfbench.reports import report as general_reports, schemas as report_schemas
from pg_perfbench.join_reports import join_reports


log = logging.getLogger(__name__)
logging.getLogger('paramiko').setLevel(logging.CRITICAL)
logging.getLogger('asyncssh').setLevel(logging.CRITICAL)
logging.getLogger('pydantic_core').setLevel(logging.CRITICAL)
logging.getLogger('docker').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)
logging.getLogger('asyncio').setLevel(logging.CRITICAL)


def print_benchmark_welcome(raw_args: RawArgs) -> None:
    log.info(f'Version - {VERSION}')
    log.info('Started MainRoutine.run')
    message_lines: list[str] = ['Incoming parameters:']
    message_lines.extend(
        f'#   {name} = {value}'
        for name, value in context_utils.sanitize_raw_args(raw_args).items()
        if value is not None
    )
    message_lines.append(f'#{"-" * 35}')
    log.info('\n'.join(message_lines))


async def perform_test(
    ctx: Context,
    connection: connection_common.Runnable,
    pgbench_cmd: str,
) -> dict[str, Any]:
    try:
        log.debug('Benchmark preparation')
        await connection.drop_cache()   # restart database
        await db_operations.wait_for_database_availability(ctx.db)
        await db_operations.init_db(db=ctx.db)
        init_cmd = get_init_execution_command(ctx.db, ctx.workload)
        log.info(f'Create a database schema. Response: {init_cmd}')
        result = await db_operations.load_dbobj(init_cmd)
        log.debug('Result:\n %s', result)
        log.debug(f'Running performance test: {pgbench_cmd}')
        result = await db_operations.run_command(pgbench_cmd)
        log.debug(f'Performance test result: {result}')
        return db_operations.get_pgbench_results(result)
    except Exception as e:
        raise PerformTestError(2, f'Benchmark execution error: {e!s}')


async def run_benchmark_tests_suit(
    connection: connection_common.Runnable, ctx: Context
) -> list[Any]:
    runs = []
    log.info('Start benchmarking')
    pgbench_commands = get_pgbench_commands(ctx.db, ctx.workload)
    for chunk in pgbench_commands:
        log.info('Current benchmark iteration: %s', str(chunk))
        res = await perform_test(ctx, connection, chunk)
        log.info('The benchmark iteration is complete')
        if res is not None:
            runs.append(list(res.values()))
    return runs


async def run_benchmark(ctx: Context) -> report_schemas.Report | None:
    print_benchmark_welcome(ctx.raw_args)
    connection = get_connection(ctx.connection)
    try:
        main_report = general_reports.get_report_structure_from_json()
        async with connection as client:
            perf_result: list[Any] = await run_benchmark_tests_suit(client, ctx)
            jsonmethods = JsonMethods(perf_result, ctx)
            dbconn = await asyncpg.connect(
                host=ctx.db.pg_host,
                port=ctx.db.pg_port,
                user=ctx.db.pg_user,
                database='postgres',
                password=ctx.db.pg_password,
            )
            for key_s, section in main_report.sections.items():
                log.debug(f'Executing section: "{key_s}"')
                for key_r, report in section.reports.items():
                    log.debug(f'Item processing: "{key_r}"')
                    if isinstance(report, report_schemas.common.BaseReportShellCommand):
                        await report.set_data(client)
                    elif isinstance(report, report_schemas.common.BaseReportSQLCommand):
                        await report.set_data(dbconn)
                    elif isinstance(report, report_schemas.common.BaseReportPythonCommand):
                        report.set_data(getattr(jsonmethods, report.get_python_func_name())())
                    log.debug('Item completed')
                log.info(f'Execution of the section completed - "{key_s}"')

            await dbconn.close()
        return main_report
    except Exception as e:
        log.error(str(e))
        log.error(exception_helper(show_traceback=(ctx.service.log_level == 'debug')))
        log.error('Emergency program termination. No report has been generated.')
    return None


async def run():
    report = None
    args = get_args_parser().parse_args()
    if args.clear_logs:
        print('Clearing logs folder')
        clear_logs()
    setup_logger()
    set_logger_level(args.log_level)

    try:
        if args.mode == WorkMode.BENCHMARK and (context := Context.from_args_map(vars(args))):
            report = await run_benchmark(context)
        elif args.mode == WorkMode.JOIN and (context := JoinContext.from_args_map(vars(args))):
            report = join_reports(context)
    except Exception as e:
        log.error(f'pg_perfbench error: {str(e)}.')
        sys.exit(1)
    finally:
        if report is None:
            sys.exit(1)

    general_reports.save_report(report)
    log.info('Benchmark report saved successfully.')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
