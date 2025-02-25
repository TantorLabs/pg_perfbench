import asyncio
import asyncpg
from typing import Any, List, Union
import re

from pg_perfbench.const import (
    WorkMode, DEFAULT_REPORT_NAME, BENCHMARK_TEMPLATE_JSON_PATH,
    get_datetime_report
)
from pg_perfbench.connections import get_connection
from pg_perfbench.db_operations import TASK_FACTORIES, DBTasks
from pg_perfbench.report_processing import fill_info_report, get_report_structure
from pg_perfbench.report_commands import collect_logs
from pg_perfbench.log import display_user_configuration


def get_pgbench_results(pgbench_output: str) -> List[Union[int, float]]:
    # This function extracts key performance numbers from pgbench output
    def get_val(iter_matches, val_type: str) -> Union[int, float, None]:
        for match_obj in iter_matches:
            sub_str = pgbench_output[match_obj.span()[0]: match_obj.span()[1]]
            val_iter = re.finditer(r'\d+([.,]\d+)?', sub_str)
            for vv in val_iter:
                numeric_str = sub_str[vv.span()[0]: vv.span()[1]]
                numeric_str = numeric_str.replace(',', '.')
                if val_type == 'float':
                    return float(numeric_str)
                elif val_type == 'int':
                    return int(numeric_str)
        return None

    # search patterns
    clients = get_val(
        re.finditer(r'number\sof\sclients\:\s(\d+)', pgbench_output),
        'int'
    )
    duration = get_val(
        re.finditer(r'duration\:\s(\d+)', pgbench_output),
        'int'
    )
    transactions = get_val(
        re.finditer(r'number\sof\stransactions\sactually\sprocessed\:\s((\d+)/\d+|\d+)', pgbench_output),
        'int'
    )
    latency_avg = get_val(
        re.finditer(r'latency\saverage\s=\s\d+((.|,)\d+)?\sms', pgbench_output),
        'float'
    )
    init_conn_time = get_val(
        re.finditer(r'initial\sconnection\stime\s=\s\d+((.|,)\d+)?\sms', pgbench_output),
        'float'
    )
    tps = get_val(
        re.finditer(r'tps\s=\s\d+((.|,)\d+)?', pgbench_output),
        'float'
    )

    return [clients, duration, transactions, latency_avg, init_conn_time, tps]


def get_filled_load_commands(db_conf, workload_conf, pgbench_param, iter_amount) -> list[str]:
    # fill placeholders in init_command and workload_command with actual db_conf and iteration value
    arg_values = {}
    init_command = workload_conf['init_command']
    workload_command = workload_conf['workload_command']

    arg_values.update(db_conf)
    arg_values.update(workload_conf)
    arg_values.update({pgbench_param: iter_amount})

    for key, value in arg_values.items():
        if isinstance(key, str):
            placeholder = ''.join(['ARG_', str(key).upper()])
            init_command = init_command.replace(placeholder, str(value))
            workload_command = workload_command.replace(placeholder, str(value))

    return [init_command, workload_command]


def load_iterations_config(db_conf, workload_conf):
    # prepare a list of [init_command, workload_command] sets for each iteration
    if not workload_conf or not isinstance(workload_conf, dict):
        return []

    # Basic checks for mandatory fields
    pgbench_param_name = workload_conf.get('pgbench_iter_name')
    iter_list = workload_conf.get('pgbench_iter_list')
    if not pgbench_param_name or not iter_list or not isinstance(iter_list, list):
        return []

    if 'init_command' not in workload_conf or 'workload_command' not in workload_conf:
        return []

    load_iterations = []
    for iteration in iter_list:
        commands = get_filled_load_commands(db_conf, workload_conf, pgbench_param_name, iteration)
        load_iterations.append(commands)

    return load_iterations


async def run_command(logger, command: str, check: bool = True) -> str:
    # run shell command asynchronously
    if not command.strip():
        logger.warning("Attempting to run an empty command string.")
        return ''

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True,
            limit=262144,
        )
    except Exception as e:
        logger.error(f"Failed to start subprocess for command: {command}\nError: {str(e)}")
        return ''

    stdout, stderr = await process.communicate()

    # if return code != 0, log error if check is True
    if process.returncode != 0:
        logger.error(f"Command '{command}' failed with exit code {process.returncode}.")
        logger.error(f"STDERR: {stderr.decode('utf-8', errors='replace')}")
        if check:
            # If we want to fail on error
            raise Exception(f"Command '{command}' returned non-zero exit code.")
    await process.wait()

    return stdout.decode('utf-8')


async def reset_db_environment(logger, conn_type, conn, db_conf, workload_conf):
    # stop DB, drop DB, sync and drop caches, then start DB and init DB
    try:
        db_tasks = DBTasks(db_conf, logger)
        tasks = TASK_FACTORIES[conn_type](db_conf=workload_conf, conn=conn)

        await tasks.start_db()
        await db_tasks.drop_db()
        await tasks.stop_db()
        await tasks.sync()
        await tasks.drop_caches()
        await tasks.start_db()
        await db_tasks.init_db()
        await db_tasks.check_db_access()
    except Exception as e:
        logger.error(f"Failed to reset DB environment: {str(e)}")
        raise


async def run_benchmark(logger, load_iteration: [Any]):
    # first command is init_command, second is workload_command
    init_cmd = load_iteration[0]
    workload_cmd = load_iteration[1]

    logger.info(f'Initial command executing:\n {init_cmd}')
    init_result = await run_command(logger, init_cmd, check=True)
    logger.info(f'Initial command result: \n {init_result}')

    perf_result = await run_command(logger, workload_cmd, check=True)
    logger.info(f'Performance command result: \n {perf_result}')

    if not perf_result.strip():
        logger.warning("Workload command returned an empty or whitespace-only result.")

    return get_pgbench_results(perf_result)


async def run_benchmark_and_collect_metrics(
        args,
        conn_type,
        conn_conf,
        db_conf,
        workload_conf,
        report_conf,
        log_conf,
        logger
) -> dict[str:Any] | None:
    perf_results = []
    report_data = {
        'args': args,
        'workload_conf': workload_conf,
        'report_conf': report_conf
    }

    display_user_configuration(args, logger)

    try:
        # load base report template
        report = get_report_structure(BENCHMARK_TEMPLATE_JSON_PATH)
        report['description'] = get_datetime_report('%d/%m/%Y %H:%M:%S')
        if report_conf['report_name'] is None:
            report['report_name'] = f'{WorkMode.BENCHMARK}-{DEFAULT_REPORT_NAME}'
        else:
            report['report_name'] = report_conf['report_name']

        # prepare iteration commands
        load_iterations = load_iterations_config(db_conf, workload_conf)
        if not load_iterations:
            logger.error("No valid load iterations configured. Check pgbench_iter_list and commands.")
            return None

        # establish a connection (SSH or Docker)
        connection_class = get_connection(conn_type)
        if not connection_class:
            logger.error(f"No valid connection factory for type: {conn_type}")
            return None

        connection = connection_class(**conn_conf)
        connection.logger = logger

        async with connection as client:
            # send custom config if present
            if 'pg_custom_config' in workload_conf:
                custom_config_path = workload_conf['pg_custom_config']
                db_data_path = workload_conf.get('pg_data_path', '')
                try:
                    await client.send_file(custom_config_path, db_data_path)
                    logger.info(f'Custom config \"{custom_config_path}\" '
                                f'moved to \"{db_data_path}\"')
                except Exception as e:
                    logger.warning(f"Failed to send custom config: {str(e)}")

            # run each iteration of the benchmark
            for load_iteration in load_iterations:
                await reset_db_environment(logger, conn_type, client, db_conf, workload_conf)
                bench_result = await run_benchmark(logger, load_iteration)
                perf_results.append(bench_result)

            # store pgbench results
            report_data['pgbench_outputs'] = perf_results

            # connect to PostgreSQL to fill additional info
            db_conn = await asyncpg.connect(**db_conf)
            await fill_info_report(client, db_conn, report_data, report)

            # optionally collect DB logs
            if log_conf.get('collect_pg_logs'):
                log_dir = await db_conn.fetchval('show log_directory')
                await collect_logs(client, log_dir, report['report_name'])

            await db_conn.close()

        if not perf_results:
            logger.warning("No benchmark results were collected (perf_results is empty).")

        return report

    except Exception as e:
        logger.error(str(e))
        logger.error('Emergency program termination. No report has been generated.')
        raise