import unittest
from pathlib import Path
from pydantic import ValidationError

from pg_perfbench.const import WorkloadTypes
from pg_perfbench.context.schemes.workload import WorkloadDefault, PgbenchOptions, WorkloadCustom


class TestWorkloadCustom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print('\nTesting the WorkloadCustom context scheme')

    def test_valid_workload_custom_initialization(self):
        valid_params = {
            'workload_path': Path('/valid/path'),
            'options': PgbenchOptions(
                pgbench_clients=[10],
                pgbench_jobs=[1],
                pgbench_time=[100]
            ),
            'init_command': 'init command',
            'workload_command': 'workload command',
            'benchmark_type': WorkloadTypes.CUSTOM
        }
        workload = WorkloadCustom(**valid_params)
        self.assertEqual(workload.benchmark_type, WorkloadTypes.CUSTOM)

    def test_invalid_workload_custom_path(self):
        invalid_params = {
            'workload_path': Path('/'),
            'options': PgbenchOptions(),
            'init_command': '',
            'workload_command': ''
        }
        with self.assertRaises(ValidationError):
            WorkloadCustom(**invalid_params)


class TestWorkloadDefault(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print('\nTesting the WorkloadDefault context scheme')

    def test_valid_workload_default_initialization(self):
        valid_params = {
            'options': {
                'pgbench_clients': [10],
                'pgbench_jobs': [1],
                'pgbench_time': [100]
            },
            'init_command': 'init command',
            'workload_command': 'workload command',
            'benchmark_type': WorkloadTypes.DEFAULT
        }
        workload = WorkloadDefault(**valid_params)
        self.assertEqual(workload.benchmark_type, WorkloadTypes.DEFAULT)


if __name__ == '__main__':
    unittest.main()
