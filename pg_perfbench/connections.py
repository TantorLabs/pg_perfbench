import asyncio
import asyncssh
import docker
import io
import os
import tarfile
import shutil
from typing import Optional
from types import TracebackType

from pg_perfbench.const import ConnectionType, SRC_LOG_ARCHIVE_DIR


class SSHConnection:
    def __init__(self, conn_params, tunnel_params=None):
        self.conn_params = conn_params
        self.tunnel_params = tunnel_params
        self.client = None
        self.tunnel = None
        self.logger = None

    async def start(self):
        try:
            self.conn_params['known_hosts'] = None
            self.client = await asyncssh.connect(**self.conn_params)
            if self.tunnel_params is not None:
                from sshtunnel import SSHTunnelForwarder
                try:
                    self.tunnel = SSHTunnelForwarder(**self.tunnel_params)
                    self.tunnel.start()
                except Exception as e:
                    raise ConnectionError(f"SSH tunnel forwarding failed: {e}")

        except asyncssh.misc.PermissionDenied:
            raise PermissionError("Verify the specified SSH key for remote server access.")

        except asyncssh.misc.ConnectionLost:
            raise TimeoutError("No access to the remote server: Verify access to the remote server.")

        except Exception as e:
            raise ConnectionError(f"SSH connection failed: {e} "
                                  f"\nVerify SSH connection parameters.")

    def close(self):
        if self.tunnel_params is not None and self.tunnel:
            self.tunnel.stop()
        if self.client:
            self.client.close()

    async def run_command(self, cmd: str, check=False) -> str:
        if not self.client:
            raise ConnectionError("SSH client not initialized.")

        if 'start' in cmd:
            process = await self.client.create_process(cmd)
            process.close()
            await asyncio.sleep(1)
            return ''

        process = await self.client.create_process(cmd)
        stdout, stderr = await process.communicate()
        if stderr != "" and check:
            raise RuntimeError(f"Command \"{cmd}\" failed for SSH connection with error:\n{stderr}")
        process.close()
        return stdout

    async def send_pg_config_file(self, local_config_path, remote_data_dir):
        if not self.client:
            raise ConnectionError("SSH client not initialized.")

        if not os.path.exists(local_config_path):
            raise FileNotFoundError(f"Local config does not exist: {local_config_path}")

        try:
            remote_config_path = os.path.join(remote_data_dir, 'postgresql.conf')
            async with self.client.start_sftp_client() as sftp_client:
                await sftp_client.put(localpaths=local_config_path, remotepath=remote_config_path)
            return remote_config_path
        except Exception as e:
            raise TimeoutError(f"Unsuccessful attempt to install the database user configuration:\n{str(e)}")

    async def copy_db_log_files(self, log_source_path, local_path, report_name):
        try:
            if not self.client:
                raise ConnectionError("SSH client not initialized.")

            log_archive_local_path = os.path.join(local_path, report_name)  # + '.tar'
            log_archive_source_path = f'{SRC_LOG_ARCHIVE_DIR}/{report_name}'

            if not os.path.exists(local_path):
                os.makedirs(local_path)

            await self.run_command(f'rm -rf {SRC_LOG_ARCHIVE_DIR}')
            await self.run_command(f'mkdir -p {SRC_LOG_ARCHIVE_DIR}')
            await self.run_command(
                f'tar -czvf {log_archive_source_path} '
                f'--directory={os.path.dirname(log_source_path)} '
                f'{os.path.basename(log_source_path)}'
            )

            async with self.client.start_sftp_client() as sftp_client:
                await sftp_client.get(log_archive_source_path, log_archive_local_path)

            await self.run_command(f'rm -rf {SRC_LOG_ARCHIVE_DIR}')
            return str(log_archive_local_path)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Unsuccessful attempt to copy the database logs to the local directory 'db_logs':\n"
                                  f"{str(e)}")
            return None

    async def __aenter__(self) -> "SSHConnection":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.close()


class DockerConnection:
    def __init__(self, conn_params, env) -> None:
        self.conn_params = conn_params
        self.docker_client = None
        self.container = None
        self.logger = None
        self.env: dict[str, str] = {}
        for key, value in env.items():
            self.env[key] = value

    async def start(self):
        if not self.docker_client:
            try:
                self.docker_client = docker.from_env()
            except docker.errors.DockerException as e:
                raise OSError(f"Cannot access Docker daemon: {e}")

        name = self.conn_params.get("container_name")
        if not name:
            raise FileNotFoundError("Missing 'container_name' in docker connection params")

        try:
            self.container = self.docker_client.containers.get(name)
        except docker.errors.NotFound:
            raise FileNotFoundError(f"Container '{name}' not found.")
        except Exception as e:
            raise OSError(f"Failed to retrieve container: {e}")

        try:
            self.container.reload()
        except Exception:
            raise OSError("Cannot reload container or port is unavailable.")

        if self.container.status == "running":
            if self.logger:
                self.logger.debug(f"Container '{name}' is already running.")
        else:
            self.container.start()
            if self.logger:
                self.logger.debug(f"Container '{name}' has been started.")

    def close(self):
        if not self.container:
            if self.logger:
                self.logger.warning("No container to stop.")
            return

        name = self.container.name
        try:
            self.container.reload()
            if self.container.status == "running":
                self.container.stop()
                if self.logger:
                    self.logger.debug(f"Container '{name}' has been stopped.")
            else:
                if self.logger:
                    self.logger.debug(f"Container '{name}' is already stopped.")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error stopping container: {str(e)}")

        if self.docker_client:
            self.docker_client.close()
        self.container = None
        self.docker_client = None

    async def run_command(self, cmd: str, check=False) -> str:
        if not self.container:
            raise PermissionError("Container not available or no access to 'postgres' user.")

        result = self.container.exec_run(
            ["/bin/bash", "-c", cmd],
            user="postgres",
            demux=True,
            environment=self.env
        )
        if result.exit_code != 0 and check:
            out, err = result.output
            error_message = err.decode("utf-8", "replace") if err else "Unknown error"
            raise RuntimeError(
                f"Command \"{cmd}\" failed for Docker connection with exit code {result.exit_code}: {error_message} \n")
        out, _ = result.output
        return out.decode("utf-8", "replace") if out else ""

    async def run_command_as_root(self, cmd: str) -> str:
        if not self.container:
            raise PermissionError("No container available.")

        result = self.container.exec_run(
            ["/bin/bash", "-c", cmd],
            user="root",
            demux=True,
            environment=self.env
        )

        if result.exit_code != 0:
            out, err = result.output
            error_message = err.decode("utf-8", "replace") if err else "Unknown error"
            raise RuntimeError(f"Command \"{cmd}\" failed with exit code {result.exit_code}: {error_message}")

        out, _ = result.output
        return out.decode("utf-8", "replace") if out else ""

    async def send_pg_config_file(self, local_config_path, remote_data_dir):
        if not self.container:
            raise PermissionError("Container not available.")
        if not os.path.exists(local_config_path):
            raise FileNotFoundError(f"File not found: {local_config_path}")

        try:
            file_name = os.path.basename(local_config_path)
            tmp_path = f"/tmp"
            tar_buffer = io.BytesIO()
            with tarfile.TarFile(fileobj=tar_buffer, mode='w') as tar:
                tar.add(local_config_path, arcname=file_name)
            tar_buffer.seek(0)

            success = self.container.put_archive(tmp_path, tar_buffer.getvalue())
            if not success:
                raise OSError("Failed to put_archive into Docker container.")

            remote_file_path = os.path.join(tmp_path, file_name)
            remote_config_path = os.path.join(remote_data_dir, 'postgresql.conf')
            chmod_cmd = f"cp {remote_file_path} {remote_config_path}"
            await self.run_command_as_root(chmod_cmd)

            chown_cmd = f"chown postgres:postgres '{remote_file_path}'"
            chown_result = await self.run_command_as_root(chown_cmd)
            if "Operation not permitted" in chown_result:
                raise PermissionError(f"Failed to chown {remote_file_path}: {chown_result}")

            chmod_cmd = f"chmod 750 '{remote_data_dir}'"
            await self.run_command_as_root(chmod_cmd)

            return remote_file_path
        except Exception as e:
            raise TimeoutError(f"Unsuccessful attempt to install the database user configuration:\n{str(e)}")

    async def copy_db_log_files(self, log_source_path, local_path, report_name):
        if not self.container:
            raise PermissionError("Container not available.")
        os.makedirs(local_path, exist_ok=True)

        local_archive_dir = os.path.join(local_path, report_name)
        try:
            stream, _ = self.container.get_archive(log_source_path)
            tar_bytes = b"".join(stream)

            archive_path = os.path.join(local_path, f"{report_name}.tar")
            with open(archive_path, "wb") as f:
                f.write(tar_bytes)

            # with tarfile.open(archive_path, "r") as tar:
            #     tar.extractall(local_archive_dir)
            return archive_path
        except Exception as e:
            if self.logger:
                self.logger.error(f"Unsuccessful attempt to copy the database logs to the local directory 'db_logs':\n"
                                  f"{str(e)}")
            return None

    async def __aenter__(self) -> "DockerConnection":
        if not hasattr(self, 'client'):
            await self.start()
        return self

    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
    ) -> None:
        # self.close()
        ...


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
            if self.logger:
                self.logger.error(f"Failed to start subprocess for command: {cmd}\nError: {str(e)}")
            return ''

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

    async def copy_db_log_files(self, log_source_path: str, local_path: str, report_name: str) -> str:
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


def get_connection(type):
    if type == ConnectionType.SSH:
        return SSHConnection
    if type == ConnectionType.DOCKER:
        return DockerConnection
    if type == ConnectionType.LOCAL:
        return LocalConnection
