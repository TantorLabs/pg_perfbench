import asyncpg
import os

from pg_perfbench.const import (
    WorkMode, DEFAULT_REPORT_NAME, BENCHMARK_TEMPLATE_JSON_PATH,
    get_datetime_report
)
from pg_perfbench.connections import get_connection
from pg_perfbench.db_operations import get_conn_type_tasks, DBTasks
from pg_perfbench.report_processing import fill_info_report, get_report_structure
from pg_perfbench.report_commands import collect_logs
from pg_perfbench.log import display_user_configuration


async def collect_info(
    args,
    conn_type,
    conn_conf,
    db_conf,
    report_conf,
    log_conf,
    logger
) -> dict | None:

    if 'report_template' not in report_conf:
        logger.error("Missing 'report_template' in report_conf.")
        return None

    # display run parameters
    display_user_configuration(args, logger)

    try:
        # load the specified report template
        template_path = report_conf['report_template']
        report = get_report_structure(template_path)

        # Set description and report_name in the loaded template
        report['description'] = get_datetime_report('%d/%m/%Y %H:%M:%S')
        if report_conf.get('report_name') is None:
            # Fallback naming for the report
            report['report_name'] = f'{WorkMode.BENCHMARK}-{DEFAULT_REPORT_NAME}'
        else:
            report['report_name'] = report_conf['report_name']

        # Prepare final result object (if needed)
        # we can store additional data in 'report_data' if necessary
        report_data = {
            'args': args,
            'report_conf': report_conf
        }

        # build a connection (SSH or Docker)
        connection_class = get_connection(conn_type)
        if not connection_class:
            logger.error(f"Unknown connection type: {conn_type}. Cannot proceed.")
            return None

        connection = connection_class(**conn_conf)
        connection.logger = logger

        async with connection as client:
            db_conn = None
            # check if user wants to collect DB info
            # (COLLECT_DB_INFO or COLLECT_ALL_INFO)
            if args['mode'] in [WorkMode.COLLECT_DB_INFO, WorkMode.COLLECT_ALL_INFO]:
                db_env = db_conf.get('db_env')
                if db_env and isinstance(db_env, dict):
                    if 'pg_custom_config' in db_env:
                        custom_config_path = db_env['pg_custom_config']
                        dest_data_path = db_env.get('pg_data_path', '')
                        if os.path.exists(custom_config_path):
                            try:
                                await client.send_file(custom_config_path, dest_data_path)
                                logger.info(f'Custom config \"{custom_config_path}\" '
                                            f'moved to \"{dest_data_path}\"')
                            except Exception as e:
                                logger.warning(f"Failed to send custom config: {str(e)}")
                        else:
                            logger.warning(f"pg_custom_config file does not exist: {custom_config_path}")

                    # start DB if tasks factory is available
                    tasks = get_conn_type_tasks(conn_type)
                    if tasks:
                        task_object = tasks(db_conf=db_env, conn=client)
                        await task_object.start_db()
                    else:
                        logger.warning(f"No task factory for connection type {conn_type}")

                    # connect to actual database
                    db_conn_params = db_conf.get('db_conn_params')
                    if db_conn_params and isinstance(db_conn_params, dict):
                        try:
                            db_conn = await asyncpg.connect(**db_conn_params)
                        except Exception as e:
                            logger.error(f"Failed to connect to DB: {str(e)}")
                            db_conn = None
                    else:
                        logger.warning("No valid 'db_conn_params' found. Skipping DB actions.")

            # fill final info from shell/sql scripts or python calls
            await fill_info_report(client, db_conn, report_data, report)

            # if DB info was collected, possibly gather logs
            if args['mode'] in [WorkMode.COLLECT_DB_INFO, WorkMode.COLLECT_ALL_INFO]:
                if db_conn and log_conf.get('collect_pg_logs'):
                    try:
                        log_dir = await db_conn.fetchval('show log_directory')
                        await collect_logs(client, log_dir, report['report_name'])
                    except Exception as e:
                        logger.warning(f"Error collecting logs: {str(e)}")

                if db_conn:
                    await db_conn.close()

        return report

    except FileNotFoundError as fe:
        logger.error(f"File not found error: {str(fe)}")
        logger.error('No report has been generated due to missing template.')
        return None
    except Exception as e:
        logger.error(f"Unexpected error in collect_info: {str(e)}")
        logger.error('Emergency termination. No report has been generated.')
        raise