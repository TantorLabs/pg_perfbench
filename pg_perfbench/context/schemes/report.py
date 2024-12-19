from pydantic import BaseModel
from pydantic import Field

from pg_perfbench.const import DEFAULT_REPORT_NAME

class ReportParameters(BaseModel):
    report_name: str = Field(default='', alias='report_name')
    chart_time_series_name: str = Field(default=DEFAULT_REPORT_NAME, alias='report_name')
    chart_time_series_xaxis: str = Field('clients')
    chart_time_series_array: list = Field([])
