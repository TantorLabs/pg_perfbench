from pg_perfbench.const import ConnectionType
from pg_perfbench.connections.ssh import SSHConnection
from pg_perfbench.connections.docker import DockerConnection
from pg_perfbench.connections.local import LocalConnection


def get_connection(type):
    if type == ConnectionType.SSH:
        return SSHConnection
    if type == ConnectionType.DOCKER:
        return DockerConnection
    if type == ConnectionType.LOCAL:
        return LocalConnection