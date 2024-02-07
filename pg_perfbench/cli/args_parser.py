import argparse

from pg_perfbench.const import WorkMode
from pg_perfbench.const import WorkloadTypes
from pg_perfbench.const import LogLevel


def parse_pgbench_options(value):
    if value:
        return list(map(int, value.split(',')))
    return None


def get_args_parser() -> argparse.ArgumentParser:
    general_group = argparse.ArgumentParser()

    ## Defining service parameters
    general_group.add_argument(
        '--clear-logs',
        action='store_true',
        help='Deleting old logs',
    )
    general_group.add_argument(
        '--log-level',
        type=str,
        choices=list(map(str, LogLevel)),
        default=str(LogLevel.INFO),
        help='Logging level',
    )
    general_group.add_argument(
        '--mode',
        type=str,
        choices=list(map(str, WorkMode)),
        help='pg_perfbench modes',
    )
    # Benchmark mode args
    ## Defining workload parameters
    workload_group = general_group.add_argument_group(
        title='Workload options',
        description='Workload profile settings: '
        'select benchmark profile or pass paths to custom SQL scripts',
    )
    workload_group.add_argument(
        '--collect-pg-logs',
        action='store_true',
        help='DB log collection mode',
    )
    workload_group.add_argument(
        '--benchmark-type',
        type=str,
        choices=list(map(str, WorkloadTypes)),
        help='Benchmark type',
    )
    workload_group.add_argument(
        '--workload-path',
        type=str,
        help='Path to the workload directory',
    )
    workload_group.add_argument(
        '--pgbench-clients',
        type=parse_pgbench_options,
        default=None,
        help='pgbench benchmarking arguments: --clients',
    )
    workload_group.add_argument(
        '--pgbench-jobs',
        type=parse_pgbench_options,
        default=None,
        help='pgbench benchmarking arguments: --jobs',
    )
    workload_group.add_argument(
        '--pgbench-time',
        type=parse_pgbench_options,
        default=None,
        help='pgbench benchmarking arguments: --time',
    )
    workload_group.add_argument(
        '--init-command',
        type=str,
        help='Database initialization command in the terminal',
    )
    workload_group.add_argument(
        '--workload-command',
        type=str,
        help='Database workload command in the terminal',
    )
    workload_group.add_argument(
        '--pgbench-path',
        type=str,
        help='Specify the pgbench path (relative to the current host)',
    )
    workload_group.add_argument(
        '--psql-path',
        type=str,
        help='Specify the psql path (relative to the current host)',
    )

    ## Defining database parameters
    db_group = general_group.add_argument_group(
        title='Database connection options'
    )
    db_group.add_argument(
        '--custom-config',
        type=str,
        default='',
        help='Specify the PostgreSQL host',
    )
    db_group.add_argument(
        '--pg-host',
        type=str,
        help='Specify the PostgreSQL host',
    )
    db_group.add_argument(
        '--pg-port',
        type=str,
        help='Specify the PostgreSQL port',
    )
    db_group.add_argument(
        '--pg-user',
        type=str,
        help='Specify the PostgreSQL user name',
    )
    db_group.add_argument(
        '--pg-user-password',
        type=str,
        help='Specify the PostgreSQL user password',
    )
    db_group.add_argument(
        '--pg-database',
        type=str,
        help='Specify the PostgreSQL database name',
    )
    db_group.add_argument(
        '--pg-data-path',
        type=str,
        help='Specify the PostgreSQL data directory',
    )
    db_group.add_argument(
        '--pg-bin-path',
        type=str,
        help='Specify the PostgreSQL binaries directory',
    )
    ## SSH connection arguments
    ssh_connection_group = general_group.add_argument_group(
        title='SSH connection options'
    )
    ssh_connection_group.add_argument(
        '--ssh-host',
        type=str,
        help='SSH connection host',
    )
    ssh_connection_group.add_argument(
        '--ssh-port',
        type=str,
        help='SSH connection port',
    )
    ssh_connection_group.add_argument(
        '--ssh-user',
        type=str,
        help='SSH connection user',
    )
    ssh_connection_group.add_argument(
        '--ssh-key',
        type=str,
        help='SSH connection key',
    )

    ssh_connection_group.add_argument(
        '--remote-pg-host',
        type=str,
    )
    ssh_connection_group.add_argument(
        '--remote-pg-port',
        type=str,
    )
    # Docker connection args
    docker_connection_group = general_group.add_argument_group(
        title='Docker container connection options'
    )
    docker_connection_group.add_argument(
        '--image-name',
        type=str,
        help='Run command: `docker images` and use `IMAGE ID` param from needed docker image',
    )
    docker_connection_group.add_argument(
        '--docker-pg-host',
        type=str,
    )
    docker_connection_group.add_argument(
        '--docker-pg-port',
        type=str,
    )
    docker_connection_group.add_argument(
        '--container-name',
        type=str,
        help='Which name of your image do you prefer?',
    )
    # Join mode args
    join_group = general_group.add_argument_group(
        title='Join mode options',
        description='Workload profile settings: '
        'select benchmark profile or pass paths to custom SQL scripts',
    )
    join_group.add_argument(
        '--join-task', type=str, help='Criteria for comparing reports'
    )
    join_group.add_argument(
        '--reference-report',
        type=str,
        default=None,
        help='Criteria for comparing reports',
    )
    join_group.add_argument('--input-dir', type=str, help='Reports directory')

    return general_group
