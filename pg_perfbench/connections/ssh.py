import asyncio
import asyncssh
import os
from typing import Optional

from pg_perfbench.const import SRC_LOG_ARCHIVE_DIR


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
                    raise ConnectionError(f'SSH tunnel forwarding failed: {e}')

        except asyncssh.misc.PermissionDenied:
            raise PermissionError(
                'Verify the specified SSH key for remote server access.'
            )

        except asyncssh.misc.ConnectionLost:
            raise TimeoutError(
                'No access to the remote server: Verify access to the remote server.'
            )

        except Exception as e:
            raise ConnectionError(
                f'SSH connection failed: {e} '
                f'\nVerify SSH connection parameters.'
            )

    def close(self):
        if self.tunnel_params is not None and self.tunnel:
            self.tunnel.stop()
        if self.client:
            self.client.close()

    async def run_command(self, cmd: str, check=False) -> str:
        if not self.client:
            raise ConnectionError('SSH client not initialized.')

        if 'start' in cmd:
            process = await self.client.create_process(cmd)
            process.close()
            await asyncio.sleep(1)
            return ''

        process = await self.client.create_process(cmd)
        stdout, stderr = await process.communicate()
        if stderr != '' and check:
            raise RuntimeError(
                f'Command "{cmd}" failed for SSH connection with error:\n{stderr}'
            )
        process.close()
        return stdout

    async def send_pg_config_file(self, local_config_path, remote_data_dir):
        if not self.client:
            raise ConnectionError('SSH client not initialized.')

        if not os.path.exists(local_config_path):
            raise FileNotFoundError(
                f'Local config does not exist: {local_config_path}'
            )

        try:
            remote_config_path = os.path.join(
                remote_data_dir, 'postgresql.conf'
            )
            async with self.client.start_sftp_client() as sftp_client:
                await sftp_client.put(
                    localpaths=local_config_path, remotepath=remote_config_path
                )
            return remote_config_path
        except Exception as e:
            raise TimeoutError(
                f'Unsuccessful attempt to install the database user configuration:\n{str(e)}'
            )

    async def copy_db_log_files(
        self, log_source_path, local_path, report_name
    ) -> Optional[str]:
        try:
            if not self.client:
                raise ConnectionError('SSH client not initialized.')

            log_archive_local_path = os.path.join(
                local_path, report_name
            )  # + '.tar'
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
                await sftp_client.get(
                    log_archive_source_path, log_archive_local_path
                )

            await self.run_command(f'rm -rf {SRC_LOG_ARCHIVE_DIR}')
            return str(log_archive_local_path)

        except Exception as e:
            if self.logger:
                self.logger.error(
                    f'Unsuccessful attempt to copy the database logs to the local directory "db_logs":\n'
                    f'{str(e)}'
                )
            return None

    async def __aenter__(self) -> 'SSHConnection':
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.close()
