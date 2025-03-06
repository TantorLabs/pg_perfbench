import unittest
from pg_perfbench.benchmark import (
    get_pgbench_results,
    get_filled_load_commands,
    load_iterations_config
)

class TestBenchmarkFunctions(unittest.TestCase):
    def test_get_pgbench_results(self):
        out = """
        number of clients: 10
        duration: 60
        number of transactions actually processed: 150/150
        latency average = 13.2 ms
        initial connection time = 2.5 ms
        tps = 100.5
        """
        results = get_pgbench_results(out)
        self.assertEqual(results, [10, 60, 150, 13.2, 2.5, 100.5])

    def test_get_filled_load_commands(self):
        db_conf = {"host": "127.0.0.1"}
        workload_conf = {
            "init_command": "init ARG_HOST",
            "workload_command": "work ARG_PGBENCH_ITER",
        }
        result = get_filled_load_commands(db_conf, workload_conf, "pgbench_iter", 50)
        self.assertEqual(len(result), 2)
        self.assertIn("127.0.0.1", result[0])
        self.assertIn("50", result[1])

    def test_load_iterations_config_empty(self):
        res = load_iterations_config({}, {})
        self.assertEqual(res, [])