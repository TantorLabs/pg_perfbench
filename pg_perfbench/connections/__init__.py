import logging

from pg_perfbench.connections.common import Connectable
from pg_perfbench.connections.docker import DockerConnection
from pg_perfbench.connections.ssh import SSHConnection
from pg_perfbench.context.schemas.connections import ConnectionParameters
from pg_perfbench.context.schemas.connections import SSHConnectionParams
from pg_perfbench.context.schemas.connections import DockerParams


def get_connection(connection_params: ConnectionParameters) -> Connectable:
    if isinstance(connection_params, SSHConnectionParams):
        logging.info('Database connection type - SSH')
        return SSHConnection(connection_params)
    if isinstance(connection_params, DockerParams):
        logging.info('Database connection type - Docker')
        return DockerConnection(connection_params)
