# PostgreSQL Performance Bench
## Testing a PostgreSQL database instance located on a remote host

#### General environment preparation 

Review and follow the steps outlined in the README [Prerequisites](../README.md#prerequisites).

#### Simple test configuration of a PostgreSQL database instance located on a remote host 
- `pg_perfbench`  is executed as a module:
```
python -m pg_perfbench <args>
```

- Application operating mode {benchmark, join}:
```
--mode=benchmark
```

- Configure SSH connection usage parameters:
```
--ssh-port=22 
--ssh-key=/path_to/private_key
--ssh-host=10.100.100.100
--remote-pg-host=127.0.0.1 
--remote-pg-port=5432 
--pg-host=127.0.0.1 
--pg-port=5438 
```
> **Note**: `--pg-port, --pg-host` - Parameters of the local address used for forwarding to the listening address of the database instance on a remote host (via SSH tunnel), specified by `--remote-pg-port, --remote-pg-host`. The specified address for `--pg-port, --pg-host` must be accessible by `pg_perfbench`.



- Logging level for output of application execution stages {info,debug,error}:
```
--log-level=debug
```
- Database instance parameters:
```
--pg-user=postgres
--pg-user-password=pswd
--pg-database=tdb
--pg-data-path=/var/lib/postgresql/data
--pg-bin-path=/usr/lib/postgresql/16/bin
```

- pgbench workload environment parameters:
```
--benchmark-type=default
--psql-path=/usr/bin/psql
--pgbench-path=/usr/bin/pgbench
--init-command="ARG_PGBENCH_PATH -i --scale=100 --foreign-keys -p ARG_PG_PORT -h ARG_PG_HOST -U postgres ARG_PG_DATABASE" 
--workload-command="ARG_PGBENCH_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U ARG_PG_USER ARG_PG_DATABASE -c ARG_PGBENCH_CLIENTS -j ARG_PGBENCH_JOBS -T ARG_PGBENCH_TIME --no-vacuum"
```
- You can also specify arguments used as placeholders in command strings `--init-command`,  `--workload-command`:
```
--pgbench-clients=5,7
--pgbench-time=10
--pgbench-jobs=2
```

- Final set of arguments for database workload over an SSH connection on a remote host:
```
python -m pg_perfbench --mode=benchmark  \
--collect-pg-logs  \
--log-level=debug  \
--ssh-port=22  \
--ssh-key=/path_to/private_key \
--ssh-host=10.100.100.100  \
--remote-pg-host=127.0.0.1  \
--remote-pg-port=5432  \
--pg-host=127.0.0.1  \
--pg-port=5438  \
--pg-user=postgres  \
--pg-user-password=pswd  \
--pg-database=tdb  \
--pg-data-path=/var/lib/postgresql/tantor-se-16/data  \
--pg-bin-path=/opt/tantor/db/16/bin  \
--pgbench-path=/usr/bin/pgbench \
--psql-path=/usr/bin/psql  \
--pgbench-clients=5,7 \
--pgbench-time=10  \
--pgbench-jobs=2 \
--init-command="ARG_PGBENCH_PATH -i --scale=100 --foreign-keys -p ARG_PG_PORT -h ARG_PG_HOST -U postgres ARG_PG_DATABASE"  \
--workload-command="ARG_PGBENCH_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U ARG_PG_USER ARG_PG_DATABASE -c ARG_PGBENCH_CLIENTS -j ARG_PGBENCH_JOBS -T ARG_PGBENCH_TIME --no-vacuum"
```
Initial application log output with correct configuration:
```
2024-11-27 21:28:09,433       INFO                                root :   37 - Logging level: debug
2024-11-27 21:28:09,433       INFO      pg_perfbench.benchmark_running :   26 - Version - 0.0.1
2024-11-27 21:28:09,434       INFO      pg_perfbench.benchmark_running :   27 - Started MainRoutine.run
2024-11-27 21:28:09,434       INFO      pg_perfbench.benchmark_running :   35 - Incoming parameters:
#   clear_logs = False
#   log_level = debug
#   mode = benchmark
#   collect_pg_logs = True
#   benchmark_type = default
#   pgbench_clients = [5, 7]
#   pgbench_jobs = [2]
#   pgbench_time = [10]
#   init_command = ARG_PGBENCH_PATH -i --scale=100 --foreign-keys -p ARG_PG_PORT -h ARG_PG_HOST -U postgres ARG_PG_DATABASE
#   workload_command = ARG_PGBENCH_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U ARG_PG_USER ARG_PG_DATABASE -c ARG_PGBENCH_CLIENTS -j ARG_PGBENCH_JOBS -T ARG_PGBENCH_TIME --no-vacuum
#   pgbench_path = /usr/bin/pgbench
#   psql_path = /usr/bin/psql
#   custom_config = 
#   pg_host = 127.0.0.1
#   pg_port = 5438
#   pg_user = postgres
#   pg_user_password = ****
#   pg_database = tdb
#   pg_data_path = /var/lib/postgresql/tantor-se-16/data
#   pg_bin_path = /opt/tantor/db/16/bin
#   ssh_host = 10.100.100.100
#   ssh_port = 22
#   ssh_key = *********************************************************************************
#   remote_pg_host = 127.0.0.1
#   remote_pg_port = 5432
#-----------------------------------
2024-11-27 21:28:09,434       INFO                                root :   15 - Database connection type - SSH
2024-11-27 21:28:09,434       INFO                                root :   77 - Template report_struct.json is configured correctly
2024-11-27 21:28:09,434       INFO        pg_perfbench.connections.ssh :   42 - Attempting to establish an SSH connection: 
2024-11-27 21:28:10,440       INFO        pg_perfbench.connections.ssh :   76 - SSH connection established.
2024-11-27 21:28:10,440       INFO      pg_perfbench.benchmark_running :   64 - Start benchmarking
2024-11-27 21:28:10,441       INFO      pg_perfbench.benchmark_running :   68 - Current benchmark iteration: /usr/bin/pgbench -p 5438 -h 127.0.0.1 -U postgres tdb -c 5 -j 2 -T 10 --no-vacuum
2024-11-27 21:28:10,441      DEBUG      pg_perfbench.benchmark_running :   44 - Benchmark preparation
2024-11-27 21:28:10,692       INFO        pg_perfbench.connections.ssh :   94 - 
2024-11-27 21:28:10,750       INFO        pg_perfbench.connections.ssh :   94 - 
2024-11-27 21:28:10,799       INFO        pg_perfbench.connections.ssh :   94 - sudo: a terminal is required to read the password; either use the -S option to read from standard input or configure an askpass helper
sudo: a password is required

Database is available.
2024-11-27 21:28:11,979       INFO          pg_perfbench.operations.db :   46 - Terminating other sessions to the test DB
2024-11-27 21:28:11,998       INFO          pg_perfbench.operations.db :   48 - Dropping test DB
2024-11-27 21:28:12,040       INFO          pg_perfbench.operations.db :   50 - Creating pristine test DB
2024-11-27 21:28:12,165       INFO      pg_perfbench.benchmark_running :   49 - Create a database schema. Response: /usr/bin/pgbench -i --scale=100 --foreign-keys -p 5438 -h 127.0.0.1 -U postgres tdb
2024-11-27 21:28:56,973      DEBUG      pg_perfbench.benchmark_running :   51 - Result:
 
2024-11-27 21:28:56,974      DEBUG      pg_perfbench.benchmark_running :   52 - Running performance test: /usr/bin/pgbench -p 5438 -h 127.0.0.1 -U postgres tdb -c 5 -j 2 -T 10 --no-vacuum

```