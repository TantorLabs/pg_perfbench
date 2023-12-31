import logging
import subprocess
from typing import Any
import re

from pg_perfbench.context.schemas.context import RawArgs
from pg_perfbench.pgbench_utils import get_pgbench_options
from pg_perfbench.context import Context
from pg_perfbench.const import WorkloadTypes

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
    raw_args: RawArgs
    pgbench_options: list[str]
    benchmark_result_data: list[Any]
    ctx: Context
    def __init__(
        self,
        benchmark_result_data: list[Any],
        ctx: Context
    ) -> None:
        self.raw_args = ctx.raw_args
        self.benchmark_result_data = benchmark_result_data
        self.ctx = ctx
        self.pgbench_options = get_pgbench_options(ctx.db, ctx.workload)

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
                data = data + (subprocess.check_output(
                    ['cat', str(item)], shell=False
                ).decode('utf-8'))
        elif self.ctx.workload.benchmark_type is WorkloadTypes.DEFAULT:
            data = str(self.ctx.workload.init_command)
        return data

    def workload(self) -> str:
        data = '\n\n'
        if self.ctx.workload.benchmark_type is WorkloadTypes.CUSTOM:
            pgbench_command = str(self.ctx.workload.workload_command).replace(
                'ARG_WORKLOAD_PATH', str(self.ctx.workload.workload_path))
            pattern = re.compile(r'(?:(?:-f|--file=)\s*)?(\S+\.sql)')
            matches = pattern.findall(pgbench_command)
            matches = [match for match in matches if match]
            for item in matches:
                data = data + (subprocess.check_output(
                    ['cat', str(item)], shell=False
                ).decode('utf-8'))
        elif self.ctx.workload.benchmark_type is WorkloadTypes.DEFAULT:
            data = str(self.ctx.workload.workload_command)
        return data

    def benchmark_result(self) -> TableData:
        theader = [
            'clients',
            'number of transactions actually processed',
            'latency average',
            'initial connection time',
            'tps',
        ]
        data = self.benchmark_result_data
        return TableData(theader, data)

    def chart_tps_clients(self) -> dict[Any]:
        return {
            'name': f'Transactions per Second 1(tps)',
            # FIXME: set id of benchmark: timestamp or pid
            'data': [[val[0], round(val[4], 1)] for val in self.benchmark_result_data],
        }  # FIXME: create a model class for pgbench result
