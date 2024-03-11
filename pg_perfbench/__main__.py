import asyncio
import logging
from argparse import Namespace
from typing import Optional

from pg_perfbench.benchmark_running import run_benchmark
from pg_perfbench.cli.args_parser import get_args_parser
from pg_perfbench.const import WorkMode
from pg_perfbench.context import Context, JoinContext
from pg_perfbench.logs import clear_logs, setup_logger
from pg_perfbench.reports import report as general_reports
from pg_perfbench.join_reports import join_reports


log = logging.getLogger(__name__)   #FIXME: log->logger


async def run(args: Optional[Namespace] = None):
    report = None

    if not args:
        args = get_args_parser().parse_args()

    if args.clear_logs:
        print('Clearing logs folder')
        clear_logs()

    log_level = setup_logger(args.log_level)

    if args.mode == WorkMode.BENCHMARK:
        context = Context.from_args_map(vars(args))
        report = await run_benchmark(context, log_level)
    elif args.mode == WorkMode.JOIN:
        context = JoinContext.from_args_map(vars(args))
        report = join_reports(context, log_level)

    if report is None:
        log.error('Emergency program termination. No report has been generated.')
        return None

    general_reports.save_report(report, args.mode)
    log.info('Benchmark report saved successfully.')


if __name__ == '__main__':
    asyncio.run(run())
