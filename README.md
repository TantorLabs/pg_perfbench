# PostgreSQL Performance Bench
This tool provides methods to run standard(TPC-B) and custom pgbench benchmarks on a PostgreSQL 
database with detailed `report` generation. A key feature of the tool is its capability to configure reports according to the type of information gathered:

* Adding the result of executing a bash script on the database host;
* Adding the result of executing an SQL script on the database;
  
The application supports two configurations for database connections, depending on its location:

* `SSH` - database located on a remote host;
* `Container` - database located in a Docker container;

## Prerequisites
- Pre-installed PostgreSQL client applications: `psql`, `pgbench`. For example, using:
```
sudo apt install postgresql-client
sudo apt install postgresql-contrib
 ```
- Python 3.11 and pip3:
```
cd /usr/src
sudo wget https://www.python.org/ftp/python/3.11.7/Python-3.11.7.tar.xz
sudo tar -xvf Python-3.11.7.tar.xz
sudo cd Python-3.11.7

sudo apt-get install libssl-dev libffi-dev gcc

./configure --prefix=/opt/python3.11
make altinstall

sudo ln -sf /opt/python3.11/bin/python3.11 /usr/bin/python3.11
sudo ln -sf /opt/python3.11/bin/pip3.11 /usr/bin/pip3.11


python3.11 --version
```
- Create a Python 3.11 virtual environment in the project's root directory for ease of use:
```
cd pg_perfbench
python3.11 -m venv venv
source venv/bin/activate
```
- Install additional packages for Python 3.11, for example, using:
 ```
  pip install -r requirements.txt
 ```
- For the tool to work, the database must be accessible under the user postgres or another
specified user with SUPERUSER rights
- Before running the tests, install and configure Docker access for the user who will be running the tool:
```
sudo apt-get install docker
sudo apt-get install docker.io
chmod 666 /var/run/docker.sock
```
- To ensure successful use, first thoroughly explore the capabilities of the tool and run the tests.

# Configuring options
pg_perfbench supports two modes: 'join' and 'benchmark'.
<br> In 'benchmark' mode, the application loads the
configured database instance and generates a report based on the report_struct.json template.<br>
In 'join' mode, the application compares reports with each other, the path to which can be specified
via the --input-dir flag (by default set to 'report' in the project root), according to criteria
described in join_tasks JSON files in the project root.
## Service options
| Parameter      | Description                                                                                                                                             |
|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--help`, `-h` | Lists all the available options or flags that can be used with the command, <br> along with a short description of what each option does and after which exit occurs.|
| `--log-level`  | Application logging level: `info`, `debug`, `error`.<br/>Default - `info`                                                                               |
| `--clear-logs` | Clearing logs from the tool's previous session. <br>Logs are located in the 'logs' folder of the root directory.                                        |

# Configuring pg_perfbench in `benchmark` mode
## Connection options 
> **Note**: During testing, port forwarding to the target database occurs, so make sure to use an available local forwarding port for --pg-port (default value is 5432).
During the operation of pg_perfbench, it is necessary to set local environment variables within the session connecting to the database host.

When establishing an SSH connection, you must first update the AcceptEnv parameter in the SSH configuration file (/etc/ssh/sshd_config) on the database server.
Specify the argument pattern as 'ARG_*' to allow multiple variables to be passed in:
<br>`/etc/ssh/sshd_config:` <br>
```
...
# Allow client to pass locale environment variables
AcceptEnv LANG LC_* ARG_*
...
```

In a Docker container, environment variables can be passed during its startup.
```
docker run -e "MYVAR1=$(echo $MYVAR1)" -e "MYVAR2=$(echo $MYVAR2)" myimage
```
### SSH connection

| Parameter           | Description                                                      |
|---------------------|------------------------------------------------------------------|
| `--ssh-port`        | Port for ssh connection (default: 22)                            |
| `--ssh-host`        | IP address of the remote server                                  |
| `--ssh-key`         | Path to the ssh connection private key file (must be configured) |
| `--remote-pg-host`  | Host of the remote server's database (default: 127.0.0.1)        |
| `--remote-pg-port`  | Port of the remote server's database (default: 5432)             |

* `The SSH connection user is postgres`. Configure SSH access keys on the database server to establish a connection to the postgres user:

```
# ========================================
# Actions on the pg_perfbench host
# ========================================

# create an ssh key at the path you specify 
mkdir -p path/to/your/postgres_keys/.ssh
ssh-keygen -t rsa -b 4096 -C "postgres" -f postgres_keys/.ssh/id_rsa
 
ls postgres_keys/.ssh
>>
    id_rsa  id_rsa.pub
 
 
chmod 700 postgres_keys/.ssh
chmod 644 postgres_keys/.ssh/id_rsa.pub
chmod 600 postgres_keys/.ssh/id_rsa 
 
scp postgres_keys/.ssh/id_rsa.pub <user>@<database_server_address>:/tmp
# ========================================
# Actions on the data base server
# ========================================
cat >> /etc/ssh/sshd_config << EOL
PubkeyAcceptedKeyTypes=+ssh-rsa
EOL
systemctl restart sshd
 
mkdir /var/lib/postgresql/.ssh
cat /tmp/id_rsa.pub >> /var/lib/postgresql/.ssh/authorized_keys
chmod 700 /var/lib/postgresql/.ssh
chown -R postgres:postgres /var/lib/postgresql/.ssh

```
Example of specified ssh connection arguments:
```
--ssh-port=22
--ssh-key=path/to/private_key
--ssh-host=10.111.1.111
--remote-pg-host=127.0.0.1
--remote-pg-port=5432
```

see more details on benchmark configuration over an SSH connection [here](doc/ssh_mode_usage.md).
### Docker connection
Preconfigure access to Docker for the user who is running the tool.

| Parameter          | Description                                             |
|--------------------|---------------------------------------------------------|
| `--image-name`     | Docker image name (must be pre-installed)               |
| `--container-name` | Name of creating container                              |
| `--docker-pg-host` | Container PostgreSQL database host (default: 127.0.0.1) |
| `--docker-pg-port` | Container PostgreSQL database port (default: 5432)      |      

<br>Example of specified docker connection arguments:<br>
```
--image-name=postgres:15
--container-name=cntr_expected
--docker-pg-host=127.0.0.1
--docker-pg-port=5432
```

see more details on benchmark configuration for a database in a Docker container [here](doc/docker_mode_usage.md).
### Common instruction
When utilizing an SSH connection, ensure that the postgres user has the privilege to clear the file 
system cache on the database server. For a Docker connection, identify the user operating the tool 
and execute the following command on the tool host.:

```
# ========================================
# Actions on the data base server
# ========================================
echo ' $(whoami) ALL=(ALL) NOPASSWD: /bin/sh -c echo 3 | /usr/bin/tee /proc/sys/vm/drop_caches' | sudo EDITOR='tee -a' visudo -f /etc/sudoers
```


## Database and workload options
### PostgreSQL database options:
The flags `pg_host` and `pg_port` are optional parameters for forwarding the address and port 
from the current host to the database host, `used directly by the tool`.

| Parameter         | Description                                                          |
|-------------------|----------------------------------------------------------------------|
| `--pg-port`       | Forwarded port (default `5432`, relative to the current host)        |
| `--pg-host`       | Forwarded address (default `127.0.0.1`, relative to the current host) |
| `--pg-user`       | User of database (must be configured or set "postgres")              |
| `--pg-database`   | Database used for testing                                            |
| `--pg-user-password` | Password for database connection (optional)                          |
| `--pg-data-path`  | Path to the PostgreSQL data directory (relative to the database host) |
| `--pg-bin-path`   | Path to the PostgreSQL bin directory (relative to the database host) |
| `--collect-pg-logs` | Enable database logging (logging must be configured by the user)     |
| `--custom-config`  | Use custom PostgreSQL config                                         |

### Workload options:
| Parameter            | Description                                                                |
|----------------------|----------------------------------------------------------------------------|
| `--benchmark-type`   | The benchmark to use: `default`, `custom`                                  | 
| `--workload-path`    | Path to the load scripts directory                                         |
| `--pgbench-clients`  | pgbench benchmarking arguments: --clients, is set as an array (e.g. 1,2,3) |
| `--pgbench-jobs`     | pgbench benchmarking arguments: --jobs, is set as an array (e.g. 1,2,3)    |
| `--pgbench-time`     | pgbench benchmarking arguments: --time, is set as an array (e.g. 1,2,3)    |
| `--pgbench-path`     | Specify the pgbench path (relative to the current host)                    |
| `--psql-path`        | Specify the psql path (relative to the current host)                       |
| `--init-command`     | Terminal command to create a table schema (relative to the current host)   |
| `--workload-command` | Terminal command for loading the database (relative to the current host)   |

- Use placeholders to set values in the table schema and load testing commands:
configure placeholders like `'ARG_'+ <DB/Workload options>`.<br><br>  
For example, you can configure pgbench by specifying the path of the load files 
(this example describes the full set of arguments for ssh connection):
```
python3.11 -m pg_perfbench --mode=benchmark \
--collect-pg-logs \
--custom-config=/tmp/user_postgresql.conf \
--log-level=debug \
--ssh-port=22 \
--ssh-key=path/to/private_key \
--ssh-host=10.128.0.141 \
--remote-pg-host=127.0.0.1 \
--remote-pg-port=5432 \
--pg-host=127.0.0.1 \
--pg-port=5435 \
--pg-user=postgres \
--pg-user-password=test_user_password \
--pg-database=tdb \
--pg-data-path=/var/lib/postgresql/data \
--pg-bin-path=/usr/lib/postgresql/15/bin \
--benchmark-type=custom \
--pgbench-clients=5,10,50 \
--pgbench-time=600 \
--workload-path=/path/to/workload \
--pgbench-path=/usr/bin/pgbench \
--psql-path=/usr/bin/psql \
--init-command="cd ARG_WORKLOAD_PATH && ARG_PSQL_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U postgres ARG_PG_DATABASE -f ARG_WORKLOAD_PATH/table-schema.sql" \
--workload-command="ARG_PGBENCH_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U ARG_PG_USER --no-vacuum --file=ARG_WORKLOAD_PATH/perf_1.sql --file=ARG_WORKLOAD_PATH/perf_2.sql ARG_PG_DATABASE -c ARG_PGBENCH_CLIENTS -j 20 -T ARG_PGBENCH_TIME"
```


or standard pgbench load
(this example shows all arguments needed to load a database in a Docker container):
```
python3.11 -m pg_perfbench --mode=benchmark \
--log-level=debug \
--collect-pg-logs \
--custom-config=/tmp/user_postgresql.conf \
--image-name=postgres:15 \
--container-name=cntr_expected \
--docker-pg-host=127.0.0.1 \
--docker-pg-port=5432 \
--pg-host=127.0.0.1 \
--pg-port=5435 \
--pg-user=postgres \
--pg-user-password=test_user_password \
--pg-database=tdb \
--pg-data-path=/var/lib/postgresql/tantor-se-1c-15/data \
--pg-bin-path=/opt/tantor/db/15/bin \
--benchmark-type=default \
--pgbench-clients=5,10,50 \
--pgbench-time=600 \
--pgbench-jobs=19 \
--init-command="ARG_PGBENCH_PATH -i --scale=100 --foreign-keys -p ARG_PG_PORT ARG_PG_HOST -U postgres ARG_PG_DATABASE" \
--workload-command="ARG_PGBENCH_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U ARG_PG_USER ARG_PG_DATABASE -c ARG_PGBENCH_CLIENTS -j ARG_PGBENCH_JOBS -T ARG_PGBENCH_TIME --no-vacuum"

```

# Configuring report

You can configure the JSON report template file `pg_perfbench/reports/templates/report_struct.json`.
Add or remove reports of the following types:

- "shell_command_file" - a report with the result of executing the specified bash script relative to the database host in the `pg_perfbench/commands/bash_commands` directory, for example:
```
"example_bash_report": {
  "header": "example_bash_header",
  "state": "collapsed",
  "item_type": "plain_text",
  "shell_command_file": "bash_example.sh",
  "data": ""
}
```

- "sql_command_file" - a report with the result of executing the specified SQL script in the database located in the `pg_perfbench/commands/sql_commands` directory, for example:
```
"example_sql_report": {
    "header": "example_sql_header",
    "state": "collapsed",
    "item_type": <"plain_text", "table">,
    "sql_command_file": "sql_example.sql",
    "data": ""
}
```

# Configuring pg_perfbench in `join` mode

| Parameter           | Description                                                                                                                                                    |
|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--join-task`       | A JSON file containing a set of merge criteria,which are items of sections,<br/> should be located in join_tasks at the root of the project                    |
| `--input-dir`       | Directory with reports on the load of a single database instance, files with <br/>a 'join' prefix are ignored. The default directory set is 'report'           |
| `--reference-report`| The report specified as a benchmark for comparison with other reports. By default, the first report listed alphabetically in the --input-dir path is selected  |

Template for the comparison criteria file:
```
{
        "description": "Comparison of database performance across different configurations in the same environment using the same PostgreSQL version",
        "items": [
            "<section_name_of_report_struct>.<report_name>.data",
            ....
            "system.uname_a.data",
        ]
}
```
Example of argument configuration in join mode:
```
python3.11 -m pg_perfbench --mode=join \
--join-task=task_compare_dbs_on_single_host.json \
--reference-report=benchmark_report.json \
--input-dir=/path/to/some/reports
```
# Running tests
When testing the tool, a Docker connection is used. Preconfigure access to Docker for the user who is running the tool.
- specify the `user` from which the tool is run:
```
echo ' <pg_perfbench user> ALL=(ALL) NOPASSWD: /bin/sh -c echo 3 | /usr/bin/tee /proc/sys/vm/drop_caches' | sudo EDITOR='tee -a' visudo -f /etc/sudoers
```
- set PYTHONPATH variable:
```
cd pg_perfbench
>>
pg_perfbench  requirements_dev.txt  tests
LICENSE log README.md requirements.txt

export PYTHONPATH=$(pwd)
```
- single test running. Example of executing unit tests:
```
python -m unittest tests.test_cli.test_arg_parser -v --failfast
python -m unittest tests.test_context.test_workload -v --failfast
python -m unittest tests.test_docker.test_pg_perfbench -v --failfast
```
- executing all tests: 
<br>`python -m unittest discover tests`
###
###
