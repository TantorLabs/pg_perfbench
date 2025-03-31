import asyncpg
from typing import Any, List, Union
import re

from pg_perfbench.const import (
    WorkMode,
    DEFAULT_REPORT_NAME,
    BENCHMARK_TEMPLATE_JSON_PATH,
    get_datetime_report,
)
from pg_perfbench.connections import get_connection
from pg_perfbench.db_operations import (
    get_conn_type_tasks,
    DBTasks,
    run_command,
    collect_db_logs,
)
from pg_perfbench.report.processing import get_report_structure
from pg_perfbench.report.commands import fill_info_report
from pg_perfbench.log import display_user_configuration


def get_pgbench_results(pgbench_output: str) -> List[Union[int, float]]:
    # This function extracts key performance numbers from pgbench output
    def get_val(iter_matches, val_type: str) -> Union[int, float, None]:
        for match_obj in iter_matches:
            sub_str = pgbench_output[match_obj.span()[0] : match_obj.span()[1]]
            val_iter = re.finditer(r'\d+([.,]\d+)?', sub_str)
            for vv in val_iter:
                numeric_str = sub_str[vv.span()[0] : vv.span()[1]]
                numeric_str = numeric_str.replace(',', '.')
                if val_type == 'float':
                    return float(numeric_str)
                elif val_type == 'int':
                    return int(numeric_str)
        return None

    # search patterns
    clients = get_val(
        re.finditer(r'number\sof\sclients\:\s(\d+)', pgbench_output), 'int'
    )
    duration = get_val(
        re.finditer(r'duration\:\s(\d+)', pgbench_output), 'int'
    )
    transactions = get_val(
        re.finditer(
            r'number\sof\stransactions\sactually\sprocessed\:\s((\d+)/\d+|\d+)',
            pgbench_output,
        ),
        'int',
    )
    latency_avg = get_val(
        re.finditer(
            r'latency\saverage\s=\s\d+((.|,)\d+)?\sms', pgbench_output
        ),
        'float',
    )
    init_conn_time = get_val(
        re.finditer(
            r'initial\sconnection\stime\s=\s\d+((.|,)\d+)?\sms', pgbench_output
        ),
        'float',
    )
    tps = get_val(
        re.finditer(r'tps\s=\s\d+((.|,)\d+)?', pgbench_output), 'float'
    )

    return [clients, duration, transactions, latency_avg, init_conn_time, tps]


def get_filled_load_commands(
    db_conf, workload_conf, pgbench_param, iter_amount
) -> list[str]:
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
            workload_command = workload_command.replace(
                placeholder, str(value)
            )

    return [init_command, workload_command]


def load_iterations_config(db_conf, workload_conf):
    db_conf_pg = {}
    for key, value in db_conf.items():
        new_key = f'pg_{key}'
        db_conf_pg[new_key] = value
    # prepare a list of [init_command, workload_command] sets for each iteration
    if not workload_conf or not isinstance(workload_conf, dict):
        return []

    # Basic checks for mandatory fields
    pgbench_param_name = workload_conf.get('pgbench_iter_name')
    iter_list = workload_conf.get('pgbench_iter_list')
    if (
        not pgbench_param_name
        or not iter_list
        or not isinstance(iter_list, list)
    ):
        return []

    if (
        'init_command' not in workload_conf
        or 'workload_command' not in workload_conf
    ):
        return []

    load_iterations = []
    for iteration in iter_list:
        commands = get_filled_load_commands(
            db_conf_pg, workload_conf, pgbench_param_name, iteration
        )
        load_iterations.append(commands)

    return load_iterations


async def reset_db_environment(
    logger, conn_type, conn, db_conf, workload_conf
):
    # stop DB, drop DB, sync and drop caches, then start DB and init DB
    try:
        db_tasks = DBTasks(db_conf, logger)
        conn_tasks = get_conn_type_tasks(conn_type)(
            db_conf=workload_conf, conn=conn, logger=logger
        )
        try:
            await conn_tasks.start_db()
        except Exception as e:
            logger.warning(str(e))
        await db_tasks.check_db_access()
        await db_tasks.drop_db()
        await conn_tasks.stop_db()
        await conn_tasks.sync()
        await conn_tasks.drop_caches()
        await conn_tasks.start_db()
        await db_tasks.check_db_access()
        await db_tasks.init_db()
        await db_tasks.check_user_db_access()
    except Exception as e:
        raise RuntimeError(f'Failed to reset DB environment:\n{str(e)}')


async def run_benchmark(logger, load_iteration: [Any]):
    # first command is init_command, second is workload_command
    init_cmd = load_iteration[0]
    workload_cmd = load_iteration[1]

    logger.info(f'Initial command executing:\n {init_cmd}')
    init_result = await run_command(logger, init_cmd, check=True)
    logger.info(f'Initial command result: \n {init_result}')

    logger.info(f'Performance command executing: \n {workload_cmd}')
    perf_result = await run_command(logger, workload_cmd, check=True)
    logger.info(f'Performance command result: \n {perf_result}')

    if not perf_result.strip():
        logger.warning(
            'Workload command returned an empty or whitespace-only result.'
        )

    return get_pgbench_results(perf_result)


async def run_benchmark_and_collect_metrics(
    args,
    conn_type,
    conn_conf,
    db_conf,
    workload_conf,
    report_conf,
    log_conf,
    logger,
) -> dict[str, any] | None:
    perf_results = []
    report_data = {
        'args': args,
        'workload_conf': workload_conf,
        'report_conf': report_conf,
    }
    display_user_configuration(args, logger)
    try:
        # Load base report template
        report = get_report_structure(BENCHMARK_TEMPLATE_JSON_PATH)
        report['description'] = get_datetime_report('%d/%m/%Y %H:%M:%S')
        if report_conf['report_name'] is None:
            report[
                'report_name'
            ] = f'{WorkMode.BENCHMARK}-{DEFAULT_REPORT_NAME}'
        else:
            report['report_name'] = report_conf['report_name']
        logger.info('Report template loaded successfully.')

        # Prepare iteration commands
        load_iterations = load_iterations_config(db_conf, workload_conf)
        if not load_iterations:
            logger.error('No valid load iterations configured.')
            return None
        logger.info(
            f'Load iterations configured successfully. Total iterations: {len(load_iterations)}'
        )

        # Choose connection type
        connection_class = get_connection(conn_type)
        if not connection_class:
            logger.error(f'No valid connection factory for type: {conn_type}')
            return None
        logger.info(f'Connection type selected: {conn_type}')

        connection = connection_class(**conn_conf)
        connection.logger = logger

        async with connection as client:
            logger.info('Connection established successfully.')
            # If custom config is specified, send it
            if (
                'pg_custom_config' in workload_conf
                and workload_conf['pg_custom_config']
            ):
                custom_config_path = workload_conf['pg_custom_config']
                db_data_path = workload_conf.get('pg_data_path', '')
                logger.info(f'Custom DB config selected: {custom_config_path}')
                remote_config = await client.send_pg_config_file(
                    custom_config_path, db_data_path
                )
                logger.info(
                    f"User's DB config set successfully: "
                    f"{workload_conf['pg_custom_config']} ---> {remote_config}"
                )

            # Run each load iteration
            logger.info('Start load testing.')
            for idx, load_iteration in enumerate(load_iterations, start=1):
                logger.info('Resetting the database.')
                await reset_db_environment(
                    logger, conn_type, client, db_conf, workload_conf
                )
                logger.info('Database reset.')
                logger.info(f'Starting load iteration {idx}...')
                bench_result = await run_benchmark(logger, load_iteration)
                perf_results.append(bench_result)
                logger.info(f'Load iteration {idx} result collected.')

            # Store pgbench results
            report_data['pgbench_outputs'] = perf_results
            # Connect to PostgreSQL to fill additional info

            logger.info('Collection of monitoring metrics.')
            db_conn = await asyncpg.connect(**db_conf)
            logger.info('Connected to DB.')
            await fill_info_report(
                logger, client, db_conn, report_data, report
            )
            logger.info('Monitoring info collected.')

            # Optionally collect DB logs
            if log_conf.get('collect_pg_logs'):
                await collect_db_logs(logger, client, db_conn, report)
            await db_conn.close()
            logger.info('Database connection closed.')

        logger.info('Benchmark process completed.')
        return report

    except Exception as e:
        logger.error(str(e))
        return None
