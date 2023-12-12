import unittest
from pg_perfbench.context.schemas.workload import WorkloadDefault


class TestWorkloads(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('\ntest_workload module')

    @staticmethod
    def workload_params() -> dict[str, str]:
        return {
            'benchmark_type': 'default',
            'options': {'pgbench_clients': [10, 15, 20], 'pgbench_time': [6]},
            'init_command': 'ARG_PGBENCH_PATH -i --scale=10 --foreign-keys -p ARG_PG_PORT '
            '-h ARG_PG_HOST -U postgres ARG_PG_DATABASE',
            'workload_command': 'ARG_PGBENCH_PATH -p ARG_PG_PORT -h ARG_PG_HOST -U '
            'postgres ARG_PG_DATABASE -c ARG_PGBENCH_CLIENTS -j 20 '
            '-T 5 --no-vacuum',
            'pgbench_path': '/usr/bin/pgbench',
            'psql_path': '/usr/bin/psql'
        }

    def test_workload_common(self):
        workload_params = self.workload_params()
        data = WorkloadDefault(**workload_params)
        self.assertEqual(data.options.pgbench_clients, [10, 15, 20])
        self.assertEqual(data.options.pgbench_jobs, [])
        self.assertEqual(data.options.pgbench_time, [6])
