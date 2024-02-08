import logging
import os

log = logging.getLogger(__name__)


def config_format_check(config_path: str) -> bool:
    if config_path:
        if os.path.isfile(config_path):
            _, file_extension = os.path.splitext(config_path)
            if file_extension != '.conf':
                log.error(
                    "The specified file is not a '*.conf' configuration file."
                )
                return False

    return True
