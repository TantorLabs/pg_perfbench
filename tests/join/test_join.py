import os
import json
import unittest

from pg_perfbench.join import ReportJoiner, JOIN_TASKS_PATH

# Define paths for the test reports directory and the dummy join_tasks file
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_REPORTS_DIR = os.path.join(TEST_DIR, 'join_reports')
TEST_JOIN_TASKS_FILENAME = 'dummy_join_tasks.json'
TEST_JOIN_TASKS_PATH = os.path.join(JOIN_TASKS_PATH, TEST_JOIN_TASKS_FILENAME)

# Create a dummy join_tasks file with a list of compare items
DUMMY_JOIN_TASKS = {
    'items': [
        'sections.system.reports.sysctl_vm.data',
        'sections.system.reports.sysctl_net_ipv4_tcp.data',
        'sections.system.reports.sysctl_net_ipv4_udp.data',
        'sections.system.reports.total_ram.data',
        'sections.db.reports.version_major.data',
    ]
}


class MockLogg:
    """A simple mock logger for testing."""

    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def error(self, msg):
        pass

    def warning(self, msg):
        pass


logger = MockLogg()


class TestReportProcessing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Write a dummy join_tasks file in the test directory."""
        os.makedirs(JOIN_TASKS_PATH, exist_ok=True)
        with open(TEST_JOIN_TASKS_PATH, 'w', encoding='utf-8') as f:
            json.dump(DUMMY_JOIN_TASKS, f)

    @classmethod
    def tearDownClass(cls):
        """Remove the dummy join_tasks file after tests are completed."""
        if os.path.exists(TEST_JOIN_TASKS_PATH):
            os.remove(TEST_JOIN_TASKS_PATH)

    def test_01load_reports_success(self):
        """Verify that load_reports successfully loads JSON reports."""
        reference_report = 'report_1.json'
        result = ReportJoiner.load_reports(
            logger, TEST_REPORTS_DIR, reference_report
        )
        self.assertIsNotNone(
            result, 'Expected non-None result from load_reports'
        )
        files, reports = result
        self.assertEqual(len(files), 5, 'Expected 5 JSON report files')
        self.assertEqual(len(reports), 5, 'Expected 5 report dictionaries')
        self.assertEqual(
            files[0],
            reference_report,
            'Reference report should be first in the list',
        )

    def test_02load_reports_invalid_directory(self):
        """Verify that load_reports returns None for a nonexistent directory."""
        result = ReportJoiner.load_reports(
            logger, 'nonexistent_directory', 'report_1.json'
        )
        self.assertIsNone(result, 'Expected None for an invalid directory')

    def test_03load_compare_items_success(self):
        """Verify that load_compare_items loads the compare items list."""
        items = ReportJoiner.load_compare_items(
            logger, 'task_compare_dbs_on_single_host.json'
        )
        self.assertIsInstance(items, list, 'Expected a list of compare items')
        self.assertEqual(len(items), 12, 'Expected 12 compare items')

    def test_04load_compare_items_invalid(self):
        """Verify that load_compare_items returns None for a nonexistent file."""
        items = ReportJoiner.load_compare_items(
            logger, 'nonexistent_file.json'
        )
        self.assertIsNone(
            items, 'Expected None for a nonexistent join_tasks file'
        )

    def test_05compare_data_strings(self):
        """Test compare_data with string inputs."""
        a = 'line1\nline2'
        b = 'line1\nline2'
        c = 'line1\nline3'
        self.assertTrue(
            ReportJoiner.compare_data(logger, a, b),
            'Expected True for identical strings',
        )
        self.assertFalse(
            ReportJoiner.compare_data(logger, a, c),
            'Expected False for differing strings',
        )

    def test_06compare_data_lists(self):
        """Test compare_data with list inputs."""
        list1 = ['a', 'b', 'c']
        list2 = ['a', 'b', 'c']
        list3 = ['a', 'b', 'd']
        self.assertTrue(
            ReportJoiner.compare_data(logger, list1, list2),
            'Expected True for identical lists',
        )
        self.assertFalse(
            ReportJoiner.compare_data(logger, list1, list3),
            'Expected False for differing lists',
        )

    def test_07compare_reports_identical(self):
        """Ensure that compare_reports identifies two identical reports as equal."""
        report_path = os.path.join(TEST_REPORTS_DIR, 'report_1.json')
        with open(report_path, 'r', encoding='utf-8') as f:
            report1 = json.load(f)
        with open(report_path, 'r', encoding='utf-8') as f:
            report2 = json.load(f)
        self.assertTrue(
            ReportJoiner.compare_reports(logger, report1, report2, []),
            'Expected identical reports to compare as equal',
        )

    def test_08add_result(self):
        """Check that add_result merges chart data, pgbench_outputs, and logs."""
        base = {
            'sections': {
                'result': {
                    'reports': {
                        'chart': {
                            'data': {
                                'series': [{'name': '', 'data': [3, 2, 1]}]
                            }
                        },
                        'pgbench_outputs': {
                            'data': [['base_report', [3, 2, 1]]]
                        },
                    }
                }
            },
            'report_name': 'base_report',
        }
        inc = {
            'sections': {
                'result': {
                    'reports': {
                        'chart': {
                            'data': {
                                'series': [{'name': '', 'data': [1, 2, 3]}]
                            }
                        },
                        'pgbench_outputs': {'data': [4, 5, 6]},
                        'logs': {'data': 'path/to/logs'},
                    }
                }
            },
            'report_name': 'inc_report',
        }
        ReportJoiner.add_result(base, inc)
        chart_series = base['sections']['result']['reports']['chart']['data'][
            'series'
        ]
        pg_outputs = base['sections']['result']['reports']['pgbench_outputs'][
            'data'
        ]
        logs = (
            base['sections']['result']['reports'].get('logs', {}).get('data')
        )

        self.assertTrue(
            len(chart_series) > 1,
            'Expected more than one chart series after add_result',
        )
        self.assertTrue(
            len(pg_outputs) > 1,
            'Expected more than one pgbench_outputs entry after add_result',
        )
        self.assertTrue(
            len(logs) == 1,
            'Expected more than one logs entry after add_result',
        )

    def test_09merge_reports(self):
        """Check that merge_reports merges a list of reports correctly."""
        reports = []
        names = []
        for i in range(3):
            report = {
                'report_name': f'report_{i + 1}',
                'sections': {
                    'result': {
                        'reports': {
                            'chart': {
                                'data': {'series': [{'name': '', 'data': [i]}]}
                            },
                            'pgbench_outputs': {'data': [i]},
                        }
                    }
                },
            }
            reports.append(report)
            names.append(f'report_{i + 1}')
        merged = ReportJoiner.merge_reports(logger, names, reports, [])
        self.assertIsInstance(
            merged, dict, 'Expected merged report to be a dictionary'
        )
        self.assertEqual(
            merged.get('report_name'),
            'report_1',
            "Expected the first report's name in the merged result",
        )
        self.assertIn(
            'header', merged, "Merged report should contain a 'header' field"
        )

    def test_10_join_reports(self):
        """Test join_reports end-to-end with dummy arguments."""
        raw_args = ''
        joined_report = ReportJoiner.join_reports(
            raw_args=raw_args,
            join_tasks=TEST_JOIN_TASKS_FILENAME,
            reference_report='report_1.json',
            input_dir=TEST_REPORTS_DIR,
            report_name='joined_report',
            logger=logger,
        )
        self.assertIsInstance(
            joined_report, dict, 'Expected join_reports to return a dictionary'
        )
        self.assertEqual(
            joined_report.get('report_name'),
            'joined_report',
            'Expected report_name to match the provided name',
        )
        self.assertIn(
            'Comparison Reports',
            joined_report.get('description', ''),
            "Expected description to contain 'Comparison Reports'",
        )


if __name__ == '__main__':
    unittest.main()
