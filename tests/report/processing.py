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
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_json_path = os.path.join(self.temp_dir, 'test_report.json')
        with open(self.test_json_path, 'w', encoding='utf-8') as f:
            json.dump({"test_key": "test_value"}, f)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_report_structure_valid(self):
        data = get_report_structure(self.test_json_path)
        self.assertEqual(data["test_key"], "test_value")

    def test_get_report_structure_not_found(self):
        with self.assertRaises(FileNotFoundError):
            get_report_structure(os.path.join(self.temp_dir, 'no_such.json'))

    def test_get_report_structure_invalid_data(self):
        path_non_dict = os.path.join(self.temp_dir, 'non_dict.json')
        with open(path_non_dict, 'w', encoding='utf-8') as f:
            json.dump(["list_item"], f)
        with self.assertRaises(ValueError):
            get_report_structure(path_non_dict)

    def test_parse_json_in_order_empty(self):
        steps, report = parse_json_in_order({"foo": "bar"})
        self.assertEqual(len(steps), 0)
        self.assertEqual(report, {"foo": "bar"})

    def test_parse_json_in_order_valid(self):
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

    @patch("pg_perfbench.report_processing.REPORT_FOLDER", new_callable=lambda: pathlib.Path(tempfile.mkdtemp()))
    def test_save_report_missing_report_name(self, mock_path):
        with self.assertRaises(ValueError):
            save_report({}, MagicMock())

    def test_save_json_report(self):
        data = {"some": "data"}
        out_path = os.path.join(self.temp_dir, 'out.json')
        _save_json_report(out_path, data)
        with open(out_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        self.assertEqual(loaded, data)

    def test_dump_updated_json(self):
        sample = {"k": "v"}
        out_file = os.path.join(self.temp_dir, 'dump.json')
        dump_updated_json(sample, out_file)
        with open(out_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        self.assertEqual(loaded, sample)
