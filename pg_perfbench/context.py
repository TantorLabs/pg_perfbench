from pg_perfbench.const import (
    ConnectionType,
    WorkMode,
    WorkloadTypes,
    DB_INFO_TEMPLATE_JSON_PATH,
    SYS_INFO_TEMPLATE_JSON_PATH,
    ALL_INFO_TEMPLATE_JSON_PATH,
)


def transform_key(key: str) -> str:
    return "--" + key.replace("_", "-")


class Context:
    def __init__(self, args, logger):
        try:
            self.filter_none(vars(args))
        except Exception as e:
            raise ValueError(f"Incorrect parameters specified:\n"
                             f"{str(e)}")

        self.structured_params = {"args": vars(args), "conn_type": args.connection_type}

        if args.pg_bin_path is None and args.mode == WorkMode.COLLECT_SYS_INFO:
            args.pg_bin_path = ""

        if args.connection_type == ConnectionType.SSH:
            self.structured_params.update({
                "conn_conf": {
                    "conn_params": {
                        "host": args.ssh_host,
                        "port": args.ssh_port,
                        "username": "postgres",
                        "client_keys": args.ssh_key,
                        "env": {
                            "ARG_PG_BIN_PATH": f"{args.pg_bin_path}"
                        },
                        "connect_timeout": 5
                    },
                    "tunnel_params": {
                        "ssh_address_or_host": (args.ssh_host, int(args.ssh_port)),
                        "ssh_username": "postgres",
                        "ssh_pkey": args.ssh_key,
                        "remote_bind_address": (
                            args.remote_pg_host,
                            int(args.remote_pg_port)
                        ),
                        "local_bind_address": (
                            args.pg_host,
                            int(args.pg_port)
                        )
                    }
                }
            })

        if args.connection_type == ConnectionType.DOCKER:
            self.structured_params.update({
                "conn_conf": {
                    "conn_params": {"container_name": args.container_name},
                    "env": {
                        "ARG_PG_BIN_PATH": args.pg_bin_path
                    }
                }
            })

        if args.connection_type == ConnectionType.LOCAL:
            self.structured_params.update({
                "conn_conf": {
                    "env": {
                        "ARG_PG_BIN_PATH": args.pg_bin_path
                    }
                }
            })

        self.structured_params.update({
            "db_conf": {
                "host": args.pg_host,
                "port": args.pg_port,
                "user": args.pg_user,
                "password": args.pg_password,
                "database": args.pg_database
            }
        })

        self.structured_params.update({
            "workload_conf": {
                "pg_data_path": args.pg_data_path,
                "pg_bin_path": args.pg_bin_path,
                "pgbench_path": args.pgbench_path,
                "psql_path": args.psql_path,
                "benchmark_type": args.benchmark_type,
                "workload_path": args.workload_path,
                "init_command": args.init_command,
                "workload_command": args.workload_command
            }
        })

        if args.pgbench_clients and args.pgbench_time:
            logger.error("Only one of two parameters can be set: --pgbench-clients or --pgbench-time")
            raise ValueError("Only one of two parameters can be set: --pgbench-clients or --pgbench-time")

        if args.pgbench_clients is not None:
            self.structured_params["workload_conf"].update({
                "pgbench_iter_name": "pgbench_clients",
                "pgbench_iter_list": args.pgbench_clients
            })
        if args.pgbench_time is not None:
            self.structured_params["workload_conf"].update({
                "pgbench_iter_name": "pgbench_time",
                "pgbench_iter_list": args.pgbench_time
            })

        if args.pg_custom_config is not None:
            self.structured_params["workload_conf"].update({
                "pg_custom_config": args.pg_custom_config
            })

        self.structured_params.update({
            "report_conf": {
                "report_name": args.report_name
            }
        })

        self.structured_params.update({
            "log_conf": {
                "collect_pg_logs": args.collect_pg_logs,
                "clear_logs": args.clear_logs,
                "log_level": args.log_level
            }
        })
        self.structured_params.update({
            "logger": logger
        })

    def filter_none(self, d: dict) -> dict:
        SSHConnectionArgs = [
            "ssh_host",
            "ssh_port",
            "ssh_key",
            "remote_pg_host",
            "remote_pg_port",
        ]
        DockerConnectionArgs = [
            "container_name",
        ]
        DBParamsArgs = [
            "pg_host",
            "pg_port",
            "pg_user",
            "pg_database",
            "pg_data_path",
            "pg_bin_path",
        ]
        WorkloadParamsArgs = [
            "init_command",
            "workload_command",
            "pgbench_path",
            "psql_path",
            "benchmark_type",
        ]

        if d.get("benchmark_type") == WorkloadTypes.CUSTOM:
            WorkloadParamsArgs.append("workload_path")

        ctype = d.get("connection_type")
        if ctype == ConnectionType.SSH:
            for key in SSHConnectionArgs:
                if d.get(key) is None:
                    raise ValueError(
                        f"Parameter \"{transform_key(key)}\" must be specified"
                        f" for connection type \"{ConnectionType.SSH}\""
                    )
        elif ctype == ConnectionType.DOCKER:
            for key in DockerConnectionArgs:
                if d.get(key) is None:
                    raise ValueError(
                        f"Parameter \"{transform_key(key)}\" must be specified for connection type \"{ConnectionType.DOCKER}\""
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
                    f"Parameter \"{transform_key(key)}\" must be specified for DB connection"
                )

        for key in WorkloadParamsArgs:
            if d.get(key) is None:
                raise ValueError(
                    f"Parameter \"{transform_key(key)}\" must be specified for workload configuration"
                )
        return d


class CollectInfoContext:
    def __init__(self, args, logger):
        try:
            self.filter_none(vars(args))
        except Exception as e:
            raise ValueError(f"Incorrect parameters specified:\n{str(e)}")

        report_template_path = {
            WorkMode.COLLECT_DB_INFO: DB_INFO_TEMPLATE_JSON_PATH,
            WorkMode.COLLECT_SYS_INFO: SYS_INFO_TEMPLATE_JSON_PATH,
            WorkMode.COLLECT_ALL_INFO: ALL_INFO_TEMPLATE_JSON_PATH
        }

        self.structured_params = {"args": vars(args), "conn_type": args.connection_type}

        if args.pg_bin_path is None and args.mode == WorkMode.COLLECT_SYS_INFO:
            args.pg_bin_path = ""

        if args.connection_type == ConnectionType.SSH:
            self.structured_params["conn_conf"] = {
                "conn_params": {
                    "host": args.ssh_host,
                    "port": args.ssh_port,
                    "username": "postgres",
                    "client_keys": args.ssh_key,
                    "known_hosts": None,
                    "env": {
                        "ARG_PG_BIN_PATH": f"{args.pg_bin_path}"
                    },
                    "connect_timeout": 5
                }
            }

            if args.mode in {WorkMode.COLLECT_DB_INFO, WorkMode.COLLECT_ALL_INFO}:
                self.structured_params["conn_conf"]["tunnel_params"] = {
                    "ssh_address_or_host": (args.ssh_host, int(args.ssh_port)),
                    "ssh_username": "postgres",
                    "ssh_pkey": args.ssh_key,
                    "remote_bind_address": (
                        args.remote_pg_host,
                        int(args.remote_pg_port)
                    ),
                    "local_bind_address": (
                        args.pg_host,
                        int(args.pg_port)
                    )
                }

        elif args.connection_type == ConnectionType.DOCKER:
            self.structured_params["conn_conf"] = {
                "conn_params": {
                    "container_name": args.container_name
                },
                "env": {
                    "ARG_PG_BIN_PATH": args.pg_bin_path
                }
            }

        elif args.connection_type == ConnectionType.LOCAL:
            self.structured_params["conn_conf"] = {
                "env": {
                    "ARG_PG_BIN_PATH": args.pg_bin_path
                }
            }

        self.structured_params["db_conf"] = {
            "db_conn_params": {
                "host": args.pg_host,
                "port": args.pg_port,
                "user": args.pg_user,
                "password": args.pg_password,
                "database": args.pg_database
            },
            "db_env": {
                "pg_data_path": args.pg_data_path,
                "pg_bin_path": args.pg_bin_path
            }
        }

        if args.pg_custom_config is not None:
            self.structured_params["db_conf"]["db_env"]["pg_custom_config"] = args.pg_custom_config

        self.structured_params["report_conf"] = {
            "report_name": args.report_name,
            "report_template": report_template_path[args.mode]
        }

        self.structured_params["log_conf"] = {
            "collect_pg_logs": args.collect_pg_logs,
            "clear_logs": args.clear_logs,
            "log_level": args.log_level
        }
        self.structured_params["logger"] = logger

    def filter_none(self, d: dict) -> dict:
        SSHConnectionArgs = [
            "ssh_host",
            "ssh_port",
            "ssh_key"
        ]
        DockerConnectionArgs = [
            "container_name",
        ]
        DBParamsArgs = [
            "pg_host",
            "pg_port",
            "pg_user",
            "pg_database",
            "pg_data_path",
            "pg_bin_path",
        ]
        mode = d.get("mode")
        if mode in {WorkMode.COLLECT_DB_INFO, WorkMode.COLLECT_ALL_INFO}:
            for key in DBParamsArgs:
                if d.get(key) == None:
                    raise ValueError(
                        f"Parameter \"{transform_key(key)}\" must be specified "
                        f"for DB connection"
                    )
            SSHConnectionArgs.append("remote_pg_host")
            SSHConnectionArgs.append("remote_pg_port")

        ctype = d.get("connection_type")
        if ctype == ConnectionType.SSH:
            for key in SSHConnectionArgs:
                if d.get(key) is None:
                    raise ValueError(
                        f"Parameter \"{transform_key(key)}\" must be specified "
                        f"for connection type \"{ConnectionType.SSH}\""
                    )
        elif ctype == ConnectionType.DOCKER:
            for key in DockerConnectionArgs:
                if d.get(key) is None:
                    raise ValueError(
                        f"Parameter \"{transform_key(key)}\" must be specified "
                        f"for connection type \"{ConnectionType.DOCKER}\""
                    )
        elif ctype == ConnectionType.LOCAL:
            pass
        else:
            raise ValueError(
                f"You must specify the connection type parameter \"{transform_key('connection_type')}\""
            )

        return d


class JoinContext:
    def __init__(self, args, logger):
        self.structured_params = {
            "args": vars(args),
            "join_tasks": args.join_tasks,
            "reference_report": args.reference_report,
            "input_dir": args.input_dir,
            "report_name": args.report_name,
            "logger": logger
        }
