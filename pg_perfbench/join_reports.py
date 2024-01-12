import os

from pg_perfbench.reports import (
    report as general_reports,
    schemas as report_schemas,
)
from pg_perfbench.context import Context


def join_reports(
    listReports: list[report_schemas.Report], compareFields: os.path
) -> report_schemas.Report | None:
    return
