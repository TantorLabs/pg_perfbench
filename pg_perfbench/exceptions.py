import sys
import traceback

from pydantic import ValidationError


class CommonException(Exception):
    """Core application error."""

    def __init__(self, code, message, text_error=''):
        self.code = code
        self.message = message
        self.text_error = text_error
        super().__init__(self.message)


class ConfigError(CommonException):
    """Error happening during application config processing."""


def _format_field_name(field_name: str | int) -> str:
    if isinstance(field_name, int):
        return str(int)
    return field_name.replace('_', '-')


def _format_fields_name_sequence(fields: tuple[int | str, ...]) -> str:
    return ','.join(_format_field_name(f) for f in fields)


def format_pydantic_error(error: ValidationError) -> str:
    messages = [f'{error.title}: validation error']
    for e in error.errors():
        messages.append(f"    {_format_fields_name_sequence(e['loc'])}: {e['msg']}")
    return '\n'.join(messages)


def exception_helper(show_traceback: bool = True) -> str:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    exc_traceback = exc_traceback if show_traceback else None
    return '\n'.join(v for v in traceback.format_exception(exc_type, exc_value, exc_traceback))


class PerformTestError(CommonException):
    """Error performing pgbench load testing."""


class BashCommandException(Exception):
    """Bash script execution error."""

    def __init__(self, code, text_error=''):
        self.code = code
        self.text_error = text_error
