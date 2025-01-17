# ruff: noqa: ANN401
from pathlib import Path
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import validator

from pg_perfbench.const import WorkloadTypes


class PgbenchOptions(BaseModel):
    pgbench_clients: list[int] = Field(default=[], alias='pgbench_clients')
    pgbench_jobs: list[int] = Field(default=[], alias='pgbench_jobs')
    pgbench_time: list[int] = Field(default=[], alias='pgbench_time')

    @validator('pgbench_clients', 'pgbench_jobs', 'pgbench_time', pre=True, each_item=True)
    def split_string_by_comma(cls, value):
        if isinstance(value, str):
            return [int(item.strip()) for item in value.split(',')]
        return value

    def get_dict(self):
        return {key: value for key, value in self.model_dump().items() if
                isinstance(value, list) and any(value)}


class SourceDestinationPaths(BaseModel):
    source: Path
    destination: Path


class WorkloadCommon(BaseModel):
    benchmark_type: str
    options: PgbenchOptions
    init_command: str
    workload_command: str
    pgbench_path: str = Field(alias='pgbench_path', default='pgbench')
    psql_path: str = Field(alias='psql_path', default='psql')


class WorkloadPaths(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    workload_path: Path = Field(alias='workload_path')

    def get_files_paths(self) -> 'WorkloadPaths':
        return WorkloadPaths(**self.model_dump(by_alias=True))


class WorkloadCustom(WorkloadPaths, WorkloadCommon):
    benchmark_type: Literal[WorkloadTypes.CUSTOM]
    # FIXME: re-use validator, or better use FilePath and find the way to test it

    @field_validator('workload_path')
    @classmethod
    def workload_not_empty(cls: type['WorkloadCustom'], v: Any) -> Any:
        if len(str(v)) <= 1:
            raise ValueError('Workload path should not be empty')
        return v


class WorkloadDefault(WorkloadCommon):
    benchmark_type: Literal[WorkloadTypes.DEFAULT]


WorkloadParameters = WorkloadCustom | WorkloadDefault
