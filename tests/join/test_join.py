import os
import json
import difflib
import tempfile
import shutil
import unittest

from pg_perfbench.const import DEFAULT_REPORT_NAME, get_datetime_report, LogLevel
from pg_perfbench.join import (
    _load_reports,
    _load_compare_items,
    _compare_data,
    _compare_reports,
    _add_result,
    _merge_reports,
    join_reports,
    JOIN_TASKS_PATH
)
from pg_perfbench.report.processing import parse_json_in_order

# Define paths for the test reports directory and the dummy join_tasks file
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_REPORTS_DIR = os.path.join(TEST_DIR, "join_reports")
TEST_JOIN_TASKS_FILENAME = "dummy_join_tasks.json"
TEST_JOIN_TASKS_PATH = os.path.join(JOIN_TASKS_PATH, TEST_JOIN_TASKS_FILENAME)

# Create a dummy join_tasks file with a list of compare items
DUMMY_JOIN_TASKS = {
    "items": [
        "sections.system.reports.sysctl_vm.data",
        "sections.system.reports.sysctl_net_ipv4_tcp.data",
        "sections.system.reports.sysctl_net_ipv4_udp.data",
        "sections.system.reports.total_ram.data",
        "sections.db.reports.version_major.data"
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
        with open(TEST_JOIN_TASKS_PATH, "w", encoding="utf-8") as f:
            json.dump(DUMMY_JOIN_TASKS, f)

    @classmethod
    def tearDownClass(cls):
        """Remove the dummy join_tasks file after tests are completed."""
        if os.path.exists(TEST_JOIN_TASKS_PATH):
            os.remove(TEST_JOIN_TASKS_PATH)

    def test_01_load_reports_success(self):
        """Verify that _load_reports successfully loads JSON reports."""
        reference_report = "report_1.json"
        result = _load_reports(logger, TEST_REPORTS_DIR, reference_report)
        self.assertIsNotNone(result, "Expected non-None result from _load_reports")
        files, reports = result
        self.assertEqual(len(files), 5, "Expected 5 JSON report files")
        self.assertEqual(len(reports), 5, "Expected 5 report dictionaries")
        self.assertEqual(files[0], reference_report, "Reference report should be first in the list")

    def test_02_load_reports_invalid_directory(self):
        """Verify that _load_reports returns None for a nonexistent directory."""
        result = _load_reports(logger, "nonexistent_directory", "report_1.json")
        self.assertIsNone(result, "Expected None for an invalid directory")

    def test_03_load_compare_items_success(self):
        """Verify that _load_compare_items loads the compare items list."""
        items = _load_compare_items(logger, "task_compare_dbs_on_single_host.json")
        self.assertIsInstance(items, list, "Expected a list of compare items")
        self.assertEqual(len(items), 12, "Expected 12 compare items")

    def test_04_load_compare_items_invalid(self):
        """Verify that _load_compare_items returns None for a nonexistent file."""
        items = _load_compare_items(logger, "nonexistent_file.json")
        self.assertIsNone(items, "Expected None for a nonexistent join_tasks file")

    def test_05_compare_data_strings(self):
        """Test _compare_data with string inputs."""
        a = "line1\nline2"
        b = "line1\nline2"
        c = "line1\nline3"
        self.assertTrue(_compare_data(logger, a, b), "Expected True for identical strings")
        self.assertFalse(_compare_data(logger, a, c), "Expected False for differing strings")

    def test_06_compare_data_lists(self):
        """Test _compare_data with list inputs."""
        list1 = ["a", "b", "c"]
        list2 = ["a", "b", "c"]
        list3 = ["a", "b", "d"]
        self.assertTrue(_compare_data(logger, list1, list2), "Expected True for identical lists")
        self.assertFalse(_compare_data(logger, list1, list3), "Expected False for differing lists")

    def test_07_compare_reports_identical(self):
        """Ensure that _compare_reports identifies two identical reports as equal."""
        report_path = os.path.join(TEST_REPORTS_DIR, "report_1.json")
        with open(report_path, "r", encoding="utf-8") as f:
            report1 = json.load(f)
        with open(report_path, "r", encoding="utf-8") as f:
            report2 = json.load(f)
        self.assertTrue(_compare_reports(logger, report1, report2, []),
                        "Expected identical reports to compare as equal")

    def test_08_add_result(self):
        """Check that _add_result merges chart data, pgbench_outputs, and logs."""
        base = {
            "sections": {
                "result": {
                    "reports": {
                        "chart": {"data": {"series": [{"name": "", "data": [3, 2, 1]}]}},
                        "pgbench_outputs": {"data": [["base_report", [3, 2, 1]]]}
                    }
                }
            },
            "report_name": "base_report"
        }
        inc = {
            "sections": {
                "result": {
                    "reports": {
                        "chart": {"data": {"series": [{"name": "", "data": [1, 2, 3]}]}},
                        "pgbench_outputs": {"data": [4, 5, 6]},
                        "logs": {"data": "path/to/logs"}
                    }
                }
            },
            "report_name": "inc_report"
        }
        _add_result(base, inc)
        chart_series = base["sections"]["result"]["reports"]["chart"]["data"]["series"]
        pg_outputs = base["sections"]["result"]["reports"]["pgbench_outputs"]["data"]
        logs = base["sections"]["result"]["reports"].get("logs", {}).get("data")

        self.assertTrue(len(chart_series) > 1, "Expected more than one chart series after _add_result")
        self.assertTrue(len(pg_outputs) > 1, "Expected more than one pgbench_outputs entry after _add_result")
        self.assertTrue(len(logs) == 1, "Expected more than one logs entry after _add_result")

    def test_09_merge_reports(self):
        """Check that _merge_reports merges a list of reports correctly."""
        reports = []
        names = []
        for i in range(3):
            report = {
                "report_name": f"report_{i + 1}",
                "sections": {
                    "result": {
                        "reports": {
                            "chart": {"data": {"series": [{"name": "", "data": [i]}]}},
                            "pgbench_outputs": {"data": [i]}
                        }
                    }
                }
            }
            reports.append(report)
            names.append(f"report_{i + 1}")
        merged = _merge_reports(logger, names, reports, [])
        self.assertIsInstance(merged, dict, "Expected merged report to be a dictionary")
        self.assertEqual(merged.get("report_name"), "report_1",
                         "Expected the first report's name in the merged result")
        self.assertIn("header", merged, "Merged report should contain a 'header' field")

    def test_10_join_reports(self):
        """Test join_reports end-to-end with dummy arguments."""
        raw_args = ""
        joined_report = join_reports(
            raw_args=raw_args,
            join_tasks=TEST_JOIN_TASKS_FILENAME,
            reference_report="report_1.json",
            input_dir=TEST_REPORTS_DIR,
            report_name="joined_report",
            logger=logger
        )
        self.assertIsInstance(joined_report, dict, "Expected join_reports to return a dictionary")
        self.assertEqual(joined_report.get("report_name"), "joined_report",
                         "Expected report_name to match the provided name")
        self.assertIn("Comparison Reports", joined_report.get("description", ""),
                      "Expected description to contain 'Comparison Reports'")


if __name__ == "__main__":
    unittest.main()
