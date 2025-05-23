import argparse
from argparse import Namespace
import sys
from typing import Optional

from pg_perfbench.const import (
    LogLevel,
    WorkloadTypes,
    WorkMode,
    ConnectionType,
)
from pg_perfbench.benchmark import BenchmarkRunner
from pg_perfbench.context import Context, CollectInfoContext, JoinContext
from pg_perfbench.log import setup_logger
from pg_perfbench.report.processing import save_report
from pg_perfbench.collect_info import InfoCollector
from pg_perfbench.join import ReportJoiner


def parse_pgbench_options(value):
    # parse comma-separated integers from user input
    if value:
        return list(map(int, value.split(',')))
    return None


def get_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='pg_perfbench CLI')

    parser.add_argument(
        '--clear-logs',
        action='store_true',
        default=False,
        help='Deleting old logs before running the tool',
    )
    parser.add_argument(
        '--log-level',
        type=str,
        choices=list(map(str, LogLevel)),
        default=str(LogLevel.INFO),
        help='Logging level',
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=list(map(str, WorkMode)),
        default=None,
        required=True,
        help='Select pg_perfbench mode',
    )
    parser.add_argument(
        '--report-name',
        type=str,
        default=None,
        help='Custom report name',
    )

    # group for workload and benchmark options
    workload_group = parser.add_argument_group(
        title='Workload options',
        description='Settings for benchmark profile or custom SQL scripts',
    )
    workload_group.add_argument(
        '--collect-pg-logs',
        action='store_true',
        default=False,
        help='Enable DB log collection (reads "SHOW log_directory;" from PostgreSQL)',
    )
    workload_group.add_argument(
        '--benchmark-type',
        type=str,
        choices=list(map(str, WorkloadTypes)),
        default=None,
        help='Benchmark type (default or custom)',
    )
    workload_group.add_argument(
        '--workload-path',
        type=str,
        default=None,
        help='Path to the workload directory with custom SQL scripts',
    )
    workload_group.add_argument(
        '--pgbench-clients',
        type=parse_pgbench_options,
        default=None,
        help='Comma-separated list of client counts for pgbench',
    )
    workload_group.add_argument(
        '--pgbench-time',
        type=parse_pgbench_options,
        default=None,
        help='Comma-separated list of test durations (in seconds) for pgbench',
    )
    workload_group.add_argument(
        '--init-command',
        type=str,
        default=None,
        help='Shell command for DB initialization before workload',
    )
    workload_group.add_argument(
        '--workload-command',
        type=str,
        default=None,
        help='Shell command for applying workload (e.g. pgbench)',
    )
    workload_group.add_argument(
        '--pgbench-path',
        type=str,
        default=None,
        help='Path to the pgbench binary (on the local or remote host)',
    )
    workload_group.add_argument(
        '--psql-path',
        type=str,
        default=None,
        help='Path to the psql binary (on the local or remote host)',
    )

    # database connection options
    db_group = parser.add_argument_group(title='Database connection options')
    db_group.add_argument(
        '--pg-custom-config',
        type=str,
        default=None,
        help='Path to the custom PostgreSQL config file to be used',
    )
    db_group.add_argument(
        '--pg-host',
        type=str,
        default=None,
        help='PostgreSQL host',
    )
    db_group.add_argument(
        '--pg-port',
        type=str,
        default=None,
        help='PostgreSQL port',
    )
    db_group.add_argument(
        '--pg-user',
        type=str,
        default='postgres',
        help='PostgreSQL user name',
    )
    db_group.add_argument(
        '--pg-password',
        type=str,
        default=None,
        help='PostgreSQL user password',
    )
    db_group.add_argument(
        '--pg-database',
        type=str,
        default=None,
        help='PostgreSQL database name',
    )
    db_group.add_argument(
        '--pg-data-path',
        type=str,
        default=None,
        help='PostgreSQL data directory path',
    )
    db_group.add_argument(
        '--pg-bin-path',
        type=str,
        default=None,
        help='PostgreSQL binaries path',
    )

    parser.add_argument(
        '--connection-type',
        type=str,
        choices=list(map(str, ConnectionType)),
        required=False,
        help='Connection type: "ssh", "docker", "local"',
    )

    # SSH-related options
    ssh_group = parser.add_argument_group('SSH connection options')
    ssh_group.add_argument(
        '--ssh-host',
        type=str,
        default=None,
        help='SSH server host',
    )
    ssh_group.add_argument(
        '--ssh-port',
        type=str,
        default=None,
        help='SSH server port',
    )
    ssh_group.add_argument(
        '--ssh-user',
        type=str,
        default=None,
        help='SSH user name',
    )
    ssh_group.add_argument(
        '--ssh-key',
        type=str,
        default=None,
        help='Path to SSH private key',
    )
    ssh_group.add_argument(
        '--remote-pg-host',
        type=str,
        default=None,
        help='PostgreSQL host on the remote side (for SSH tunneling)',
    )
    ssh_group.add_argument(
        '--remote-pg-port',
        type=str,
        default=None,
        help='PostgreSQL port on the remote side (for SSH tunneling)',
    )

    # Docker-related options
    docker_group = parser.add_argument_group('Docker connection options')
    docker_group.add_argument(
        '--docker-pg-host',
        type=str,
        default=None,
        help='PostgreSQL host inside Docker',
    )
    docker_group.add_argument(
        '--docker-pg-port',
        type=str,
        default=None,
        help='PostgreSQL port inside Docker',
    )
    docker_group.add_argument(
        '--container-name',
        type=str,
        default=None,
        help='Name of the container to be created or used',
    )

    # join mode options (comparing multiple reports)
    join_group = parser.add_argument_group(
        title='Join mode options',
        description='Options for joining or comparing multiple JSON reports',
    )
    join_group.add_argument(
        '--join-tasks',
        type=str,
        default=None,
        help='Path to JSON file with items to compare in the reports',
    )
    join_group.add_argument(
        '--reference-report',
        type=str,
        default=None,
        help='File name of the reference JSON report',
    )
    join_group.add_argument(
        '--input-dir',
        type=str,
        default=None,
        help='Directory containing the JSON reports to compare',
    )

    return parser


async def execute_pg_perfbench(args: Optional[Namespace] = None):
    # the main entry point to run the benchmark tool
    report = None
    logger = None

    if not args:
        try:
            args = get_args_parser().parse_args()
        except SystemExit:
            # parse arguments if not provided
            if any(arg in __import__('sys').argv for arg in ('--help', '-h')):
                return None
            else:
                print('Error parsing arguments. Exiting.')
                return None

    try:
        logger = setup_logger(args.log_level, args.clear_logs)
        logger.info('Logger configured successfully.')

        # check if user provided any valid mode
        if not args.mode:
            logger.error(
                'No mode specified. Please set --mode to a valid option.'
            )
            return None

        # run the appropriate mode
        if args.mode == WorkMode.BENCHMARK:
            # Creating a context for benchmark mode
            ctx = Context(args, logger)
            report = await BenchmarkRunner.run_benchmark_and_collect_metrics(
                **ctx.structured_params
            )

        elif args.mode in {
            WorkMode.COLLECT_SYS_INFO,
            WorkMode.COLLECT_DB_INFO,
            WorkMode.COLLECT_ALL_INFO,
        }:
            # Creating a context for collect info mode
            ctx = CollectInfoContext(args, logger)
            report = await InfoCollector.collect_info(**ctx.structured_params)

        elif args.mode in WorkMode.JOIN:
            # Creating a context for join mode
            ctx = JoinContext(args, logger)
            report = ReportJoiner.join_reports(**ctx.structured_params)

        else:
            logger.error(f'Unsupported mode: {args.mode}')
            return None

        # check if a report was generated
        if report is None:
            logger.error(
                'Emergency program termination. No report has been generated.'
            )
            return None

        # save the generated report (JSON/HTML)
        save_report(logger, report)
        logger.info('Benchmark report saved successfully.')

    except Exception as e:
        logger.error(f'Fatal error: {e}')
        sys.exit(1)
