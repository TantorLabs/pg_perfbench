# pg_perfbench - PostgreSQL Performance Bench

## Overview

pg_perfbench is a versatile benchmarking tool designed to evaluate the performance of PostgreSQL databases. It enables running both standard (TPC-B) and custom `pgbench` benchmarks, with a focus on detailed and configurable `report` generation to capture key insights. 

The tool offers flexible report customization, allowing users to tailor the content based on collected data, such as:

- **Execution of Bash Scripts**: Incorporate the output of Bash scripts run on the database host directly into the report.
- **Execution of SQL Scripts**: Include SQL query results from the database to analyze specific metrics.

pg_perfbench supports two primary database connection modes to suit different deployment setups:

- **SSH**: Connects to a PostgreSQL database hosted on a remote server via SSH.
- **Docker**: Connects to a PostgreSQL instance running inside a Docker container.


##	Terminology

| Term                  | Description                                                                                                                                                      |
|-----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **pgbench**           | A widely used benchmarking tool for PostgreSQL, designed to simulate multiple clients running transactions in parallel, often based on the TPC-B standard.       |
| **TPC-B**             | A standard for benchmarking OLTP (online transaction processing) systems, primarily focusing on transaction throughput and data manipulation.                    |
| **Benchmark mode**    | The configuration and set of operations for running a specific type of pgbench benchmark, which can include standard or custom modes as set by the user.         |
| **Report**            | A detailed record generated post-benchmark containing the performance metrics and optionally, the output of bash and SQL scripts, for analysis and comparison.   |
| **SSH connection**    | Connection to a PostgreSQL database on a remote host through SSH, allowing benchmark operations to run remotely on databases hosted outside Docker environments. |
| **Docker connection** | Connection to a PostgreSQL database running within a Docker container, enabling benchmark tests and reporting within isolated containerized environments.        |
| **Report template**   | The predefined format or structure for reports generated by the tool, specifying the data points to collect and the report format for analysis consistency.      |
| **Join reports**      | A feature that consolidates multiple benchmark reports into one, allowing for an aggregated view of results across different benchmark instances.                |


## Features

*pg_perfbench* operates in several modes to facilitate flexible benchmarking and reporting with PostgreSQL databases.

- **Benchmark**: This mode enables performance benchmarking through different types of database connections:
    - **SSH Connection**: Enables benchmarking on a remote PostgreSQL database server over SSH. Suitable for testing performance in distributed environments.
    - **Docker Connection**: Facilitates benchmarking on a PostgreSQL instance running in a Docker container. Ideal for isolated testing and containerized environments.

- **Join**: This mode allows for merging multiple benchmark reports into a single, cohesive report. This is useful for comprehensive analysis and comparison of results from different test scenarios.


## Requirements & Dependencies



## Installation guide

#### Ubuntu/Redhat/CentOS

1. Install Python3.11 if it isn't installed: `sudo apt-get install python3.11` (for Ubuntu), `sudo yum install python311` (for Redhat/Centos)
2. Clone the repository: `git clone https://github.com/TantorLabs/pg_perfbench.git`
3. Go to the project directory: `cd pg_perfbench`
4. Set up a virtual environment:
   - Install the virtual environment: `python3.11 -m venv venv11`
   - Activate the virtual environment: `source venv11/bin/activate`
5. Install the dependencies: `pip install -r requirements.txt`
6. For the tool to work, the database must be accessible under the user *postgres* or another
specified user with *SUPERUSER* rights
7. Before running the tests, install and configure Docker access for the user who will be running the tool:
```commandline
sudo apt-get install docker
sudo apt-get install docker.io
chmod 666 /var/run/docker.sock
```
To ensure successful use, first thoroughly explore the capabilities of the tool and run the *tests*.



##	Testing
When testing the tool, a Docker connection is used. Preconfigure access to Docker for the user who is running the tool.
- Specify the `user` from which the tool is run:
```venv
echo ' <pg_perfbench user> ALL=(ALL) NOPASSWD: /bin/sh -c echo 3 | /usr/bin/tee /proc/sys/vm/drop_caches' | sudo EDITOR='tee -a' visudo -f /etc/sudoers
```
- Set PYTHONPATH variable:
```venv
cd pg_perfbench
ls
>>
pg_perfbench  requirements_dev.txt  tests
LICENSE log README.md requirements.txt

export PYTHONPATH=$(pwd)
```
- Execute all tests: 
```venv
python -m unittest discover tests
```
- Single test running. Example of executing unit tests:
```venv
python -m unittest tests.test_cli.test_arg_parser -v --failfast
python -m unittest tests.test_context.test_workload -v --failfast
python -m unittest tests.test_docker.test_pg_perfbench -v --failfast
```


## Usage

To display the help message for the CLI, run:

```venv
python -m pg_perfbench --help
```

### Common `pg_perfbench` options

These options control the overall behavior of `pg_perfbench`.

| Parameter        | Description                                                                                                            |
|------------------|------------------------------------------------------------------------------------------------------------------------|
| `--help`, `-h`   | Lists all available options and flags, along with brief descriptions for each. Exits after displaying the information. |
| `--log-level`    | Sets the logging level: `info`, `debug`, `error` (default: `info`).                                                    |
| `--clear-logs`   | Clears logs from the previous session. Logs are stored in the `logs` folder in the root directory.                     |
| `--mode`         | Operation mode: `benchmark` (for performance tests) or `join` (for report merging).                                    |


### Database configuration options

These options configure the PostgreSQL database connection and authentication settings.

| Parameter            | Description                                                                                                 |
|----------------------|-------------------------------------------------------------------------------------------------------------|
| `--pg-host`          | Host IP for PostgreSQL (relative to the current host, default: `127.0.0.1`).                                |
| `--pg-port`          | Forwarded port for PostgreSQL (default: `5432`, relative to the current host).                              |
| `--pg-user`          | PostgreSQL user for the connection (default or configured as "postgres").                                   |
| `--pg-user-password` | Password for the PostgreSQL user (if required by the database configuration).                               |
| `--pg-database`      | Name of the database used for benchmarking.                                                                 |
| `--pg-data-path`     | Path to the PostgreSQL data directory on the database host.                                                 |
| `--pg-bin-path`      | Path to the PostgreSQL binaries on the database host.                                                       |
| `--collect-pg-logs`  | Enables PostgreSQL log collection during benchmarking (requires prior configuration on the database host).  |
| `--custom-config`    | Specifies a custom PostgreSQL configuration file for the benchmark session.                                 |


### Workload configuration options

These options set up the workload parameters and benchmarking commands.

| Parameter             | Description                                                                                          |
|-----------------------|------------------------------------------------------------------------------------------------------|
| `--benchmark-type`    | Type of benchmark to use: `default` or `custom` (for custom workload use `--benchmark-type=custom`). |
| `--pgbench-clients`   | Array of client counts for `pgbench` benchmarks (e.g., `5,10,20`).                                   |
| `--pgbench-jobs`      | Array of job counts for `pgbench` benchmarks (e.g., `1,2,3`).                                        |
| `--pgbench-time`      | Array of durations (in seconds) for `pgbench` benchmarks (e.g., `30,60,90`).                         |
| `--pgbench-path`      | Path to the `pgbench` executable (relative to the current host).                                     |
| `--psql-path`         | Path to the `psql` executable (relative to the current host).                                        |
| `--workload-path`     | Path to the workload directory containing SQL scripts or other required files.                       |
| `--init-command`      | Command to initialize the database schema (relative to the current host).                            |
| `--workload-command`  | Command to load the benchmark workload into the database (relative to the current host).             |

### Environment Variables (Placeholders)

The following placeholders can be used in `--init-command` and `--workload-command` options. These allow dynamic substitution of values based on command-line arguments, making the configuration flexible across different environments.

| Placeholder            | Description                                                                                             |
|------------------------|---------------------------------------------------------------------------------------------------------|
| `ARG_PGBENCH_PATH`     | Path to the `pgbench` executable (from `--pgbench-path`).                                               |
| `ARG_PSQL_PATH`        | Path to the `psql` executable (from `--psql-path`).                                                     |
| `ARG_PG_HOST`          | Host IP for PostgreSQL after port forwarding (from `--pg-host`).                                        |
| `ARG_PG_PORT`          | Port for PostgreSQL after port forwarding (from `--pg-port`).                                           |
| `ARG_PG_USER`          | PostgreSQL user (from `--pg-user`).                                                                     |
| `ARG_PG_USER_PASSWORD` | Password for PostgreSQL user (from `--pg-user-password`).                                               |
| `ARG_PG_DATABASE`      | Name of the database used for benchmarking (from `--pg-database`).                                      |
| `ARG_PGBENCH_CLIENTS`  | Current client count for `pgbench` (from `--pgbench-clients`).                                          |
| `ARG_PGBENCH_JOBS`     | Number of parallel jobs for `pgbench` (from `--pgbench-jobs`).                                          |
| `ARG_PGBENCH_TIME`     | Duration in seconds for `pgbench` (from `--pgbench-time`).                                              |
| `ARG_WORKLOAD_PATH`    | Path to the workload directory, including SQL files or other data for testing (from `--workload-path`). |

To set an environment variable in the command line, you can use the following syntax:

For **Linux/macOS**:

```bash
export VARIABLE_NAME=value
```

For example, if you want to set `ARG_PG_PORT` to `5433` in Linux/macOS, you would use:

```bash
export ARG_PG_PORT=5433
```

This environment variable will be available in the current shell session. If you need it to persist across sessions, you can add the `export` command to your shell’s profile file (e.g., `.bashrc` or `.zshrc` for Linux/macOS).

### Run benchmark

The benchmark can be run using two types of connections:
- **SSH connection**
- **Docker connection**

#### SSH connection

| Parameter           | Description                                                                                                          |
|---------------------|----------------------------------------------------------------------------------------------------------------------|
| `--ssh-port`        | Port for the SSH connection (default: 22).                                                                           |
| `--ssh-host`        | IP address of the remote server hosting the database.                                                                |
| `--ssh-key`         | Path to the SSH private key file (must be configured before running the benchmark).                                  |
| `--remote-pg-host`  | Local IP of the database on the remote server (default: `127.0.0.1`).                                                |
| `--remote-pg-port`  | Port of the database on the remote server (default: `5432`).                                                         |
| `--pg-host`         | The host IP used by `pgbench` after SSH port forwarding (usually `127.0.0.1`).                                       |
| `--pg-port`         | Port on the `pg_perfbench` host to which `pgbench` connects after forwarding (should differ if port 5432 is in use). |

> **Important**: If another PostgreSQL instance is already running on port 5432 on the `pg_perfbench` host, use a different port for SSH forwarding to prevent conflicts.

Example of SSH Connection Parameters:
```
--ssh-port=22
--ssh-key=path/to/private_key
--ssh-host=10.111.1.111
--remote-pg-host=127.0.0.1
--remote-pg-port=5432
--pg-host=127.0.0.1
--pg-port=5433  # Use a different port if 5432 is already in use
```

**Example Setup Using a Virtual Machine (VM)**

To simulate an SSH connection, you can set up a virtual machine with PostgreSQL installed (see more details in [How to Configure SSH Connection with Oracle VirtualBox](#how-to-configure-ssh-connection-with-oracle-virtualbox)):

1. **Create a VM with Ubuntu (or your preferred OS)**:
   - Install PostgreSQL on the VM:
     ```bash
     sudo apt update
     sudo apt install postgresql
     sudo systemctl start postgresql
     ```
   - Install OpenSSH Server on the VM to enable SSH:
     ```bash
     sudo apt install openssh-server
     sudo systemctl start ssh
     ```

2. **Configure SSH Key-Based Authentication** (on the host machine):
   - Generate an SSH key pair on the host:
     ```bash
     ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
     ```
   - Copy the SSH public key to the VM:
     ```bash
     ssh-copy-id user@<VM_IP_address>
     ```

3. **Run pg_perfbench with SSH Connection**:
   After configuring the VM, you can run `pg_perfbench` with the following command:

```venv
python -m pg_perfbench --mode=benchmark \
--ssh-host=<VM_IP_address> \
--ssh-port=22 \
--ssh-key=~/.ssh/id_rsa \
--remote-pg-host=127.0.0.1 \
--remote-pg-port=5432 \
--pg-host=127.0.0.1 \
--pg-port=5433 \
--pg-user=postgres \
--pg-database=testdb \
--benchmark-type=default \
--pgbench-clients=5,10 \
--pgbench-time=60 \
--pgbench-path=/usr/bin/pgbench \
--psql-path=/usr/bin/psql
```


You also can configure pgbench by specifying the path of the load files 
(this example describes the full set of arguments for ssh connection).
Use placeholders to set values in the table schema and load testing commands: configure placeholders like `'ARG_'+ <DB|Workload options>`.
```venv
python -m pg_perfbench --mode=benchmark \
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


#### Docker connection

Before using the Docker connection mode, ensure the user running `pg_perfbench` has the necessary permissions to access Docker. Typically, this involves adding the user to the `docker` group.

| Parameter          | Description                                                            |
|--------------------|------------------------------------------------------------------------|
| `--image-name`     | The name of the Docker image to use (must be pre-installed)            |
| `--container-name` | Name of the container to be created and used for benchmarking          |
| `--docker-pg-host` | Host for PostgreSQL inside the Docker container (default: `127.0.0.1`) |
| `--docker-pg-port` | Port for PostgreSQL inside the Docker container (default: `5432`)      |

**Example Docker connection arguments:**

These arguments specify the necessary Docker parameters to set up a PostgreSQL instance for benchmarking.

```
--image-name=postgres:15
--container-name=cntr_expected
--docker-pg-host=127.0.0.1
--docker-pg-port=5432
```

**Example configuration for running pg_perfbench with Docker connection:**

Below is an example of how you might configure `pg_perfbench` for a Docker connection. This includes specifying benchmarking parameters such as client count, time, and commands for initializing and loading data.
``` venv
python -m pg_perfbench --mode=benchmark \
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

###	Work with reports

#### Configuring Report

You can customize the JSON report template file located at `pg_perfbench/reports/templates/report_struct.json`. This template allows you to add or remove specific types of reports, enabling flexibility in the structure of your generated reports.

- **"shell_command_file"**: Includes the output of a specified Bash script, which is located relative to the database host in the `pg_perfbench/commands/bash_commands` directory. This is useful for capturing system information or custom metrics from shell commands.

Example configuration for a Bash report:
```json
"example_bash_report": {
  "header": "example_bash_header",
  "state": "collapsed",
  "item_type": "plain_text",
  "shell_command_file": "bash_example.sh",
  "data": ""
}
```

- **"sql_command_file"**: Executes a specified SQL script in the PostgreSQL database and includes its output in the report. The SQL scripts are stored in the `pg_perfbench/commands/sql_commands` directory. This allows you to include custom SQL metrics or query results directly in the report.

Example configuration for an SQL report:
```json
"example_sql_report": {
    "header": "example_sql_header",
    "state": "collapsed",
    "item_type": "<plain_text, table>",
    "sql_command_file": "sql_example.sql",
    "data": ""
}
```

### Configuring pg_perfbench in `join` Mode

The `join` mode in `pg_perfbench` enables merging multiple reports into a single consolidated report for easier comparison across different benchmarks or configurations. This mode is configured using specific parameters and a JSON file that defines the criteria for merging sections of reports.

| Parameter            | Description                                                                                                                                            |
|----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--join-task`        | A JSON file specifying the criteria for merging report sections. This file should be located in the `join_tasks` directory at the project root.        |
| `--input-dir`        | Directory containing the reports for a single database instance. Files prefixed with `join` are ignored. Default directory is set to `report`.         |
| `--reference-report` | The report used as a reference for comparison with other reports. If not specified, the first report alphabetically in the `--input-dir` path is used. |

**Template for the comparison criteria file**:
The JSON file defines which sections and data points to include in the merged report. Here is an example of the structure:

```json
{
    "description": "Comparison of database performance across different configurations in the same environment using the same PostgreSQL version",
    "items": [
        "<section_name_of_report_struct>.<report_name>.data",
        ...
        "system.uname_a.data"
    ]
}
```

**Example of running pg_perfbench in join mode**:

To execute `pg_perfbench` in `join` mode with the specified comparison criteria, use the following command:

```venv11
python -m pg_perfbench --mode=join \
    --join-task=task_compare_dbs_on_single_host.json \
    --reference-report=benchmark_report.json \
    --input-dir=/path/to/some/reports
```


## Project and directory structure

Main directories:
- `join_tasks/`: Contains JSON files defining criteria for merging multiple reports in `join` mode.
- `log/`: Stores application log files generated during benchmark runs.
- `pg_perfbench/`: Main Python modules and core benchmarking logic.
- `report/`: Directory where generated benchmark reports are saved in HTML and JSON formats.
- `tests/`: Contains test modules for validating various functionalities of `pg_perfbench`.

The core logic of `pg_perfbench` is organized within the following Python modules:

- **`pg_perfbench/benchmark_running.py`**: Manages the execution of benchmark tests.
- **`pg_perfbench/cli/args_parser.py`**: Handles command-line argument parsing.
- **`pg_perfbench/commands`**: Contains auxiliary shell and SQL scripts used in benchmarking.
- **`pg_perfbench/connections/`**: Defines connection logic, including `docker.py` and `ssh.py` for Docker and SSH connections, respectively.
- **`pg_perfbench/join_reports.py`**: Logic for merging multiple benchmark reports in `join` mode.
- **`pg_perfbench/reports/report.py`**: Manages report generation, formatting, and schema validation.
- **`pg_perfbench/context/`**: Defines the `Context` class, managing configurations and context settings.
- **`pg_perfbench/operations/`**: Contains modules for specific database operations and utilities.

### Example Directory Structure

Below is a detailed view of the project directory structure in work process, with key directories and files highlighted.

`tree pg_perfbench/ -L 3`:

```commandline
pg_perfbench/
├── join_tasks                # Contains JSON files for merging criteria in join mode
│   └── task_compare_dbs_on_single_host.json
├── LICENSE
├── log                       # Stores log files for each benchmark run
│   ├── 2024-10-09_15:58:31.log
│   └── ... (other logs)
├── pg_perfbench              # Core Python modules for benchmarking
│   ├── benchmark_running.py  # Manages the execution of benchmark tests
│   ├── cli                   # CLI utilities for argument parsing
│   │   ├── args_parser.py
│   ├── commands              # Directory with shell and SQL command scripts
│   │   ├── bash_commands
│   │   └── sql_commands
│   ├── compatibility.py      # Handles compatibility issues across different environments
│   ├── connections           # Connection logic for SSH and Docker
│   │   ├── docker.py
│   │   └── ssh.py
│   ├── context               # Manages configuration and context classes
│   │   ├── utils.py
│   ├── env_data.py           # Environment-specific data management
│   ├── exceptions.py         # Custom exceptions for error handling
│   ├── join_reports.py       # Logic for merging multiple reports
│   ├── logs.py               # Logging utilities
│   ├── operations            # Contains specific DB operations and utility scripts
│   │   ├── db.py
│   ├── pgbench_utils.py      # Utility functions for managing pgbench
│   ├── reports               # Report generation and templates
│   │   ├── report.py
│   │   └── templates
│   └── workload              # Workload definitions, e.g., TPC-C and TPC-E
│       ├── tpc-c
│       └── tpc-e
├── README.md
├── report                    # Stores generated benchmark reports in HTML and JSON formats
│   ├── single_report_2024-10-01_22:01:38.html
│   └── ... (other reports)
├── requirements_dev.txt      # Development dependencies
├── requirements.txt          # Application dependencies
├── tests                     # Test modules for validating functionality
│   ├── test_cli              # CLI tests
│   ├── test_context          # Context management tests
│   └── test_docker           # Docker connection tests
│       ├── test_pg_perfbench.py
├── tmp.py                    # Temporary or auxiliary scripts
└── venv11                   # Python virtual environment for project dependencies
```

### Explanation of Key Directories and Files

- **`join_tasks/`**: Contains JSON files like `task_compare_dbs_on_single_host.json` which define criteria for merging sections of reports, useful for `join` mode.
- **`log/`**: Stores log files, which help in debugging and tracking benchmark runs.
- **`pg_perfbench/`**: Main codebase directory containing core modules for running benchmarks, handling connections, and generating reports. Key subdirectories and files include:
  - `commands/`: Contains `bash_commands` and `sql_commands`, which are shell and SQL scripts executed during benchmarking.
  - `connections/`: Includes modules for setting up Docker (`docker.py`) and SSH (`ssh.py`) connections.
  - `context/`: Manages configurations and settings through the `Context` class.
  - `reports/`: Contains the `report.py` module for creating benchmark reports, along with `templates` for report structure.
- **`report/`**: Stores generated HTML and JSON reports, making it easy to view results of previous benchmark runs.
- **`tests/`**: Contains testing modules to validate CLI functionality, context management, and Docker connections.


----

## How to

This paragraph shows any case of work with **pg_perfbench**.

### How to Configure SSH Connection with Oracle VirtualBox

This guide explains how to set up an SSH connection to a PostgreSQL database running on a Virtual Machine (VM) in Oracle VirtualBox. This setup is useful for benchmarking or remote database management from a host machine.

#### 1. Host Machine Setup

1. **Generate SSH Key Pair**:
   Generate an SSH key pair on your host machine for secure access to the VM.
   ```bash
   ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
   ```

2. **Identify Network Interfaces**:
   List network interfaces on the host machine to find the correct network adapter for the bridge connection.
   ```bash
   ip link show
   ```

3. **Configure VirtualBox Network**:
   In VirtualBox, set the VM network adapter to use a bridged connection:
   - Go to **Settings > Network > Adapter 1**.
   - Set **Attached to** to **Bridged Adapter**.
   - Select the correct adapter (e.g., `wlp0s20f3`) from the **Name** dropdown list.
   - Confirm that the adapter is active by checking it with `ip link show`.

#### 2. Virtual Machine Setup

1. **Install PostgreSQL**:
   On the VM, install PostgreSQL and set it to start on boot.
   ```bash
   sudo apt update
   sudo apt install postgresql-15 postgresql-client-15 -y
   sudo systemctl enable postgresql
   sudo systemctl start postgresql
   sudo systemctl status postgresql
   ```

2. **Configure PostgreSQL**:
   Update the PostgreSQL configuration to listen on localhost, ensuring it uses the default port `5432`.
   ```bash
   sudo vim /etc/postgresql/15/main/postgresql.conf
   ```
   In `postgresql.conf`, set the following values:
   ```
   listen_addresses = 'localhost'
   port = 5432
   ```

3. **Modify pg_hba.conf**:
   Edit `pg_hba.conf` to set the authentication method if necessary.
   ```bash
   sudo vim /etc/postgresql/15/main/pg_hba.conf
   ```

4. **Restart PostgreSQL**:
   Restart the PostgreSQL service to apply configuration changes.
   ```bash
   sudo systemctl restart postgresql
   ```

5. **Install OpenSSH Server**:
   Install the OpenSSH server on the VM to enable SSH access.
   ```bash
   sudo apt update
   sudo apt install openssh-server
   sudo systemctl restart ssh
   ```

6. **Configure Firewall**:
   If the firewall is enabled, allow SSH traffic.
   ```bash
   sudo ufw allow ssh
   sudo ufw status
   ```

7. **Verify SSH Service**:
   Check that the SSH service is active.
   ```bash
   sudo systemctl status ssh
   ```

8. **Get VM IP Address**:
   Obtain the VM’s IP address, which will be used for SSH connections from the host.
   ```bash
   hostname -I
   ```

#### 3. Configure SSH Access from Host to VM

1. **Verify SSH Port Access**:
   Ensure that the SSH port on the VM is accessible by testing it from the host.
   ```bash
   nc -zv <VM_IP_ADDRESS> 22
   ```

2. **Copy SSH Key to VM**:
   Copy the SSH public key from the host machine to the VM for passwordless authentication.
   ```bash
   ssh-copy-id <username>@<VM_IP_ADDRESS>
   ```

3. **Test SSH Connection**:
   Verify the SSH connection by logging into the VM from the host.
   ```bash
   ssh <username>@<VM_IP_ADDRESS>
   ```

#### 4. Additional Configuration on VM

1. **Enable RSA Key Authentication**:
   Edit the SSH configuration on the VM to accept RSA keys, if required.
   ```bash
   sudo -i
   echo "PubkeyAcceptedKeyTypes=+ssh-rsa" >> /etc/ssh/sshd_config
   ```

2. **Restart SSH Service**:
   Restart the SSH service on the VM to apply the new settings.
   ```bash
   sudo systemctl restart sshd
   ```



