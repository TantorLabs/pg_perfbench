import unittest
import tempfile
import shutil
import os
from unittest.mock import patch, MagicMock
from unittest import IsolatedAsyncioTestCase
from pg_perfbench.report.commands import (
    get_script_text,
    run_shell_command,
    run_sql_command
)


class TestReportCommands(IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.script_path = os.path.join(self.temp_dir, "script.sh")
        with open(self.script_path, "w", encoding="utf-8") as f:
            f.write("#!/bin/bash\necho 'script ok'")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_script_text_ok(self):
        content = get_script_text(self.script_path)
        self.assertIn("script ok", content)

    def test_get_script_text_not_found(self):
        with self.assertRaises(FileNotFoundError):
            get_script_text("/no/such/path.sh")

    async def test_run_shell_command_plain_text(self):
        class MockConn:
            async def run_command(self, cmd):
                return "command success"

        item = {
            "shell_command_file": "fake_cmd.sh",
            "item_type": "plain_text"
        }
        with patch("pg_perfbench.report_commands.get_script_text", return_value="echo 'OK'"):
            await run_shell_command(MockConn(), item)
            self.assertEqual(item["data"], "command success")

    async def test_run_sql_command_no_file(self):
        class MockDB:
            async def fetch(self, sql):
                return []

            async def fetchval(self, sql):
                return "val"

        item = {
            "item_type": "plain_text"
        }
        await run_sql_command(MockDB(), item)
        self.assertNotIn("data", item)
