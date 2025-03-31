from .docker import DockerConnection
from .local import LocalConnection
from .ssh import SSHConnection
from .common import get_connection


__all__ = [
    'DockerConnection',
    'LocalConnection',
    'SSHConnection',
    'get_connection'
]