import asyncio
import asyncssh
import docker
import io
import os
from sshtunnel import SSHTunnelForwarder
import tarfile
from types import TracebackType
from typing import Self

from pg_perfbench.const import ConnectionType, LOG_ARCHIVE_DIR

class SSHConnection:
    def __init__(self, conn_params, tunnel_params = None):
        self.conn_params = conn_params
        self.tunnel_params = tunnel_params
        self.client = None
        self.tunnel = None
        self.logger = None

    def set_params(self, conn_params, tunnel_params):
        self.conn_params = conn_params
        self.tunnel_params = tunnel_params

    async def start(self):

        try:
            self.client = await asyncssh.connect(**self.conn_params)
            if self.tunnel_params is not None:
                self.tunnel = SSHTunnelForwarder(**self.tunnel_params)
                self.tunnel.start()
        except Exception as e:
            raise

    def close(self):
        if self.tunnel_params is not None:
            self.tunnel.stop()
        self.client.close()

    async def run_command(self, cmd: str)->str:
        if 'start' in cmd:
            process = await self.client.create_process(cmd)
            process.close()
            await asyncio.sleep(1)
            return ''

        process = await self.client.create_process(cmd)
        stdout, stderr = await process.communicate()
        process.close()
        return stdout

    async def send_file(self, local_config_path, remote_data_dir):
        remote_config_path = os.path.join(remote_data_dir, 'postgresql.conf')
        async with self.client.start_sftp_client() as sftp_client:
            await sftp_client.put(localpaths=local_config_path, remotepath=remote_config_path)
        return remote_config_path

    async def copy_db_log_files(self, log_source_path, local_path, report_name):
        log_archive_local_path = os.path.join(local_path, report_name)
        log_archive_source_path = f'{LOG_ARCHIVE_DIR}/{report_name}'
        try:

            if not os.path.exists(local_path):
                os.makedirs(local_path)

            await self.run_command(f'rm -rf {LOG_ARCHIVE_DIR}')
            await self.run_command(f'mkdir -p {LOG_ARCHIVE_DIR}')
            await self.run_command(
                f'tar -czvf {log_archive_source_path} --directory={os.path.dirname(log_source_path)}'
                f' {os.path.basename(log_source_path)}'
            )

            async with self.client.start_sftp_client() as sftp_client:
                await sftp_client.get(
                    log_archive_source_path, log_archive_local_path
                )

            await self.run_command(f'rm -rf {LOG_ARCHIVE_DIR}')
            self.logger.info(f'The log archive has been sent to :{log_archive_local_path}')
            return str(log_archive_local_path)
        except Exception as e:
            self.logger.error(f'Attempt to transfer database logs failed :{str(e)}')
            return None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.close()


class DockerConnection:
    def __init__(self, conn_params) -> None:
        self.conn_params = conn_params
        self.docker_client = None
        self.container = None
        self.logger = None

    def set_params(self, conn_params):
        self.conn_params = conn_params

    async def start(self):
        if not self.docker_client:
            self.docker_client = docker.from_env()
        name = self.conn_params.get("container_name")
        if not name:
            raise ValueError("Missing 'container_name'")
        self.container = self.docker_client.containers.get(name)
        self.container.reload()
        if self.container.status == "running":
            if self.logger:
                self.logger.info(f"Container '{name}' is already running.")
        else:
            self.container.start()
            if self.logger:
                self.logger.info(f"Container '{name}' has been started.")

    def close(self):
        if not self.container:
            if self.logger:
                self.logger.warning("No container to stop.")
            return
        name = self.container.name
        self.container.reload()
        if self.container.status == "running":
            self.container.stop()
            if self.logger:
                self.logger.info(f"Container '{name}' has been stopped.")
        else:
            if self.logger:
                self.logger.info(f"Container '{name}' is already stopped.")
        if self.docker_client:
            self.docker_client.close()
        self.container = None
        self.docker_client = None

    async def run_command(self, cmd: str) -> str:
        if not self.container:
            raise RuntimeError("Container not available")
        result = self.container.exec_run(
            ["/bin/bash", "-c", cmd],
            user="postgres",
            demux=True
        )
        out, err = result.output
        out_str = out.decode("utf-8", "replace") if out else ""
        err_str = err.decode("utf-8", "replace") if err else ""
        return out_str if out_str else err_str

    async def send_file(self, local_config_path, remote_data_dir):
        if not self.container:
            raise RuntimeError("Container not available")
        if not os.path.exists(local_config_path):
            raise FileNotFoundError(local_config_path)
        file_name = os.path.basename(local_config_path)
        tar_buffer = io.BytesIO()
        with tarfile.TarFile(fileobj=tar_buffer, mode='w') as tar:
            tar.add(local_config_path, arcname=file_name)
        tar_buffer.seek(0)
        success = self.container.put_archive(remote_data_dir, tar_buffer.getvalue())
        if not success:
            raise RuntimeError("Failed to put_archive")
        return os.path.join(remote_data_dir, file_name)

    async def copy_db_log_files(self, log_source_path, local_path, report_name):
        if not self.container:
            raise RuntimeError("Container not available")
        os.makedirs(local_path, exist_ok=True)
        local_archive_dir = os.path.join(local_path, report_name)
        try:
            stream, _ = self.container.get_archive(log_source_path)
            tar_bytes = b"".join(stream)
            archive_path = os.path.join(local_path, f"{report_name}.tar")
            with open(archive_path, "wb") as f:
                f.write(tar_bytes)
            with tarfile.open(archive_path, "r") as tar:
                tar.extractall(local_archive_dir)
            return local_archive_dir
        except Exception:
            return None

    async def __aenter__(self) -> Self:
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

def get_connection(type):
    if type == ConnectionType.SSH:
        return SSHConnection
    if type == ConnectionType.DOCKER:
        return DockerConnection


