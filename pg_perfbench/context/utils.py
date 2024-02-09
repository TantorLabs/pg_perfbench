import logging
from copy import deepcopy

from pg_perfbench.context.schemes.context import RawArgs

log = logging.getLogger(__name__)

# TODO: make RawArgs a dict-based class with additional methods, but pydantic-friendly
_SENSITIVE_FIELDS = ('pg_user_password', 'ssh_key')


def sanitize_raw_args(args: RawArgs) -> RawArgs:
    """Get given dictionary, but values of sensitive items were replaced with *."""
    result = deepcopy(args)
    for field in _SENSITIVE_FIELDS:
        if (value := result.get(field)) is None or not isinstance(value, str):
            continue
        result[field] = '*' * len(value)
    return result


def get_deparsed_arguments(args: RawArgs) -> list[tuple[str, ...]]:
    """Get list of arguments provided to the application"""
    result: list[tuple[str, ...]] = []
    for key, value in args.items():
        if value is None:
            continue
        if isinstance(value, bool):
            result.append((key,))
            continue
        result.append((key, value))
    return result
