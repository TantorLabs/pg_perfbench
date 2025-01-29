from datetime import datetime

from typing import Literal
from pydantic import BaseModel, Field, validator, Extra

from pg_perfbench.reports.schemas.common import SectionItemReports
from pg_perfbench.const import get_datetime_report


def _get_now_timestamp() -> str:
    return datetime.now().strftime('%d/%m/%Y %H:%M:%S')


class BenchmarkReport(BaseModel):
    header: str = Field(default='')
    report_name: str = Field(default='')
    description: str = Field(default_factory=_get_now_timestamp)
    sections: dict[str, SectionItemReports]

    # @validator('description', pre=True, always=True)
    # def set_default_description(cls, v):
    #     if not v:
    #         return get_datetime_report('%d/%m/%Y %H:%M:%S')
    #     return v

class SysInfoReport(BaseModel):
    header: str
    report_name: str = Field(default='')
    description: str = Field(default_factory=_get_now_timestamp)
    sections: dict[Literal['system'], SectionItemReports]

class DBInfoReport(BaseModel):
    header: str
    report_name: str = Field(default='')
    description: str = Field(default_factory=_get_now_timestamp)
    sections: dict[Literal['db'], SectionItemReports]

class AllInfoReport(BaseModel):
    header: str
    report_name: str = Field(default='')
    description: str = Field(default_factory=_get_now_timestamp)
    sections: dict[Literal['db', 'system'], SectionItemReports]