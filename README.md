# PostgreSQL Performance Bench
This tool provides methods to run standard(TPC-B) and custom pgbench benchmarks on a PostgreSQL 
database with detailed `report` generation. An important feature of the tool is the ability to configure the report based on the type of information collected:

* Adding the result of executing a bash script on the database host
* Adding the result of executing an SQL script on the database

The pg_perfbench tool supports two types of database connections:

* `SSH` - remote
* `Docker` - container

## Prerequisites
- The `psql`, `pgbench` PostgreSQL client
- Python 3.11 and pip3
- For convenience, create a Python 3.11 virtual environment in the root directory of the project:
<br>`cd pg_perfbench`
<br>`python3.11 -m venv venv`
<br>`source venv/bin/activate`
- Install additional packages, for Python 3.11 eg. with:
 <br>`python3.11 -m pip install -r requirements.txt`
- For the tool to work, the database must be accessible under the user postgres or another 
specified user with SUPERUSER rights
- Before running the tests, configure Docker access for the user who will be running the tool.
- To ensure successful use, first thoroughly explore the capabilities of the tool and run the tests.

# Configuring options
## Service options
| Parameter      | Description                                                                                                                                             |
|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--help`, `-h` | Lists all the available options or flags that can be used with the command,<br> along with a short description of what each option does and after which exit occurs.|
| `--log-level`  | Application logging level: `info`, `debug`, `error`.<br/>Default - `info`                                                                               |
| `--clear-logs` | Clearing logs from the tool's previous session. <br>Logs are located in the 'logs' folder of the root directory.                                        |

## Connection options 
### SSH connection

| Parameter           | Description                                                      |
|---------------------|------------------------------------------------------------------|
| `--ssh-port`        | Port for ssh connection (default: 22)                            |
| `--ssh-host`        | IP address of the remote server                                  |
| `--ssh-key`         | Path to the ssh connection private key file (must be configured) |
| `--remote-pg-host`  | Host of the remote server's database(default: 127.0.0.1)         |
| `--remote-pg-port`  | Port of the remote server's database(default: 5432)              |

* `The SSH connection user is postgres`.Configure SSH access keys on the database server to establish a connection to the postgres user:

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
<br>Example of specified ssh connection arguments:
<br>`--ssh-port=22`<br>
`--ssh-key=path/to/private_key`<br>
`--ssh-host=10.111.1.111`<br>
`--remote-pg-host=127.0.0.1`<br>
`--remote-pg-port=5432`<br>


### Docker connection
Preconfigure access to Docker for the user who is running the tool.

| Parameter          | Description                                            |
|--------------------|--------------------------------------------------------|
| `--image-name`     | Docker image name(must be pre-installed)               |
| `--container-name` | Name of creating container                             |
| `--docker-pg-host` | Container PostgreSQL database host(default: 127.0.0.1) |
| `--docker-pg-port` | Container PostgreSQL database port(default: 5432)      |      

<br>Example of specified docker connection arguments:<br>
`--image-name=postgres:15`<br>
`--container-name=cntr_expected`<br>
`--docker-pg-host=127.0.0.1`<br>
`--docker-pg-port=5432`<br>

### Common instruction
When using `SSH connection`, grant the `postgres user` the privilege to clear the file 
system cache `on the database server`. For `Docker connection`, specify the `user` from
which the tool is run, and execute the following command `on the tool host`:

```
# ========================================
# Actions on the data base server
# ========================================
echo '<user> ALL=(ALL) NOPASSWD: /bin/sh -c echo 3 | /usr/bin/tee /proc/sys/vm/drop_caches' | sudo EDITOR='tee -a' visudo -f /etc/sudoers
```


## Database and workload options
### PostgreSQL database options:
The flags `pg_host` and `pg_port` are optional parameters for forwarding the address and port 
from the current host to the database host, `used directly by the tool`.

| Parameter            | Description                                                            |
|----------------------|------------------------------------------------------------------------|
| `--pg-port`          | Forwarded port (default `5432`, relative to the current host)          |
| `--pg-host`          | Forwarded address (default `127.0.0.1`, relative to the current host)  |
| `--pg-user`          | User of database(must be configured or set "postgres")                 |
| `--pg-database`      | Database used for testing                                              |
| `--pg-user-password` | Password for database connection(optional)                             |
| `--pg-data-path`     | Path to the PostgreSQL data directory (relative to the database host)  |
| `--pg-bin-path`      | Path to the PostgreSQL bin directory (relative to the database host)   |
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
`For example`, you can configure pgbench by specifying the path of the load files 
(this example describes the full set of arguments for ssh connection):
<br>`python3.11 -m pg_perfbench --log-level=debug \ `<br>
`--ssh-port=22 \ `<br>
`--ssh-key=path/to/private_key \`<br>
`--ssh-host=10.128.0.141 \ `<br>
`--remote-pg-host=127.0.0.1 \ `<br>
`--remote-pg-port=5432 \ `<br><br>
`--pg-host=127.0.0.1 \ `<br>
`--pg-port=5435 \ `<br>
`--pg-user=postgres \ `<br>
`--pg-user-password=test_user_password \ `<br>
`--pg-database=tdb \ `<br>
`--pg-data-path=/var/lib/postgresql/data \ `<br>
`--pg-bin-path=/usr/lib/postgresql/15/bin \ `<br><br>
`--benchmark-type=default \ `<br>
`--pgbench-clients=5,10,50 \ `<br>
`--pgbench-time=600 \ `<br>
`--workload-path=/path/to/workload \ `<br>
`--pgbench-path=/usr/bin/pgbench \ `<br>
`--psql-path=/usr/bin/psql \ `<br>
`--init-command="cd ARG_WORKLOAD_PATH && ARG_PSQL_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U postgres ARG_PG_DATABASE -f ARG_WORKLOAD_PATH/table-schema.sql" \ `<br>
`--workload-command="ARG_PGBENCH_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U ARG_PG_USER --no-vacuum --file=ARG_WORKLOAD_PATH/perf_1.sql --file=ARG_WORKLOAD_PATH/perf_2.sql ARG_PG_DATABASE -c ARG_PGBENCH_CLIENTS -j 20 -T ARG_PGBENCH_TIME"`

    <br>or standard pgbench load
    (this example describes the full set of arguments for docker connection):
    <br>`python3.11 -m pg_perfbench --log-level=debug \ `<br>
    `--image-name=postgres:15 \ `<br>
    `--container-name=cntr_expected \ `<br>
    `--docker-pg-host=127.0.0.1 \ `<br>
    `--docker-pg-port=5432 \ `<br><br>
    `--pg-host=127.0.0.1 \ `<br>
    `--pg-port=5435 \ `<br>
    `--pg-user=postgres \ `<br>
    `--pg-user-password=test_user_password \ `<br>
    `--pg-database=tdb \ `<br>
    `--pg-data-path=/var/lib/postgresql/tantor-se-1c-15/data \ `<br>
    `--pg-bin-path=/opt/tantor/db/15/bin \ `<br><br>
    `--benchmark-type=default \ `<br>
    `--pgbench-clients=5,10,50 \ `<br>
    `--pgbench-time=600 \ `<br>
    `--pgbench-jobs=19 \ `<br>
    `--init-command="ARG_PGBENCH_PATH -i --scale=100 --foreign-keys -p ARG_PG_PORT -h ARG_PG_HOST -U postgres ARG_PG_DATABASE" \ `<br>
    `--workload-command="ARG_PGBENCH_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U ARG_PG_USER ARG_PG_DATABASE -c ARG_PGBENCH_CLIENTS -j ARG_PGBENCH_JOBS -T ARG_PGBENCH_TIME --no-vacuum"`<br>

# Configuring report

You can configure the JSON report template file `pg_perfbench/reports/templates/report_struct.json`: add or remove a report of the type:

- "shell_command_file" - a report with the result of executing the specified bash script relative to the database host in the `pg_perfbench/commands/bash_commands` directory, for example::
<br><br>`                "example_bash_report": {`
<br>`                    "header": "example_bash_header",`
<br>`                    "state": "collapsed",`
<br>`                    "item_type": "plain_text",`
<br>`                    "shell_command_file": "bash_example.sh",`
<br>`                    "data": ""`
<br>`                }`
<br><br>
- "sql_command_file" - a report with the result of executing the specified SQL script in the database located in the `pg_perfbench/commands/sql_commands` directory, for example:
<br><br>`                "example_sql_report": {`
<br>`                    "header": "example_sql_header",`
<br>`                    "state": "collapsed",`
<br>`                    "item_type": <"plain_text", "table">,`
<br>`                    "sql_command_file": "sql_example.sql",`
<br>`                    "data": ""`
<br>`                }`
<br><br>
# Running tests
When testing the tool, a Docker connection is used. Preconfigure access to Docker for the user who is running the tool.
- set PYTHONPATH variable:
<br>`cd pg_perfbench`<br>
`export PYTHONPATH=$(pwd)`
- single test running: 
  <br>`python -m unittest tests.test_*.test_* -v --failfast`
- full test running: 
  <br>`python -m unittest discover tests`
###
###
