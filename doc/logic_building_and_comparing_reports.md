# Generating report in `collect-sys-info` mode
> **Note**: In this mode, only the 'system' section is populated, and there is no access to collect database information.

### Common parameters
| Parameter       | Description                                                               |
|-----------------|---------------------------------------------------------------------------|
| `--mode='collect-sys-info'`       | The execution mode of pg_perfbench should be set to `'collect-sys-info'`    |
| `--log-level`   | Application logging level: `info`, `debug`, `error` (default - `info`) |
| `--report-name` | Report name(optional)                                                  |

### Docker container parameters 
| Parameter           | Description                                                            |
|---------------------|------------------------------------------------------------------------|
| `--container-name` | Name of creating container                                             |

<br>For example, the following parameter group can be configured:
```
python -m pg_perfbench --mode=collect-sys-info \
--log-level=debug \
--container-name=cntr_test
```

### Remote host parameters via SSH
| Parameter           | Description                                                               |
|---------------------|---------------------------------------------------------------------------|
| `--ssh-port`        | Port for ssh connection (default: 22)                            |
| `--ssh-host`        | IP address of the remote server                                  |
| `--ssh-key`         | Path to the ssh connection private key file (must be configured) |

<br>For example, the following parameter group can be configured:
```
python -m pg_perfbench --mode=collect-sys-info  \
--log-level=debug   \
--ssh-port=22   \
--ssh-key=/path_to/private_key \
--ssh-host=10.177.199.199
```
### Template configuration
You can configure the JSON report template file `pg_perfbench/reports/templates/sys_info_report_struct.json`.
Add or remove reports of the following types:

- "shell_command_file" - a report with the result of executing the specified bash script relative to the database host in the `pg_perfbench/commands/bash_commands` directory:

&emsp; &emsp;- output type `plain_text`:

```
"example_bash_report": {
  "header": "example_bash_header",
  "state": "collapsed",
  "item_type": "plain_text",
  "shell_command_file": "bash_example.sh",
  "data": ""
}
```

&emsp; &emsp;- output type `table`:

> **Note**: this bash script should return data in the form of an array of objects on the basis of which the table is built, as an example you can see the output of lshw in the report pg_perfbench/reports/templates/report_struct.json
```
"example_bash_report": {
  "header": "example_bash_header",
  "state": "collapsed",
  "item_type": "table",
  "shell_command_file": "bash_example.sh", <----- 
  "theader": [],
  "data": []
}
```

# Generating report in `collect-db-info` mode

> **Note**: In this mode, only the 'db' section is populated.

### Common parameters
| Parameter      | Description                                                               |
|----------------|---------------------------------------------------------------------------|
| `--mode='collect-db-info'`    | The execution mode of pg_perfbench should be set to `'collect-db-info'`    |
| `--log-level`  | Application logging level: `info`, `debug`, `error` (default - `info`) |
| `--report-name` | Report name(optional)                                                  |
| `--pg-port`       | Forwarded port (default `5432`, relative to the current host)        |
| `--pg-host`       | Forwarded address (default `127.0.0.1`, relative to the current host) |
| `--pg-user`       | User of database (must be configured or set "postgres")              |
| `--pg-database`   | Database used for testing                                            |
| `--pg-user-password` | Password for database connection (optional)                          |
| `--pg-data-path`  | Path to the PostgreSQL data directory (relative to the database host) |
| `--pg-bin-path`   | Path to the PostgreSQL bin directory (relative to the database host) |
| `--collect-pg-logs` | Enable database logging (logging must be configured by the user)     |
| `--custom-config`  | Use custom PostgreSQL config                                         |

### Docker container parameters 
| Parameter           | Description                                                            |
|---------------------|------------------------------------------------------------------------|
| `--container-name` | Name of creating container                                             |

<br>For example, the following parameter group can be configured:
```
python -m pg_perfbench --mode=collect-db-info   \
--log-level=debug   \
--container-name=cntr_test    \
--pg-host=127.0.0.1 \
--pg-port=5435  \
--pg-user=postgres  \
--pg-user-password=test \
--pg-database=tdb   \
--pg-data-path=/var/lib/postgresql/data \
--pg-bin-path=/usr/lib/postgresql/15/bin
```
### Remote host parameters via SSH
| Parameter           | Description                                                               |
|---------------------|---------------------------------------------------------------------------|
| `--ssh-port`        | Port for ssh connection (default: 22)                            |
| `--ssh-host`        | IP address of the remote server                                  |
| `--ssh-key`         | Path to the ssh connection private key file (must be configured) |

<br>For example, the following parameter group can be configured:
```
python -m pg_perfbench --mode=collect-db-info \
--log-level=debug \
--ssh-port=22 \
--ssh-key=/path_to/private_key \
--ssh-host=10.199.199.199 \
--remote-pg-host=127.0.0.1  \
--remote-pg-port=5432  \
--pg-host=127.0.0.1  \
--pg-port=5435  \
--pg-user=postgres  \
--pg-user-password=pswd  \
--pg-database=tdb  \
--pg-data-path=/var/lib/postgresql/16/data  \
--pg-bin-path=/opt/postgresql/db/16/bin
```
### Template configuration
You can configure the JSON report template file `pg_perfbench/reports/templates/db_info_report_struct.json`.
Add or remove reports of the following types:
- "sql_command_file" - a report with the result of executing the specified SQL script in the database located in the `pg_perfbench/commands/sql_commands` directory, for example:

&emsp; &emsp;- output type `plain_text`:
```
"example_sql_report": {
    "header": "example_sql_header",
    "state": "collapsed",
    "item_type": "plain_text",
    "sql_command_file": "sql_example.sql",
    "data": ""
}
```
&emsp; &emsp;- output type `table`:
> **Note**: This sql script should return a tabular form of the data. Examples can be found in pg_perfbench/reports/templates/report_struct.json
```
"example_bash_report": {
  "header": "example_bash_header",
  "state": "collapsed",
  "item_type": "table",
  "shell_command_file": "sql_example.sql", <----- 
  "theader": [],
  "data": []
}
```

# Generating report in `collect-all-info` mode
> **Note**: In this mode, the 'system' and 'db' sections are filled.
### Common parameters
| Parameter      | Description                                                               |
|----------------|---------------------------------------------------------------------------|
| `--mode='collect-all-info'`    | The execution mode of pg_perfbench should be set to `'collect-all-info'`    |
| `--log-level`  | Application logging level: `info`, `debug`, `error` (default - `info`) |
| `--report-name` | Report name(optional)                                                  |
| `--pg-port`       | Forwarded port (default `5432`, relative to the current host)        |
| `--pg-host`       | Forwarded address (default `127.0.0.1`, relative to the current host) |
| `--pg-user`       | User of database (must be configured or set "postgres")              |
| `--pg-database`   | Database used for testing                                            |
| `--pg-user-password` | Password for database connection (optional)                          |
| `--pg-data-path`  | Path to the PostgreSQL data directory (relative to the database host) |
| `--pg-bin-path`   | Path to the PostgreSQL bin directory (relative to the database host) |
| `--collect-pg-logs` | Enable database logging (logging must be configured by the user)     |
| `--custom-config`  | Use custom PostgreSQL config                                         |

### Docker container parameters 
| Parameter           | Description                                                            |
|---------------------|------------------------------------------------------------------------|

| `--container-name` | Name of creating container                                             |


<br>For example, the following parameter group can be configured:
```
python -m pg_perfbench --mode=collect-db-info   \
--log-level=debug   \
--container-name=cntr_test    \
--pg-host=127.0.0.1 \
--pg-port=5435  \
--pg-user=postgres  \
--pg-user-password=test \
--pg-database=tdb   \
--pg-data-path=/var/lib/postgresql/data \
--pg-bin-path=/usr/lib/postgresql/15/bin
```

### Remote host parameters via SSH
| Parameter           | Description                                                               |
|---------------------|---------------------------------------------------------------------------|
| `--ssh-port`        | Port for ssh connection (default: 22)                            |
| `--ssh-host`        | IP address of the remote server                                  |
| `--ssh-key`         | Path to the ssh connection private key file (must be configured) |

<br>For example, the following parameter group can be configured:
```
python -m pg_perfbench --mode=collect-db-info \
--log-level=debug \
--ssh-port=22 \
--ssh-key=/path_to/private_key \
--ssh-host=10.199.199.199 \
--remote-pg-host=127.0.0.1  \
--remote-pg-port=5432  \
--pg-host=127.0.0.1  \
--pg-port=5435  \
--pg-user=postgres  \
--pg-user-password=pswd  \
--pg-database=tdb  \
--pg-data-path=/var/lib/postgresql/16/data  \
--pg-bin-path=/opt/postgresql/db/16/bin
```
### Template configuration
You can configure the JSON report template file `pg_perfbench/reports/templates/all_info_report_struct.json`.
Add or remove reports of the following types:

- "shell_command_file" - a report with the result of executing the specified bash script relative to the database host in the `pg_perfbench/commands/bash_commands` directory:

&emsp; &emsp;- output type `plain_text`:

```
"example_bash_report": {
  "header": "example_bash_header",
  "state": "collapsed",
  "item_type": "plain_text",
  "shell_command_file": "bash_example.sh",
  "data": ""
}
```

&emsp; &emsp;- output type `table`:

> **Note**: this bash script should return data in the form of an array of objects on the basis of which the table is built, as an example you can see the output of lshw in the report pg_perfbench/reports/templates/report_struct.json
```
"example_bash_report": {
  "header": "example_bash_header",
  "state": "collapsed",
  "item_type": "table",
  "shell_command_file": "bash_example.sh", <----- 
  "theader": [],
  "data": []
}
```
- "sql_command_file" - a report with the result of executing the specified SQL script in the database located in the `pg_perfbench/commands/sql_commands` directory, for example:

&emsp; &emsp;- output type `plain_text`:
```
"example_sql_report": {
    "header": "example_sql_header",
    "state": "collapsed",
    "item_type": "plain_text",
    "sql_command_file": "sql_example.sql",
    "data": ""
}
```
&emsp; &emsp;- output type `table`:
> **Note**: This sql script should return a tabular form of the data. Examples can be found in pg_perfbench/reports/templates/report_struct.json
```
"example_bash_report": {
  "header": "example_bash_header",
  "state": "collapsed",
  "item_type": "table",
  "shell_command_file": "sql_example.sql", <----- 
  "theader": [],
  "data": []
}
```
# Generating report in `benchmark` mode
> **Note**: In this template, the following sections are also included:<br>
`benchmark`: This section displays the user application configuration, detailed benchmark configuration, a detailed description of the database schema for load, and load scripts.<br>
`result`: This section shows the detailed output of the pgbench benchmark results and the load iteration chart.<br>
These sections cannot be modified.

The description of the parameters is located on the main [page](../README.md#configuring-pg_perfbench-in-benchmark-mode).
### Template configuration
You can configure the JSON report template file `pg_perfbench/reports/templates/report_struct.json`.
Add or remove reports of the following types:

- "shell_command_file" - a report with the result of executing the specified bash script relative to the database host in the `pg_perfbench/commands/bash_commands` directory:

&emsp; &emsp;- output type `plain_text`:

```
"example_bash_report": {
  "header": "example_bash_header",
  "state": "collapsed",
  "item_type": "plain_text",
  "shell_command_file": "bash_example.sh",
  "data": ""
}
```

&emsp; &emsp;- output type `table`:

> **Note**: this bash script should return data in the form of an array of objects on the basis of which the table is built, as an example you can see the output of lshw in the report pg_perfbench/reports/templates/report_struct.json
```
"example_bash_report": {
  "header": "example_bash_header",
  "state": "collapsed",
  "item_type": "table",
  "shell_command_file": "bash_example.sh", <----- 
  "theader": [],
  "data": []
}
```
- "sql_command_file" - a report with the result of executing the specified SQL script in the database located in the `pg_perfbench/commands/sql_commands` directory, for example:

&emsp; &emsp;- output type `plain_text`:
```
"example_sql_report": {
    "header": "example_sql_header",
    "state": "collapsed",
    "item_type": "plain_text",
    "sql_command_file": "sql_example.sql",
    "data": ""
}
```
&emsp; &emsp;- output type `table`:
> **Note**: This sql script should return a tabular form of the data. Examples can be found in pg_perfbench/reports/templates/report_struct.json
```
"example_bash_report": {
  "header": "example_bash_header",
  "state": "collapsed",
  "item_type": "table",
  "shell_command_file": "sql_example.sql", <----- 
  "theader": [],
  "data": []
}
```
### Logic of Report Information Collection
![image lost](collectiong_report_info.png "user workload scenarios")


# Generating report in `join` mode
In this mode, single workload reports can be compared based on selected categories, which can be configured manually.

#### Join mode options
| Option                     | Description                                               |
|----------------------------|-----------------------------------------------------------|
| `--report-name`   | Report name                                                                                                                                |
| `--join-task`              | Criteria for comparing reports                            |
| `--reference-report`       | Criteria for comparing reports                            |
| `--input-dir`              | Reports directory                                         |



#### Example Configuration
```bash
python3.11 -m pg_perfbench --mode=join \
--join-task=task_compare_dbs_on_single_host.json \
--reference-report=benchmark_report_2024-12-03_12:37:28.json \
--input-dir=/path_to/reports
```

In the example above:
 - **pg_perfbench** compares reports located in the directory `--input-dir=/path_to/reports`.
 - The reference comparison report can be set using the `--reference-report` argument, by default the first one alphabetically is used.
 - `--join-task` - comparison fields that must match between the compared reports, can be configured manually in ***.json** format according to the schema:

 ```bash
 {
     "description": "......",
     "items": [
         "section.report.data",
         "section.report.data",
         "section.report.data",
         ........
     ]
 }
```
- The final comparison report `join_report.json` is saved `report` directory.

![image lost](join_mode_logic.png "user workload scenarios")
