import asyncio
import os
from types import TracebackType
from typing import Self
import asyncssh
from sshtunnel import SSHTunnelForwarder

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

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.close()

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

# draft
class DockerConnection:
    def __init__(self, connection_params) -> None:
        self.params = connection_params
        self.docker_client = None
        self.container = None

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
        self.close()


def get_connection(type):
    if type == ConnectionType.SSH:
        return SSHConnection
    if type == ConnectionType.DOCKER:
        return DockerConnection


