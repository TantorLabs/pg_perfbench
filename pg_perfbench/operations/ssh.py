import logging

import asyncssh
from asyncssh import SSHClientConnection

from pg_perfbench.context.schemas.workload import SourceDestinationPaths
from pg_perfbench.exceptions import exception_helper

log = logging.getLogger(__name__)


async def copy_by_paths(
    connection: SSHClientConnection,
    transition_paths: SourceDestinationPaths,
) -> None:
    # TODO: handle exceptions from the 'scp' docstring: OSError, asyncssh.SFTPError, ValueError
    try:
        await asyncssh.scp(transition_paths.source, (connection, transition_paths.destination))
    except Exception:
        log.error(exception_helper(show_traceback=True))
