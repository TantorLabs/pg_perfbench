import os
import sys
import glob
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

from pg_perfbench.const import LogLevel, LOGS_FOLDER


def display_user_configuration(raw_args, logger):
    message_lines: list[str] = ['Incoming parameters:']
    message_lines.extend(
        f'#   {name} = {value}'
        for name, value in raw_args.items()
        if value is not None
    )
    message_lines.append(f'#{"-" * 35}')
    logger.info('\n'.join(message_lines))


def setup_logger(raw_log_level, arg_clear_logs = False):
    # optional clearing of old logs
    if arg_clear_logs:
        clear_logs()
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
    log_level = LogLevel(raw_log_level)
    log = logging.getLogger()
    logging.getLogger("paramiko").setLevel(logging.CRITICAL)
    logging.getLogger("asyncssh").setLevel(logging.CRITICAL)
    logging.getLogger("docker").setLevel(logging.CRITICAL)
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)
    logging.getLogger("asyncio").setLevel(logging.CRITICAL)

    if (log_level_int := log_level.as_level_int_value()) is None:
        log.setLevel(logging.INFO)
        log.error('Incorrectly specified --log-level, automatically set to "info" level.')
    log.setLevel(log_level_int)
    log.info('Logging level: %s', log_level)
    if arg_clear_logs:
        log.info("Clearing logs folder.")
    return log


def clear_logs():
    files = glob.glob(str(LOGS_FOLDER / '*.log'))
    for f in files:
        os.remove(f)
