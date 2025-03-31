import asyncpg

from pg_perfbench.const import (
    WorkMode,
    DEFAULT_REPORT_NAME,
    get_datetime_report,
)
from pg_perfbench.connections.common import get_connection
from pg_perfbench.db_operations import get_conn_type_tasks, collect_db_logs
from pg_perfbench.report.processing import get_report_structure
from pg_perfbench.report.commands import fill_info_report
from pg_perfbench.log import display_user_configuration


async def _prepare_report(report_conf, logger):
    """
    Loads the report template and sets its description and report_name.
    """
    template_path = report_conf['report_template']
    report = get_report_structure(template_path)
    report['description'] = get_datetime_report('%d/%m/%Y %H:%M:%S')
    if report_conf.get('report_name') is None:
        report['report_name'] = f'{WorkMode.BENCHMARK}-{DEFAULT_REPORT_NAME}'
    else:
        report['report_name'] = report_conf['report_name']
    return report


async def _handle_db_info(client, conn_type, db_conf, logger):
    """
    Handles sending custom configuration, starting the database,
    and establishing a connection to the database.
    Returns an asyncpg connection or None.
    """
    db_conn = None
    db_env = db_conf.get('db_env')
    if db_env and isinstance(db_env, dict):
        if 'pg_custom_config' in db_env:
            custom_config_path = db_env['pg_custom_config']
            dest_data_path = db_env.get('pg_data_path', '')
            try:
                await client.send_pg_config_file(
                    custom_config_path, dest_data_path
                )
                logger.info(
                    f'Custom config "{custom_config_path}" moved to "{dest_data_path}"'
                )
            except Exception as e:
                logger.warning(f'Failed to send custom config: {str(e)}')

        tasks = get_conn_type_tasks(conn_type)
        if tasks:
            task_object = tasks(db_conf=db_env, conn=client, logger=logger)
            try:
                await task_object.start_db()
            except Exception as e:
                logger.warning(str(e))
        else:
            logger.warning(
                f"No task factory for connection type {client.conn_params.get('connection_type')}"
            )

        db_conn_params = db_conf.get('db_conn_params')
        if db_conn_params and isinstance(db_conn_params, dict):
            try:
                db_conn = await asyncpg.connect(**db_conn_params)
            except Exception as e:
                logger.error(f'Failed to connect to DB: {str(e)}')
                db_conn = None
        else:
            logger.warning(
                "No valid 'db_conn_params' found. Skipping DB actions."
            )
    return db_conn


async def collect_info(
    args, conn_type, conn_conf, db_conf, report_conf, log_conf, logger
) -> dict | None:
    if 'report_template' not in report_conf:
        logger.error('Missing "report_template" in report_conf.')
        return None

    # Display run parameters.
    display_user_configuration(args, logger)

    try:
        # Prepare report template.
        report = await _prepare_report(report_conf, logger)
        logger.info('Report template loaded successfully.')

        report_data = {'args': args, 'report_conf': report_conf}

        # Choose connection type.
        connection_class = get_connection(conn_type)
        if not connection_class:
            logger.error(
                f'Unknown connection type: {conn_type}. Cannot proceed.'
            )
            return None
        logger.info(f'Connection type selected: {conn_type}')

        connection = connection_class(**conn_conf)
        connection.logger = logger

        async with connection as client:
            logger.info('Connection established successfully.')
            db_conn = None

            # If DB info is to be collected, establish DB connection.
            if args['mode'] in [
                WorkMode.COLLECT_DB_INFO,
                WorkMode.COLLECT_ALL_INFO,
            ]:
                db_conn = await _handle_db_info(
                    client, conn_type, db_conf, logger
                )
                logger.info(
                    'Database connection established successfully for collecting DB info.'
                )

            # Collect monitoring information.
            await fill_info_report(
                logger, client, db_conn, report_data, report
            )
            logger.info('Monitoring info collected successfully.')

            # Optionally collect DB logs.
            if args['mode'] in [
                WorkMode.COLLECT_DB_INFO,
                WorkMode.COLLECT_ALL_INFO,
            ]:
                if log_conf.get('collect_pg_logs'):
                    await collect_db_logs(logger, client, db_conn, report)
                await db_conn.close()
                logger.info('Database connection closed.')

        logger.info('Collect info process completed successfully.')
        return report

    except FileNotFoundError as fe:
        logger.error(f'File not found error: {str(fe)}')
        logger.error('No report has been generated due to missing template.')
        return None
    except Exception as e:
        logger.error(f'Unexpected error in collect_info: {str(e)}')
        logger.error('Emergency termination. No report has been generated.')
        raise
