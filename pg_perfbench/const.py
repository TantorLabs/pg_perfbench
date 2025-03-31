import enum
import logging
import sys
from datetime import datetime
from pathlib import Path

# Conditionally import StrEnum depending on Python version
if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from aenum import StrEnum

VERSION = '0.0.2'  # FIXME: print real app version here
SOURCE_ROOT_FOLDER = Path(__file__).parent
PROJECT_ROOT_FOLDER = SOURCE_ROOT_FOLDER.parent
LOGS_FOLDER = PROJECT_ROOT_FOLDER / 'log'

REPORT_FOLDER = PROJECT_ROOT_FOLDER / 'report'
REPORT_TEMPLATE_FOLDER = SOURCE_ROOT_FOLDER / 'templates'

BENCHMARK_TEMPLATE_JSON_NAME = 'benchmark_report_struct.json'
BENCHMARK_TEMPLATE_JSON_PATH = (
    REPORT_TEMPLATE_FOLDER / BENCHMARK_TEMPLATE_JSON_NAME
)

DB_INFO_TEMPLATE_JSON_NAME = 'db_info_report_struct.json'
DB_INFO_TEMPLATE_JSON_PATH = (
    REPORT_TEMPLATE_FOLDER / DB_INFO_TEMPLATE_JSON_NAME
)

SYS_INFO_TEMPLATE_JSON_NAME = 'sys_info_report_struct.json'
SYS_INFO_TEMPLATE_JSON_PATH = (
    REPORT_TEMPLATE_FOLDER / SYS_INFO_TEMPLATE_JSON_NAME
)

ALL_INFO_TEMPLATE_JSON_NAME = 'all_info_report_struct.json'
ALL_INFO_TEMPLATE_JSON_PATH = (
    REPORT_TEMPLATE_FOLDER / ALL_INFO_TEMPLATE_JSON_NAME
)

SHELL_COMMANDS_PATH = SOURCE_ROOT_FOLDER / 'commands' / 'bash_commands'
SQL_COMMANDS_PATH = SOURCE_ROOT_FOLDER / 'commands' / 'sql_commands'

REPORT_TIMESTAMP = datetime.now()


def get_datetime_report(format: str = '%d/%m/%Y %H:%M:%S'):
    """Return the current report timestamp as a string in the specified format."""
    return REPORT_TIMESTAMP.strftime(format)


CURRENT_TIME = get_datetime_report('%Y-%m-%d_%H-%M-%S')
DEFAULT_REPORT_NAME = f'report_{CURRENT_TIME}'

LOCAL_DB_LOGS_PATH = PROJECT_ROOT_FOLDER / 'db_logs'
DEFAULT_LOG_ARCHIVE_NAME = f'logs_archive_report_{CURRENT_TIME}.tar.gz'
SRC_LOG_ARCHIVE_DIR = '/tmp/log_archive'


@enum.unique
class WorkMode(StrEnum):
    """Enumeration of application work modes."""

    BENCHMARK = 'benchmark'
    JOIN = 'join'
    COLLECT_SYS_INFO = 'collect-sys-info'
    COLLECT_DB_INFO = 'collect-db-info'
    COLLECT_ALL_INFO = 'collect-all-info'


@enum.unique
class WorkloadTypes(StrEnum):
    """Enumeration of supported workload types."""

    CUSTOM = 'custom'
    DEFAULT = 'default'


@enum.unique
class ConnectionType(StrEnum):
    """Enumeration of database connection types."""

    SSH = 'ssh'
    LOCAL = 'local'
    DOCKER = 'docker'


@enum.unique
class LogLevel(StrEnum):
    """Enumeration for logging levels."""

    INFO = 'info'
    DEBUG = 'debug'
    ERROR = 'error'

    def as_level_int_value(self) -> int | None:
        """Convert the enumeration member to an integer logging level."""
        if self is LogLevel.INFO:
            return logging.INFO
        elif self is LogLevel.DEBUG:
            return logging.DEBUG
        elif self is LogLevel.ERROR:
            return logging.ERROR
        return None
