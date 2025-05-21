# PostgreSQL Performance Bench
## Testing a PostgreSQL database instance located on a local host

#### General environment preparation 
Review and follow the steps outlined in the README [preparation](../README.md#dependencies-and-installation).

#### Environment preparation for Local connection
Review and follow the steps outlined in the README [general instructions](../README.md#general-instructions-for-all-connection-types)
 and [local connection](../README.md#local-connection) description.

When using a local connection, the application must be configured in the `postgres` user's environment:
```commandline
su - postgres 
git clone https://github.com/TantorLabs/pg_perfbench.git
cd pg_perfbench
python3.10 -m venv venv
source venv/bin/activate
```

#### Application configuration for local access to the database

- `pg_perfbench`  is executed as a module:
```
python -m pg_perfbench <args>
```

- Application operating mode {benchmark, join}:
```
--mode=benchmark
```

- Configure local connection usage parameters:
```
--connection-type=local
```
> **Note**: `--pg-port, --pg-host` - Parameters for establishing a local connection to the database.   
>  The specified address for `--pg-port, --pg-host` must be accessible by `pg_perfbench`.



- Logging level for output of application execution stages [`info`,`debug`,`error`]:
```
--log-level=debug
```
- Database instance parameters:
```
--pg-user=postgres
--pg-database=tdb
--pg-data-path=/var/lib/postgresql/16/main
--pg-bin-path=/usr/lib/postgresql/16/bin
```

- pgbench workload environment parameters:
```
--benchmark-type=default
--psql-path=/usr/bin/psql
--pgbench-path=/usr/bin/pgbench
--init-command="ARG_PGBENCH_PATH -i --scale=10 --foreign-keys -p ARG_PG_PORT -h ARG_PG_HOST -U postgres ARG_PG_DATABASE"        \
--workload-command="ARG_PGBENCH_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U ARG_PG_USER ARG_PG_DATABASE -c ARG_PGBENCH_CLIENTS -j 10 -T 10 --no-vacuum"
```
- You can also specify arguments used as placeholders in command strings `--init-command`,  `--workload-command`(see more [workload description](workload_description.md#how-to-configure-workload)):
  - `--pg-host` will be resolved as `ARG_PG_HOST`.
  - `--pgbench-clients` will be resolved as `ARG_PGBENCH_CLIENTS`.

- Final set of arguments for database workload over an SSH connection on a remote host:
```
python -m pg_perfbench --mode=benchmark     \
--log-level=info       \
--collect-pg-logs   \
--connection-type=local     \
--pg-host=127.0.0.1     \
--pg-port=5432      \
--pg-user=postgres      \
--pg-password=pswd      \
--pg-database=tdb       \
--pg-custom-config=/tmp/primary_1.conf      \
--pg-data-path=/var/lib/postgresql/16/main      \
--pg-bin-path=/usr/lib/postgresql/16/bin        \
--benchmark-type=default        \
--pgbench-clients=5,7       \
--pgbench-path=/usr/bin/pgbench     \
--psql-path=/usr/bin/psql       \
--init-command="ARG_PGBENCH_PATH -i --scale=10 --foreign-keys -p ARG_PG_PORT -h ARG_PG_HOST -U postgres ARG_PG_DATABASE"        \
--workload-command="ARG_PGBENCH_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U ARG_PG_USER ARG_PG_DATABASE -c ARG_PGBENCH_CLIENTS -j 10 -T 10 --no-vacuum"
```
Initial application log output with correct configuration:
```
2025-03-18 23:59:48,116       INFO                                root :   55 - Logging level: debug
2025-03-18 23:59:48,116       INFO                                root :  283 - Logger configured successfully.
2025-03-18 23:59:48,116       INFO                                root :   19 - Incoming parameters:
#   clear_logs = False
#   log_level = debug
#   mode = benchmark
#   collect_pg_logs = True
#   benchmark_type = default
#   pgbench_clients = [5, 7]
#   init_command = ARG_PGBENCH_PATH -i --scale=10 --foreign-keys -p ARG_PG_PORT -h ARG_PG_HOST -U postgres ARG_PG_DATABASE
#   workload_command = ARG_PGBENCH_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U ARG_PG_USER ARG_PG_DATABASE -c ARG_PGBENCH_CLIENTS -j 10 -T 10 --no-vacuum
#   pgbench_path = /usr/bin/pgbench
#   psql_path = /usr/bin/psql
#   pg_custom_config = /tmp/primary_1.conf
#   pg_host = 127.0.0.1
#   pg_port = 5432
#   pg_user = postgres
#   pg_password = pswd
#   pg_database = tdb
#   pg_data_path = /var/lib/postgresql/16/main
#   pg_bin_path = /usr/lib/postgresql/16/bin
#   connection_type = local
#-----------------------------------
2025-03-18 23:59:48,116       INFO                                root :  201 - Report template loaded successfully.
2025-03-18 23:59:48,116       INFO                                root :  208 - Load iterations configured successfully. Total iterations: 2
2025-03-18 23:59:48,116       INFO                                root :  215 - Connection type selected: local
2025-03-18 23:59:48,116       INFO                                root :  300 - LocalConnection started (no persistent process).
2025-03-18 23:59:48,116       INFO                                root :  221 - Connection established successfully.
2025-03-18 23:59:48,116       INFO                                root :  226 - Custom DB config selected: /tmp/primary_1.conf
2025-03-18 23:59:48,117       INFO                                root :  228 - User's DB config set successfully: /tmp/primary_1.conf ---> /var/lib/postgresql/16/main/postgresql.conf
2025-03-18 23:59:48,117       INFO                                root :  232 - Start load testing.
2025-03-18 23:59:48,117       INFO                                root :  234 - Resetting the database.
2025-03-18 23:59:49,128      DEBUG                                root :   50 - Terminating other sessions to the test DB.
2025-03-18 23:59:49,132      DEBUG                                root :   52 - Dropping test DB.
2025-03-18 23:59:50,288      DEBUG                                root :   29 - Creating pristine test DB.
2025-03-18 23:59:50,329      DEBUG                                root :   68 - Database is available.
2025-03-18 23:59:50,329       INFO                                root :  236 - Database reset successfully.
2025-03-18 23:59:50,329       INFO                                root :  237 - Starting load iteration 1...

```
