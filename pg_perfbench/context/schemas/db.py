# ruff: noqa: ANN401
from pydantic import BaseModel
from pydantic import Field


class DBParameters(BaseModel):
    pg_host: str = Field(alias='pg_host', default='127.0.0.1')
    pg_port: str = Field(alias='pg_port', default='5432')
    pg_database: str = Field(alias='pg_database', default='postgres')
    pg_user: str = Field(alias='pg_user')
    pg_password: str = Field(alias='pg_user_password')
    pg_data_directory_path: str = Field(alias='pg_data_path')
    pg_bin_path: str = Field(alias='pg_bin_path')
    collect_pg_logs: bool = Field(alias='collect_pg_logs', default=False)
    custom_config: str = Field(alias='custom_config', default='')
