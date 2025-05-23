from pg_perfbench.const import ConnectionType, WorkMode, WorkloadTypes
from .base_context import BaseContext, transform_key


class Context(BaseContext):
    def __init__(self, args, logger):
        super().__init__(args, logger)

        try:
            self.filter_none(vars(args))
        except Exception as e:
            raise ValueError(f'Incorrect parameters specified:\n{str(e)}')

        if args.pg_bin_path is None and args.mode == WorkMode.COLLECT_SYS_INFO:
            args.pg_bin_path = ''

        # Add connection configuration
        self._add_connection_config(args)

        # Add SSH tunnel params if needed
        if args.connection_type == ConnectionType.SSH:
            self.structured_params['conn_conf']['tunnel_params'] = {
                'ssh_address_or_host': (args.ssh_host, int(args.ssh_port)),
                'ssh_username': 'postgres',
                'ssh_pkey': args.ssh_key,
                'remote_bind_address': (
                    args.remote_pg_host,
                    int(args.remote_pg_port),
                ),
                'local_bind_address': (args.pg_host, int(args.pg_port)),
            }

        # Add database configuration
        self.structured_params['db_conf'] = {
            'host': args.pg_host,
            'port': args.pg_port,
            'user': args.pg_user,
            'password': args.pg_password,
            'database': args.pg_database,
        }

        # Add workload configuration
        self.structured_params['workload_conf'] = {
            'pg_data_path': args.pg_data_path,
            'pg_bin_path': args.pg_bin_path,
            'pgbench_path': args.pgbench_path,
            'psql_path': args.psql_path,
            'benchmark_type': args.benchmark_type,
            'workload_path': args.workload_path,
            'init_command': args.init_command,
            'workload_command': args.workload_command,
        }

        # Handle pgbench parameters
        if args.pgbench_clients and args.pgbench_time:
            logger.error(
                'Only one of two parameters can be set: --pgbench-clients or --pgbench-time'
            )
            raise ValueError(
                'Only one of two parameters can be set: --pgbench-clients or --pgbench-time'
            )

        if args.pgbench_clients is not None:
            self.structured_params['workload_conf'].update(
                {
                    'pgbench_iter_name': 'pgbench_clients',
                    'pgbench_iter_list': args.pgbench_clients,
                }
            )
        if args.pgbench_time is not None:
            self.structured_params['workload_conf'].update(
                {
                    'pgbench_iter_name': 'pgbench_time',
                    'pgbench_iter_list': args.pgbench_time,
                }
            )

        # Add custom config if present
        if args.pg_custom_config is not None:
            self.structured_params['workload_conf'][
                'pg_custom_config'
            ] = args.pg_custom_config

        # Add report configuration
        self.structured_params['report_conf'] = {
            'report_name': args.report_name
        }

        # Add log configuration
        self.structured_params['log_conf'] = {
            'collect_pg_logs': args.collect_pg_logs,
            'clear_logs': args.clear_logs,
            'log_level': args.log_level,
        }

    def filter_none(self, d: dict) -> dict:
        SSHConnectionArgs = [
            'ssh_host',
            'ssh_port',
            'ssh_key',
            'remote_pg_host',
            'remote_pg_port',
        ]
        DockerConnectionArgs = [
            'container_name',
        ]
        DBParamsArgs = [
            'pg_host',
            'pg_port',
            'pg_user',
            'pg_database',
            'pg_data_path',
            'pg_bin_path',
        ]
        WorkloadParamsArgs = [
            'init_command',
            'workload_command',
            'pgbench_path',
            'psql_path',
            'benchmark_type',
        ]

        if d.get('benchmark_type') == WorkloadTypes.CUSTOM:
            WorkloadParamsArgs.append('workload_path')

        ctype = d.get('connection_type')
        if ctype == ConnectionType.SSH:
            for key in SSHConnectionArgs:
                if d.get(key) is None:
                    raise ValueError(
                        f'Parameter "{transform_key(key)}" must be specified'
                        f' for connection type "{ConnectionType.SSH}"'
                    )
        elif ctype == ConnectionType.DOCKER:
            for key in DockerConnectionArgs:
                if d.get(key) is None:
                    raise ValueError(
                        f'Parameter "{transform_key(key)}" must be specified for connection type "{ConnectionType.DOCKER}"'
                    )
        elif ctype == ConnectionType.LOCAL:
            pass
        else:
            raise ValueError(
                f"You must specify the connection type parameter \"{transform_key('connection_type')}\""
            )

        for key in DBParamsArgs:
            if d.get(key) is None:
                raise ValueError(
                    f'Parameter "{transform_key(key)}" must be specified for DB connection'
                )

        for key in WorkloadParamsArgs:
            if d.get(key) is None:
                raise ValueError(
                    f'Parameter "{transform_key(key)}" must be specified for workload configuration'
                )
        return d
