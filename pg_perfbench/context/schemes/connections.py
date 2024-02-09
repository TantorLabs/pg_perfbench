# ruff: noqa: ANN401
from pathlib import Path

from pydantic import BaseModel
from pydantic import Field


# TODO: those nodes require simplification
class LocalNodeParams(BaseModel):
    host: str = Field(alias='pg_host')
    port: int = Field(alias='pg_port')


class RemoteNodeParams(BaseModel):
    host: str = Field(default='127.0.0.1', alias='remote_pg_host')
    port: int = Field(default=5432, alias='remote_pg_port')


class DockerRemoteNodeParams(BaseModel):
    host: str = Field(default='127.0.0.1', alias='docker_pg_host')
    port: int = Field(default=5432, alias='docker_pg_port')


class TunnelParams(BaseModel):
    local: LocalNodeParams = Field(default_factory=LocalNodeParams)
    remote: RemoteNodeParams | DockerRemoteNodeParams


class WorkPaths(BaseModel):
    pg_data_path: str = Field(alias='pg_data_path')
    pg_bin_path: str = Field(alias='pg_bin_path')
    custom_config: str = Field(alias='custom_config', default='')


class SSHConnectionParams(BaseModel):
    host: str = Field('127.0.0.1', alias='ssh_host')
    port: int = Field(22, alias='ssh_port')
    user: str = Field('postgres', alias='ssh_user')
    key: str = Field(alias='ssh_key')
    tunnel: TunnelParams = Field(default_factory=TunnelParams)
    work_paths: WorkPaths


class DockerParams(BaseModel):
    image_name: str = Field(alias='image_name')
    container_name: str = Field('pg_perfbench', alias='container_name')
    tunnel: TunnelParams = Field(default_factory=TunnelParams)
    work_paths: WorkPaths


class UnixParams(BaseModel):
    path: Path = Field(alias='socket_path')


ConnectionParameters = SSHConnectionParams | DockerParams
