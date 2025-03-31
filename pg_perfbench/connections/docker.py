import asyncio
import docker
import io
import os
import tarfile
from typing import Optional
from types import TracebackType


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
            raise FileNotFoundError("Missing \"container_name\" in docker connection params")

        try:
            self.container = self.docker_client.containers.get(name)
        except docker.errors.NotFound:
            raise FileNotFoundError(f"Container \"{name}\" not found.")
        except Exception as e:
            raise OSError(f"Failed to retrieve container: {e}")

        try:
            self.container.reload()
        except Exception:
            raise OSError("Cannot reload container or port is unavailable.")

        if self.container.status == "running":
            if self.logger:
                self.logger.debug(f"Container \"{name}\" is already running.")
        else:
            self.container.start()
            if self.logger:
                self.logger.debug(f"Container \"{name}\" has been started.")

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
                    self.logger.debug(f"Container \"{name}\" has been stopped.")
            else:
                if self.logger:
                    self.logger.debug(f"Container \"{name}\" is already stopped.")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error stopping container: {str(e)}")

        if self.docker_client:
            self.docker_client.close()
        self.container = None
        self.docker_client = None

    async def run_command(self, cmd: str, check=False) -> str:
        if not self.container:
            raise PermissionError("Container not available or no access to \"postgres\" user.")

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

            chown_cmd = f"chown postgres:postgres '{remote_config_path}'"
            chown_result = await self.run_command_as_root(chown_cmd)
            if "Operation not permitted" in chown_result:
                raise PermissionError(f"Failed to chown {remote_file_path}: {chown_result}")

            chmod_cmd = f"chmod 750 '{remote_config_path}'"
            await self.run_command_as_root(chmod_cmd)

            return remote_config_path
        except Exception as e:
            raise TimeoutError(f"Unsuccessful attempt to install the database user configuration:\n{str(e)}")

    async def copy_db_log_files(self, log_source_path, local_path, report_name) -> Optional[str]:
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
                self.logger.error(
                    f"Unsuccessful attempt to copy the database logs to the local directory \"db_logs\":\n"
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
