import enum
import logging
import sys
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

    def as_level_int_value(self) -> int:
        if self is LogLevel.INFO:
            return logging.INFO
        if self is LogLevel.DEBUG:
            return logging.DEBUG
        return logging.ERROR
