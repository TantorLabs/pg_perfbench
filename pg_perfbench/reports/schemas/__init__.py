from datetime import datetime

from pydantic import BaseModel, Field, validator

from pg_perfbench.reports.schemas.common import SectionItemReports


def _get_now_timestamp() -> str:
    return datetime.now().strftime('%d/%m/%Y %H:%M:%S')


class Report(BaseModel):
    header: str
    description: str = Field(default_factory=_get_now_timestamp)
    sections: dict[str, SectionItemReports]

    @validator('description', pre=True, always=True)
    def set_default_description(cls, v):
        if not v:
            return datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        return v
