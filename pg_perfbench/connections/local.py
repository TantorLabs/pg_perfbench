import asyncio
import os
import shutil
import tarfile
from typing import Optional
from types import TracebackType


class LocalConnection:
    def __init__(self, env) -> None:
        self.conn_params: Optional[dict] = None
        self.process: Optional[asyncio.subprocess.Process] = None
        self.logger = None

        self.env = os.environ.copy()
        for key, value in env.items():
            self.env[key] = value

    async def start(self) -> None:
        if self.logger:
            self.logger.info("LocalConnection started (no persistent process).")

    async def close(self) -> None:
        if self.logger:
            self.logger.info("LocalConnection closed.")

    async def run_command(self, cmd: str, check: bool = False) -> str:
        if not cmd.strip():
            if self.logger:
                self.logger.warning("Attempting to run an empty command string.")
            return ''

        try:
            if 'start' in cmd:
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                    shell=True,
                    limit=262144,
                    env=self.env
                )
                await asyncio.sleep(1)
                return ''
            else:
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    shell=True,
                    limit=262144,
                    env=self.env
                )
        except Exception as e:
            raise RuntimeError(f"Failed to start subprocess for command: {cmd}\nError: {str(e)}")

        stdout, stderr = await process.communicate()
        if process.returncode != 0 and check:
            if self.logger:
                self.logger.error(f"Command '{cmd}' failed for Local connection with exit code {process.returncode}.")
                self.logger.error(f"STDERR: {stderr.decode('utf-8', errors='replace')}")
            if check:
                raise RuntimeError(f"Command '{cmd}' returned non-zero exit code.")

        return stdout.decode('utf-8', errors='replace')

    async def send_pg_config_file(self, local_config_path: str, remote_data_dir: str) -> str:
        # Check if the local file exists
        if not os.path.exists(local_config_path):
            raise FileNotFoundError(f"Local file not found: {local_config_path}")

        # Check if the destination directory exists
        if not os.path.isdir(remote_data_dir):
            raise FileNotFoundError(f"Destination directory not found: {remote_data_dir}")

        try:
            dest_path = os.path.join(remote_data_dir, "postgresql.conf")

            shutil.copy2(local_config_path, dest_path)

            return dest_path
        except Exception as e:
            raise TimeoutError(f"Unsuccessful attempt to install the database user configuration:\n{str(e)}")

    async def copy_db_log_files(self, log_source_path: str, local_path: str, report_name: str)  -> Optional[str]:
        try:
            if not os.path.isdir(log_source_path):
                raise FileNotFoundError(f"Log source path does not exist or is not a directory: {log_source_path}")

            if not os.listdir(log_source_path):
                raise ValueError(f"Log source directory is empty: {log_source_path}")

            os.makedirs(local_path, exist_ok=True)
            dest_path = os.path.join(local_path, f"{report_name}")

            with tarfile.open(dest_path, "w") as tar:
                tar.add(log_source_path, arcname=os.path.basename(log_source_path))
            return dest_path
        except Exception as e:
            if self.logger:
                self.logger.error(f"Unsuccessful attempt to copy the database logs to the local directory 'db_logs':\n"
                                  f"{str(e)}")
            return None

    async def __aenter__(self) -> "LocalConnection":
        await self.start()
        return self

    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
    ) -> None:
        await self.close()
