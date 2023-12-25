# PostgreSQL Performance Bench
This tool provides methods to run standard(TPC-B) and custom pgbench benchmarks on a PostgreSQL 
database with detailed `report` generation. A key feature of the tool is its capability to configure reports according to the type of information gathered:

* Adding the result of executing a bash script on the database host;
* Adding the result of executing an SQL script on the database;
  
The application offers support for two configurations of database connections:

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
 ```python3.11 -m pip install -r requirements.txt```
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
## Service options
| Parameter      | Description                                                                                                                                             |
|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--help`, `-h` | Lists all the available options or flags that can be used with the command, <br> along with a short description of what each option does and after which exit occurs.|
| `--log-level`  | Application logging level: `info`, `debug`, `error`.<br/>Default - `info`                                                                               |
| `--clear-logs` | Clearing logs from the tool's previous session. <br>Logs are located in the 'logs' folder of the root directory.                                        |

## Connection options 
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

| Parameter            | Description                                                           |
|----------------------|-----------------------------------------------------------------------|
| `--pg-port`          | Forwarded port (default `5432`, relative to the current host)         |
| `--pg-host`          | Forwarded address (default `127.0.0.1`, relative to the current host) |
| `--pg-user`          | User of database (must be configured or set "postgres")               |
| `--pg-database`      | Database used for testing                                             |
| `--pg-user-password` | Password for database connection (optional)                           |
| `--pg-data-path`     | Path to the PostgreSQL data directory (relative to the database host) |
| `--pg-bin-path`      | Path to the PostgreSQL bin directory (relative to the database host)  |
### Workload options:
| Parameter            | Description                                                                |
|----------------------|----------------------------------------------------------------------------|
| `--benchmark`        | The benchmark to use: `default`, `custom`                                  | 
| `--pgbench-clients`  | pgbench benchmarking arguments: --clients, is set as an array (e.g. 1,2,3) |
| `--pgbench-jobs`     | pgbench benchmarking arguments: --jobs, is set as an array (e.g. 1,2,3)    |
| `--pgbench-time`     | pgbench benchmarking arguments: --time, is set as an array (e.g. 1,2,3)    |
| `--pgbench-path`     | Specify the pgbench path (relative to the current host)                    |
| `--psql-path`        | Specify the psql path (relative to the current host)                       |
| `--init-command`     | Terminal command to create a table schema (relative to the current host)   |
| `--workload-command` | Terminal command for loading the database (relative to the current host)   |

- Use placeholders to set values in the table schema and load testing commands:
configure placeholders like `'ARG_'+ <DB|Workload options>`.<br><br>  
For example, you can configure pgbench by specifying the path of the load files 
(this example describes the full set of arguments for ssh connection):
```
python3.11 -m pg_perfbench --log-level=debug \
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
--benchmark-type=default \
--pgbench-clients=5,10,50 \
--pgbench-time=600 \
--workload-path=/path/to/workload \
--pgbench-path=/usr/bin/pgbench \
--psql-path=/usr/bin/psql \
--init-command="cd ARG_WORKLOAD_PATH && ARG_PSQL_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U postgres ARG_PG_DATABASE -f ARG_WORKLOAD_PATH/table-schema.sql" \
--workload-command="ARG_PGBENCH_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U ARG_PG_USER --no-vacuum --file=ARG_WORKLOAD_PATH/perf_1.sql --file=ARG_WORKLOAD_PATH/perf_2.sql ARG_PG_DATABASE -c ARG_PGBENCH_CLIENTS -j 20 -T ARG_PGBENCH_TIME"
```


or standard pgbench load
(this example describes the full set of arguments for docker connection):
```
python3.11 -m pg_perfbench --log-level=debug \
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
