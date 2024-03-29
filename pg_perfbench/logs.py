import os
import glob
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

from pg_perfbench.const import LogLevel
from pg_perfbench.const import LOGS_FOLDER


def setup_logger(raw_log_level) -> int:
    """Configure logger"""
    log_level = 0
    file_name = f'{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}.log'
    LOGS_FOLDER.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        format='{asctime} {levelname:>10s} {name:>35s} : {lineno:-4d} - {message}',
        style='{',
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(sys.stdout),
            RotatingFileHandler(
                LOGS_FOLDER / file_name,
                maxBytes=1024 * 10000,
                backupCount=10,
            ),
        ],
    )
    log_level = LogLevel(raw_log_level)     # FIXME: Soft validation of the --log-level flag
    log = logging.getLogger()

    if (log_level_int := log_level.as_level_int_value()) is None:
        log.setLevel(logging.INFO)
        log.error('Incorrectly specified --log-level, automatically set to "info" level.')
    log.setLevel(log_level_int)
    log.info('Logging level: %s', log_level)
    return log_level


def clear_logs():
    files = glob.glob(str(LOGS_FOLDER / '*.log'))
    for f in files:
        os.remove(f)
