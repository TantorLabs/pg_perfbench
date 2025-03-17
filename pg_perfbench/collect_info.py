import asyncpg
import os

from pg_perfbench.const import (
    WorkMode, DEFAULT_REPORT_NAME, BENCHMARK_TEMPLATE_JSON_PATH,
    get_datetime_report
)
from pg_perfbench.connections import get_connection
from pg_perfbench.db_operations import get_conn_type_tasks, DBTasks
from pg_perfbench.report.processing import get_report_structure
from pg_perfbench.report.commands import collect_logs, fill_info_report
from pg_perfbench.log import display_user_configuration


async def _prepare_report(report_conf, logger):
    """
    Loads the report template and sets its description and report_name.
    """
    template_path = report_conf["report_template"]
    report = get_report_structure(template_path)
    report["description"] = get_datetime_report("%d/%m/%Y %H:%M:%S")
    if report_conf.get("report_name") is None:
        report["report_name"] = f"{WorkMode.BENCHMARK}-{DEFAULT_REPORT_NAME}"
    else:
        report["report_name"] = report_conf["report_name"]
    return report


async def _handle_db_info(client, db_conf, logger):
    """
    Handles sending custom configuration, starting the database,
    and establishing a connection to the database.
    Returns an asyncpg connection or None.
    """
    db_conn = None
    db_env = db_conf.get("db_env")
    if db_env and isinstance(db_env, dict):
        if "pg_custom_config" in db_env:
            custom_config_path = db_env["pg_custom_config"]
            dest_data_path = db_env.get("pg_data_path", "")
            try:
                await client.send_pg_config_file(custom_config_path, dest_data_path)
                logger.info(f'Custom config "{custom_config_path}" moved to "{dest_data_path}"')
            except Exception as e:
                logger.warning(f"Failed to send custom config: {str(e)}")

        tasks = get_conn_type_tasks(conn_type)
        if tasks:
            task_object = tasks(db_conf=db_env, conn=client)
            try:
                await task_object.start_db()
            except Exception as e:
                logger.warning(str(e))
        else:
            logger.warning(f"No task factory for connection type {client.conn_params.get('connection_type')}")

        db_conn_params = db_conf.get("db_conn_params")
        if db_conn_params and isinstance(db_conn_params, dict):
            try:
                db_conn = await asyncpg.connect(**db_conn_params)
            except Exception as e:
                logger.error(f"Failed to connect to DB: {str(e)}")
                db_conn = None
        else:
            logger.warning("No valid 'db_conn_params' found. Skipping DB actions.")
    return db_conn


async def _collect_logs_if_needed(client, db_conn, log_conf, logger, report):
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


async def collect_info(
    args,
    conn_type,
    conn_conf,
    db_conf,
    report_conf,
    log_conf,
    logger
) -> dict | None:
    if "report_template" not in report_conf:
        logger.error("Missing 'report_template' in report_conf.")
        return None

    # Display run parameters.
    display_user_configuration(args, logger)

    try:
        report = await _prepare_report(report_conf, logger)

        report_data = {
            "args": args,
            "report_conf": report_conf
        }

        connection_class = get_connection(conn_type)
        if not connection_class:
            logger.error(f"Unknown connection type: {conn_type}. Cannot proceed.")
            return None

        connection = connection_class(**conn_conf)
        connection.logger = logger

        async with connection as client:
            db_conn = None
            if args["mode"] in [WorkMode.COLLECT_DB_INFO, WorkMode.COLLECT_ALL_INFO]:
                db_conn = await _handle_db_info(client, db_conf, logger)

            await fill_info_report(client, db_conn, report_data, report)
            if args["mode"] in [WorkMode.COLLECT_DB_INFO, WorkMode.COLLECT_ALL_INFO]:
                await _collect_logs_if_needed(client, db_conn, log_conf, logger, report)
                await db_conn.close()

        return report

    except FileNotFoundError as fe:
        logger.error(f"File not found error: {str(fe)}")
        logger.error("No report has been generated due to missing template.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in collect_info: {str(e)}")
        logger.error("Emergency termination. No report has been generated.")
        raise
