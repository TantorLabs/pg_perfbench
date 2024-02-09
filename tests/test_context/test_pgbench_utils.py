import pytest

from pg_perfbench.const import WorkloadTypes
from pg_perfbench.context.schemes.db import DBParameters
from pg_perfbench.context.schemes.workload import WorkloadDefault


ssh_connection_params = {
    'ssh_host': '127.0.0.1',
    'ssh_port': 22,
    'ssh_user': 'postgres',
    'ssh_key': 'your_ssh_key',
    'tunnel': {
        'local': {
            'tunnel_local_host': 'localhost',
            'tunnel_local_port': 12345,
        },
        'remote': {
            'tunnel_remote_host': '127.0.0.1',
            'tunnel_remote_port': 5432,
        },
    },
}

raw_workload_params = {
    "benchmark_type": WorkloadTypes.DEFAULT,
    "options": {
        "pgbench_clients": [10, 20],
        "pgbench_jobs": [1, 2],
        "pgbench_time": [60, 120]
    },
    'pgbench_path': '/usr/bin/pgbench',
    'psql_path': '/usr/bin/psql',
    'init_command': 'pgbench -i --scale=10 --foreign-keys -p 5432 -h 127.0.0.1 -U '
    'postgres ARG_PG_DATABASE',
    'workload_command': 'pgbench -p 5432 -h 127.0.0.1 -U postgres ARG_PG_DATABASE'
    ' -c ARG_PGBENCH_CLIENTS -j 20 -T 10 --no-vacuum'
}

raw_db_params = {
    'pg_host': '127.0.0.1',
    'pg_port': '5432',
    'pg_user': 'test_user',
    'pg_database': 'example_database',
    'pg_user_password': 'test_user_password',
    'pg_data_path': 'etc/postgresql/15/main',
    'pg_bin_path': 'usr/lib/postgresql/15/bin',
}


def test_collection_of_pgbench_commands():
    db_params = DBParameters(**raw_db_params)
    workload_params = WorkloadDefault(**raw_workload_params)
    assert db_params
    assert workload_params
