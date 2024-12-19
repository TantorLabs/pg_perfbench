import logging
import subprocess
from typing import Any, Literal
import re

from pg_perfbench.pgbench_utils import get_pgbench_options
from pg_perfbench.context import Context
from pg_perfbench.const import WorkloadTypes, LOCAL_DB_LOGS_PATH, DEFAULT_LOG_ARCHIVE_NAME
from pg_perfbench.reports.schemas.common import ItemLink, StateTypes, ReportTypes

log = logging.getLogger(__name__)


def _execute_command(command: list[str]) -> str:
    # TODO: untrusted input may be checked here. Should we do it?
    return subprocess.check_output(command, shell=False).decode('utf-8').strip()  # noqa S603


class TableData:
    theader: list[str]
    data: list[list[str | float]]

    def __init__(self, theader: list[str], data: list[list[str | float]]):
        self.theader = theader
        self.data = data


class JsonMethods:    # FIXME: this class needs a lot of fixes.....
    raw_args: dict[Any]
    pgbench_options: list[str]
    benchmark_result_data: list[Any]
    ctx: Context

    def __init__(self, benchmark_result_data: list[Any], ctx: Context) -> None:
        self.raw_args = {name: value for name, value in ctx.raw_args.items() if value is not None}
        self.benchmark_result_data = benchmark_result_data
        self.ctx = ctx
        self.pgbench_options = get_pgbench_options(ctx.workload)

    def pgbench_options_table(self) -> TableData:
        theader = ['iteration number', 'pgbench_options']
        data = [[self.pgbench_options.index(val), str(val)] for val in self.pgbench_options]
        return TableData(theader, data)

    def args(self) -> TableData:
        theader = ['arg', 'value']
        data = [[key, str(value)] for key, value in self.raw_args.items()]
        return TableData(theader, data)

    def workload_tables(self) -> str:
        data = ''
        if self.ctx.workload.benchmark_type is WorkloadTypes.CUSTOM:
            init_command = str(self.ctx.workload.init_command)
            init_command = init_command.replace(
                'ARG_WORKLOAD_PATH', str(self.ctx.workload.workload_path))
            pattern = re.compile(r'(?:(?:-f|--file=)\s*)?(\S+\.sql)')
            matches = pattern.findall(init_command)
            matches = [match for match in matches if match]
            for item in matches:
                data = data + f'{str(item)} :\n' + (subprocess.check_output(
                    ['cat', f'{str(item)}'], shell=False
                ).decode('utf-8')) + '\n\n'
        elif self.ctx.workload.benchmark_type is WorkloadTypes.DEFAULT:
            data = str(self.ctx.workload.init_command)
        return data

    def workload(self) -> str:
        data = ''
        if self.ctx.workload.benchmark_type is WorkloadTypes.CUSTOM:
            pgbench_command = str(self.ctx.workload.workload_command).replace(
                'ARG_WORKLOAD_PATH', str(self.ctx.workload.workload_path))
            pattern = re.compile(r'(?:(?:-f|--file=)\s*)?(\S+\.sql)')
            matches = pattern.findall(pgbench_command)
            matches = [match for match in matches if match]
            for item in matches:
                data = data + f'{str(item)} :\n' + (subprocess.check_output(
                    ['cat', f'{str(item)}'], shell=False
                ).decode('utf-8')) + '\n\n'
        elif self.ctx.workload.benchmark_type is WorkloadTypes.DEFAULT:
            data = str(self.ctx.workload.workload_command)
        return data

    def benchmark_result(self) -> TableData:
        theader = [
            'clients',
            'duration',
            'number of transactions actually processed',
            'latency average',
            'initial connection time',
            'tps',
        ]
        data = self.benchmark_result_data
        return TableData(theader, data)

    def chart_tps_clients(self) -> dict[Any]:
        return {
            'title': {
                'text': f'tps({self.ctx.report.chart_time_series_xaxis})'
            },
            'xaxis': {
                'title': {
                    'text': self.ctx.report.chart_time_series_xaxis
                }
            },
            'series': [
                {
                    'name': f'{self.ctx.report.chart_time_series_name},tps',
                    'data': [
                        [x, round(val[5], 1)]
                        for x, val in zip(self.ctx.report.chart_time_series_array, self.benchmark_result_data)
                    ],
                }
            ]
        }  # FIXME: create a model class for pgbench result


async def collect_logs(connect, remote_logs_path, report_name: str = DEFAULT_LOG_ARCHIVE_NAME) -> ItemLink | None:
    if data := await connect.copy_db_log_files(remote_logs_path, LOCAL_DB_LOGS_PATH, report_name):
        report_item = ItemLink(
            header='database logs',
            description='Local path to the database log archive',
            item_type=ReportTypes.LINK.value,
            state=StateTypes.COLLAPSED.value,
            python_command='collect_logs',
            data=data
        )
        return report_item
    else:
        log.error('Error collecting log files')
        return None
