from typing import Dict, Any, Optional
from pg_perfbench.const import ConnectionType


def transform_key(key: str) -> str:
    return "--" + key.replace("_", "-")


class BaseContext:
    """Base class for all context classes with common functionality"""

    def __init__(self, args, logger):
        self.structured_params = {"args": vars(args), "logger": logger}

    def filter_none(self, d: dict) -> dict:
        """Base method to be overridden by child classes"""
        return d

    def _add_connection_config(self, args):
        """Add connection configuration based on connection type"""
        conn_type = args.connection_type
        self.structured_params["conn_type"] = conn_type

        if conn_type == ConnectionType.SSH:
            self._add_ssh_connection_config(args)
        elif conn_type == ConnectionType.DOCKER:
            self._add_docker_connection_config(args)
        elif conn_type == ConnectionType.LOCAL:
            self._add_local_connection_config(args)
        else:
            raise ValueError(
                f"You must specify the connection type parameter \"{transform_key('connection_type')}\""
            )

    def _add_ssh_connection_config(self, args):
        """Add SSH connection configuration"""
        conn_params = {
            "host": args.ssh_host,
            "port": args.ssh_port,
            "username": "postgres",
            "client_keys": args.ssh_key,
            "known_hosts": None,
            "env": {
                "ARG_PG_BIN_PATH": f"{args.pg_bin_path}"
            },
            "connect_timeout": 5
        }

        self.structured_params["conn_conf"] = {"conn_params": conn_params}

    def _add_docker_connection_config(self, args):
        """Add Docker connection configuration"""
        self.structured_params["conn_conf"] = {
            "conn_params": {"container_name": args.container_name},
            "env": {
                "ARG_PG_BIN_PATH": args.pg_bin_path
            }
        }

    def _add_local_connection_config(self, args):
        """Add Local connection configuration"""
        self.structured_params["conn_conf"] = {
            "env": {
                "ARG_PG_BIN_PATH": args.pg_bin_path
            }
        }
