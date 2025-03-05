from pg_perfbench.const import (ConnectionType, WorkMode,
                                DB_INFO_TEMPLATE_JSON_PATH, SYS_INFO_TEMPLATE_JSON_PATH, ALL_INFO_TEMPLATE_JSON_PATH)

class Context:
    def __init__(self, args, logger):
        self.structured_params = {
            'args': vars(args)
        }
        self.structured_params.update({
            'conn_type': args.connection_type
        })
        if args.connection_type == ConnectionType.SSH:
            self.structured_params.update({
                'conn_conf': {
                        'conn_params': {
                        'host': args.ssh_host,
                        'port': args.ssh_port,
                        'username': 'postgres',
                        'client_keys': args.ssh_key,
                        'known_hosts': None,
                        'env': {
                            'ARG_PG_BIN_PATH': f'{args.pg_bin_path}'
                        },
                        'connect_timeout': 5
                    },
                    'tunnel_params': {
                        'ssh_address_or_host': (args.ssh_host, int(args.ssh_port)),
                        'ssh_username': 'postgres',
                        'ssh_pkey': args.ssh_key,
                        'remote_bind_address': (
                            args.remote_pg_host,
                            int(args.remote_pg_port)
                        ),
                        'local_bind_address': (
                            args.pg_host,
                            int(args.pg_port)
                        ),
                    }
                }
            }
        )

        if args.connection_type == ConnectionType.DOCKER:
            self.structured_params.update({
                'conn_conf': {
                    'conn_params': {'container_name': args.container_name}
                }
            })

        self.structured_params.update({
            'db_conf' : {
                'host': args.pg_host,
                'port': args.pg_port,
                'user': args.pg_user,
                'password': args.pg_password,
                'database': args.pg_database
            }
        })

        self.structured_params.update({
            'workload_conf' : {
                'pg_data_path': args.pg_data_path,
                'pg_bin_path': args.pg_bin_path,
                'pgbench_path': args.pgbench_path,
                'psql_path': args.psql_path,
                'benchmark_type': args.benchmark_type,
                'workload_path': args.workload_path,
                'init_command': args.init_command,
                'workload_command': args.workload_command
            }
        })

        if args.pgbench_clients and args.pgbench_time:
            logger.error('Only one of two parameters can be set: '
                         '--pgbench-clients or --pgbench-time')
            raise

        if args.pgbench_clients is not None:
            self.structured_params['workload_conf'].update({'pgbench_iter_name': 'pgbench_clients'})
            self.structured_params['workload_conf'].update({'pgbench_iter_list': args.pgbench_clients})
        if args.pgbench_time is not None:
            self.structured_params['workload_conf'].update({'pgbench_iter_name': 'pgbench_time'})
            self.structured_params['workload_conf'].update({'pgbench_iter_list': args.pgbench_time})


        if args.pg_custom_config is not None:
            self.structured_params['workload_conf'].update(
                {'pg_custom_config': args.pg_custom_config}
            )

        self.structured_params.update({
            'report_conf': {
                'report_name': args.report_name
            }
        })

        self.structured_params.update({
                'log_conf': {
                    'collect_pg_logs': args.collect_pg_logs,
                    'clear_logs': args.clear_logs,
                    'log_level': args.log_level
            }
        })
        self.structured_params.update({
                'logger': logger
        })


class CollectInfoContext:
    def __init__(self, args, logger):
        report_template_path = {
            WorkMode.COLLECT_DB_INFO: DB_INFO_TEMPLATE_JSON_PATH,
            WorkMode.COLLECT_SYS_INFO: SYS_INFO_TEMPLATE_JSON_PATH,
            WorkMode.COLLECT_ALL_INFO: ALL_INFO_TEMPLATE_JSON_PATH
        }
        self.structured_params = {
            'args': vars(args)
        }
        self.structured_params.update({
            'conn_type': args.connection_type
        })
        if args.connection_type == ConnectionType.SSH:
            self.structured_params.update({
                'conn_conf': {
                    'conn_params': {
                        'host': args.ssh_host,
                        'port': args.ssh_port,
                        'username': 'postgres',
                        'client_keys': args.ssh_key,
                        'known_hosts': None,
                        'env': {
                            'ARG_PG_BIN_PATH': f'{args.pg_bin_path}'
                        },
                        'connect_timeout': 5
                    }
                }
            })
        if args.mode in {WorkMode.COLLECT_DB_INFO, WorkMode.COLLECT_ALL_INFO}:
            self.structured_params['conn_conf'].update({
                        'tunnel_params': {
                            'ssh_address_or_host': (args.ssh_host, int(args.ssh_port)),
                            'ssh_username': 'postgres',
                            'ssh_pkey': args.ssh_key,
                            'remote_bind_address': (
                                args.remote_pg_host,
                                int(args.remote_pg_port)
                            ),
                            'local_bind_address': (
                                args.pg_host,
                                int(args.pg_port)
                            ),
                    }
                })

        self.structured_params.update({
            'db_conf': {
                'db_conn_params': {
                     'host': args.pg_host,
                     'port': args.pg_port,
                     'user': args.pg_user,
                     'password': args.pg_password,
                     'database': args.pg_database
                },
                'db_env': {
                    'pg_data_path': args.pg_data_path,
                    'pg_bin_path': args.pg_bin_path,
                }
            }
        })

        if args.pg_custom_config is not None:
            self.structured_params['db_conf'].update({
                'db_env':
                    {
                        'pg_custom_config': args.pg_custom_config
                    }
            })

        self.structured_params.update({
            'report_conf': {
                'report_name': args.report_name,
                'report_template': report_template_path[args.mode]
            }
        })

        self.structured_params.update({
            'log_conf': {
                'collect_pg_logs': args.collect_pg_logs,
                'clear_logs': args.clear_logs,
                'log_level': args.log_level
            }
        })
        self.structured_params.update({
                'logger': logger
        })


class JoinContext:
    def __init__(self, args, logger):
        self.structured_params = {
            'join_tasks': args.join_tasks,
            'reference_report': args.reference_report,
            'input_dir': args.input_dir,
            'report_name': args.report_name,
            'logger': logger
        }
