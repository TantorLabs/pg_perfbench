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


class InfoCollector:
    """
    A static utility class to collect system and database configuration info,
    generate reports, and optionally collect PostgreSQL logs.
    """

    @staticmethod
    async def prepare_report(report_conf: dict, logger) -> dict:
        """
        Loads the report template and sets its metadata fields.
        """
        template_path = report_conf['report_template']
        report = get_report_structure(template_path)
        report['description'] = get_datetime_report('%d/%m/%Y %H:%M:%S')

        report['report_name'] = report_conf.get(
            'report_name', f'{WorkMode.BENCHMARK}-{DEFAULT_REPORT_NAME}'
        )
        return report

    @staticmethod
    async def handle_db_info(client, conn_type: str, db_conf: dict, logger):
        """
        Prepares the database for collecting metrics:
        - sends custom config if available,
        - starts PostgreSQL,
        - connects to the DB.
        Returns an asyncpg connection or None.
        """
        db_conn = None
        db_env = db_conf.get('db_env')
        if db_env and isinstance(db_env, dict):
            # Send custom configuration file if provided
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

            # Start the PostgreSQL server
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

            # Connect to the PostgreSQL database
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

    @staticmethod
    async def collect_monitoring_info(
        logger, client, db_conn, report_data: dict, report: dict
    ):
        """
        Fills the report with system and database monitoring info.
        """
        await fill_info_report(logger, client, db_conn, report_data, report)
        logger.info('Monitoring info collected successfully.')

    @staticmethod
    async def collect_logs_if_needed(
        args: dict, log_conf: dict, logger, client, db_conn, report: dict
    ):
        """
        Collects PostgreSQL logs if requested in configuration.
        """
        if args['mode'] in [
            WorkMode.COLLECT_DB_INFO,
            WorkMode.COLLECT_ALL_INFO,
        ]:
            if log_conf.get('collect_pg_logs') and db_conn:
                await collect_db_logs(logger, client, db_conn, report)
                await db_conn.close()
                logger.info('Database connection closed.')

    @staticmethod
    async def collect_info(
        args: dict,
        conn_type: str,
        conn_conf: dict,
        db_conf: dict,
        report_conf: dict,
        log_conf: dict,
        logger,
    ) -> dict | None:
        """
        Orchestrates full process of collecting system and DB info,
        generating and returning a report dictionary.
        """
        if 'report_template' not in report_conf:
            logger.error('Missing "report_template" in report_conf.')
            return None

        display_user_configuration(args, logger)

        try:
            # Step 1: Prepare report structure
            report = await InfoCollector.prepare_report(report_conf, logger)
            logger.info('Report template loaded successfully.')
            report_data = {'args': args, 'report_conf': report_conf}

            # Step 2: Initialize connection object
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

                # Step 3: Handle optional DB setup and connection
                if args['mode'] in [
                    WorkMode.COLLECT_DB_INFO,
                    WorkMode.COLLECT_ALL_INFO,
                ]:
                    db_conn = await InfoCollector.handle_db_info(
                        client, conn_type, db_conf, logger
                    )
                    logger.info(
                        'Database connection established for collecting DB info.'
                    )

                # Step 4: Collect metrics
                await InfoCollector.collect_monitoring_info(
                    logger, client, db_conn, report_data, report
                )

                # Step 5: Optionally collect PostgreSQL logs
                await InfoCollector.collect_logs_if_needed(
                    args, log_conf, logger, client, db_conn, report
                )

            logger.info('Collect info process completed successfully.')
            return report

        except FileNotFoundError as fe:
            logger.error(f'File not found error: {str(fe)}')
            logger.error(
                'No report has been generated due to missing template.'
            )
            return None
        except Exception as e:
            logger.error(f'Unexpected error in collect_info: {str(e)}')
            logger.error(
                'Emergency termination. No report has been generated.'
            )
            raise
