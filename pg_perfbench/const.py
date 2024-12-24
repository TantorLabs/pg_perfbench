import enum
import logging
import sys
from datetime import datetime
from pathlib import Path

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from compatibility import StrEnum

VERSION = '0.0.1'  # FIXME: print real app version here
SOURCE_ROOT_FOLDER = Path(__file__).parent
PROJECT_ROOT_FOLDER = SOURCE_ROOT_FOLDER.parent
LOGS_FOLDER = PROJECT_ROOT_FOLDER / 'log'

REPORT_FOLDER = PROJECT_ROOT_FOLDER / 'report'
REPORT_TEMPLATE_FOLDER = SOURCE_ROOT_FOLDER / 'reports' / 'templates'
TEMPLATE_JSON_NAME = 'report_struct.json'
TEMPLATE_JSON_PATH = REPORT_TEMPLATE_FOLDER / TEMPLATE_JSON_NAME

SHELL_COMMANDS_PATH = SOURCE_ROOT_FOLDER / 'commands' / 'bash_commands'
SQL_COMMANDS_PATH = SOURCE_ROOT_FOLDER / 'commands' / 'sql_commands'

REPORT_TIMESTAMP = datetime.now()


def get_datetime_report(format: str = '%d/%m/%Y %H:%M:%S'):
    return REPORT_TIMESTAMP.strftime(format)


DEFAULT_REPORT_NAME  = f'report_{get_datetime_report("%Y-%m-%d_%H:%M:%S")}'

LOCAL_DB_LOGS_PATH = PROJECT_ROOT_FOLDER / 'db_logs'
DEFAULT_LOG_ARCHIVE_NAME = f'logs_archive_report_{get_datetime_report("%Y-%m-%d_%H-%M-%S")}.tar.gz'
LOG_ARCHIVE_DIR = '/tmp/log_archive'

@enum.unique
class WorkMode(StrEnum):
    BENCHMARK = 'benchmark'
    JOIN = 'join'


@enum.unique
class WorkloadTypes(StrEnum):
    CUSTOM = 'custom'
    DEFAULT = 'default'


@enum.unique
class BenchmarkProfile(StrEnum):
    TPC_C = 'tpc-c'
    TPC_DS = 'tpc-ds'
    TPC_E = 'tpc-e'


@enum.unique
class ConnectionType(StrEnum):
    SSH = 'ssh'
    LOCAL = 'local'
    DOCKER = 'docker'


@enum.unique
class LogLevel(StrEnum):
    INFO = 'info'
    DEBUG = 'debug'
    ERROR = 'error'

    def as_level_int_value(self) -> int | None:
        if self is LogLevel.INFO:
            return logging.INFO
        elif self is LogLevel.DEBUG:
            return logging.DEBUG
        elif self is logging.ERROR:
            return logging.ERROR
