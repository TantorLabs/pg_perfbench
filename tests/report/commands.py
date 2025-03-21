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


class MockLogger:
    """A simple mock logger for testing."""

    def debug(self, message: str) -> None:
        pass

    def info(self, message: str) -> None:
        pass

    def error(self, message: str) -> None:
        pass

    def warning(self, message: str) -> None:
        pass


class TestReportCommands(IsolatedAsyncioTestCase):
    """Tests for functions in pg_perfbench.report.commands."""

    def setUp(self) -> None:
        """Create a temporary directory and script file for testing."""
        self.logger = MockLogger()
        self.temp_dir = tempfile.mkdtemp()
        self.script_path = os.path.join(self.temp_dir, "script.sh")
        with open(self.script_path, "w", encoding="utf-8") as f:
            f.write("#!/bin/bash\necho 'script ok'")

    def tearDown(self) -> None:
        """Remove the temporary directory and its contents."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_script_text_ok(self) -> None:
        """Check that get_script_text reads a valid script file correctly."""
        content = get_script_text(self.script_path)
        self.assertIn("script ok", content, "Expected 'script ok' in script content.")

    def test_get_script_text_not_found(self) -> None:
        """Check that get_script_text raises FileNotFoundError for an invalid path."""
        with self.assertRaises(FileNotFoundError):
            get_script_text("/no/such/path.sh")

    async def test_run_shell_command_plain_text(self) -> None:
        """Check that run_shell_command processes a 'plain_text' item_type successfully."""
        class MockConn:
            """A mock connection object simulating run_command behavior."""
            async def run_command(self, cmd, check):
                return "command success"

        item = {
            "shell_command_file": "fake_cmd.sh",
            "item_type": "plain_text"
        }

        # Patch get_script_text to return a dummy script content
        with patch("pg_perfbench.report.commands.get_script_text", return_value="echo 'OK'"):
            await run_shell_command(self.logger, MockConn(), item)
            self.assertEqual(
                item["data"],
                "command success",
                "Expected 'command success' in item['data']"
            )

    async def test_run_sql_command_no_file(self) -> None:
        """Check that run_sql_command handles missing 'sql_command_file' gracefully."""
        class MockDB:
            """A mock database connection object simulating SQL fetch methods."""
            async def fetch(self, sql):
                return []

            async def fetchval(self, sql):
                return "val"

        item = {
            "item_type": "plain_text"
            # Missing 'sql_command_file'
        }
        await run_sql_command(self.logger, MockDB(), item)
        # Because no 'sql_command_file' was provided, 'data' should not be set
        self.assertNotIn("data", item, "Expected no 'data' key in item due to missing 'sql_command_file'")
