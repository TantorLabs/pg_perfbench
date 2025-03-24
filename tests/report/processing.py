import unittest
import tempfile
import shutil
import os
import json
import pathlib
from unittest.mock import MagicMock, patch

from pg_perfbench.report.processing import (
    get_report_structure,
    parse_json_in_order,
    save_report,
    _save_json_report,
    dump_updated_json
)


class TestReportProcessing(unittest.TestCase):
    """Tests for functions in pg_perfbench.report.processing."""

    def setUp(self) -> None:
        """Create a temporary directory and a simple JSON file for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_json_path = os.path.join(self.temp_dir, "test_report.json")
        with open(self.test_json_path, "w", encoding="utf-8") as f:
            json.dump({"test_key": "test_value"}, f)

    def tearDown(self) -> None:
        """Remove the temporary directory and its contents."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_report_structure_valid(self) -> None:
        """Check that get_report_structure returns the data for a valid JSON file."""
        data = get_report_structure(self.test_json_path)
        self.assertEqual(data["test_key"], "test_value")

    def test_get_report_structure_not_found(self) -> None:
        """Check that get_report_structure raises FileNotFoundError if the file does not exist."""
        with self.assertRaises(FileNotFoundError):
            get_report_structure(os.path.join(self.temp_dir, "no_such.json"))

    def test_get_report_structure_invalid_data(self) -> None:
        """
        Check that get_report_structure raises ValueError
        if the JSON data is not a dictionary.
        """
        path_non_dict = os.path.join(self.temp_dir, "non_dict.json")
        with open(path_non_dict, "w", encoding="utf-8") as f:
            json.dump(["list_item"], f)
        with self.assertRaises(ValueError):
            get_report_structure(path_non_dict)

    def test_parse_json_in_order_empty(self) -> None:
        """Check that parse_json_in_order returns empty steps when no sections are present."""
        steps, report = parse_json_in_order({"foo": "bar"})
        self.assertEqual(len(steps), 0)
        self.assertEqual(report, {"foo": "bar"})

    def test_parse_json_in_order_valid(self) -> None:
        """Check that parse_json_in_order identifies shell/ python commands in the report structure."""
        report_data = {
            "sections": {
                "setup": {
                    "reports": {
                        "command1": {
                            "shell_command_file": "do_something.sh"
                        },
                        "command2": {
                            "python_command": "args"
                        }
                    }
                }
            }
        }
        steps, report = parse_json_in_order(report_data)
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0]["cmd_type"], "shell_command")
        self.assertEqual(steps[1]["cmd_type"], "python_command")

    @patch(
        "pg_perfbench.report.processing.REPORT_FOLDER",
        new_callable=lambda: pathlib.Path(tempfile.mkdtemp())
    )
    def test_save_report_missing_report_name(self, mock_path: pathlib.Path) -> None:
        """
        Check that save_report raises ValueError if the report dictionary
        does not contain a 'report_name' key.
        """
        with self.assertRaises(ValueError):
            save_report( MagicMock(), {})

    def test_save_json_report(self) -> None:
        """Check that _save_json_report writes JSON data to the specified path."""
        data = {"some": "data"}
        out_path = os.path.join(self.temp_dir, "out.json")
        _save_json_report(out_path, data)
        with open(out_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertEqual(loaded, data)

    def test_dump_updated_json(self) -> None:
        """Check that dump_updated_json writes JSON data as expected."""
        sample = {"k": "v"}
        out_file = os.path.join(self.temp_dir, "dump.json")
        dump_updated_json(sample, out_file)
        with open(out_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertEqual(loaded, sample)


if __name__ == "__main__":
    unittest.main()
