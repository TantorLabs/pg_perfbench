from pg_perfbench.report.commands import collect_logs
from pg_perfbench.const import ConnectionType

from .db import DBTasks
from .conn_tasks import run_command, SSHTasks, DockerTasks, LocalConnTasks

__all__ = [
    'DBTasks',
    'SSHTasks',
    'DockerTasks',
    'LocalConnTasks',
    'run_command'
]


async def collect_db_logs(logger, client, db_conn, report):
    try:
        logger.info("Collection of database logs.")
        log_dir = await db_conn.fetchval("show log_directory")
        # If log_dir doesn't contain a slash, fetch data_directory and join them.
        if "/" not in log_dir:
            data_dir = await db_conn.fetchval("show data_directory")
            log_dir = f"{data_dir}/{log_dir}"
        log_report = await collect_logs(logger, client, log_dir, report["report_name"])
        if log_report:
            report["sections"]["result"]["reports"].update(log_report)
            logger.info("DB logs collected successfully.")

    except Exception as e:
        logger.error(f"Failed to collect DB logs: {e}")


def get_conn_type_tasks(type):
    if type == ConnectionType.SSH:
        return SSHTasks
    if type == ConnectionType.DOCKER:
        return DockerTasks
    if type == ConnectionType.LOCAL:
        return LocalConnTasks
