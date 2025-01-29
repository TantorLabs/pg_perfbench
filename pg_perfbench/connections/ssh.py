import asyncio
import logging
import os
from types import TracebackType
from typing import Self

import asyncssh
from asyncssh import SSHClientConnection
from sshtunnel import SSHTunnelForwarder

from pg_perfbench.connections.common import Connectable
from pg_perfbench.const import DEFAULT_LOG_ARCHIVE_NAME, LOG_ARCHIVE_DIR
from pg_perfbench.context.schemes.connections import SSHConnectionParams
from pg_perfbench.exceptions import BashCommandException
from pg_perfbench.operations.common import config_format_check

log = logging.getLogger(__name__)


class SSHConnection(Connectable):
    params: SSHConnectionParams
    tunnel: SSHTunnelForwarder
    client: SSHClientConnection

    def __init__(self, connection_params: SSHConnectionParams) -> None:
        self.params = connection_params

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

    async def start(self) -> None:
        log.info('Attempting to establish an SSH connection: ')
        try:
            self.client = await asyncssh.connect(
                host=self.params.host,
                port=self.params.port,
                username=self.params.user,
                client_keys=self.params.key,
                known_hosts=None,
                env={
                    'ARG_PG_BIN_PATH': f'{self.params.work_paths.pg_bin_path}'
                },
                connect_timeout=5,
            )
            self.tunnel = SSHTunnelForwarder(
                (self.params.host, self.params.port),
                ssh_username=self.params.user,
                ssh_pkey=self.params.key,
                remote_bind_address=(
                    self.params.tunnel.remote.host,
                    self.params.tunnel.remote.port,
                ),
                local_bind_address=(
                    self.params.tunnel.local.host,
                    self.params.tunnel.local.port,
                ),
            )
            self.tunnel.start()

            if self.params.work_paths.custom_config:
                if config_format_check(self.params.work_paths.custom_config):
                    await self.send_config(
                        self.params.work_paths.custom_config,
                        self.params.work_paths.pg_data_path,
                    )
            log.info('SSH connection established.')
        except asyncio.TimeoutError:
            log.error('Failed to establish SSH connection: Connection attempt timed out.')
            raise
        except Exception as e:
            log.error(f'Failed to establish SSH connection:{str(e)}')
            raise

    async def run(self, cmd: str) -> str:
        if 'start' in cmd:
            process = await self.client.create_process(cmd)
            process.close()
            await asyncio.sleep(1)
            return ''

        process = await self.client.create_process(cmd)
        stdout, stderr = await process.communicate()
        process.close()
        log.info(str(stderr))
        return stdout

    async def bash_command(self, cmd: str) -> str:
        try:
            result = await self.client.run('bash', input=cmd, check=True)
        except Exception as e:
            raise BashCommandException(e.returncode, e.stderr)
        return result.stdout

    async def drop_cache(self) -> None:
        await self.run(
            f'{self.params.work_paths.pg_bin_path}/pg_ctl '
            f'stop -D {self.params.work_paths.pg_data_path}',
        )
        await self.run('sync')
        await self.run(
            'sudo /bin/sh -c "echo 3 | /usr/bin/tee /proc/sys/vm/drop_caches"'
        )
        await self.run(
            f'{self.params.work_paths.pg_bin_path}/pg_ctl start -D '
            f'{self.params.work_paths.pg_data_path}'
        )

    async def restart_db(self) -> None:
        await self.run(
            f'{self.params.work_paths.pg_bin_path}/pg_ctl '
            f'stop -D {self.params.work_paths.pg_data_path}',
        )
        await self.run(
            f'{self.params.work_paths.pg_bin_path}/pg_ctl start -D '
            f'{self.params.work_paths.pg_data_path}'
        )

    async def send_config(self, local_path, data_dir) -> str | None:
        remote_config_path = os.path.join(data_dir, 'postgresql.conf')
        async with self.client.start_sftp_client() as sftp_client:
            await sftp_client.put(localpaths=local_path, remotepath=remote_config_path)
            log.info(f'Custom config "{local_path}" \n moved to the data directory "{remote_config_path}"')
            return remote_config_path

    async def copy_db_log_files(
        self, log_source_path, local_path, report_name
    ) -> str | None:
        log_archive_local_path = os.path.join(local_path, report_name)
        log_archive_source_path = f'{LOG_ARCHIVE_DIR}/{report_name}'
        try:

            if not os.path.exists(local_path):
                os.makedirs(local_path)

            await self.run(f'rm -rf {LOG_ARCHIVE_DIR}')
            await self.run(f'mkdir -p {LOG_ARCHIVE_DIR}')
            await self.run(
                f'tar -czvf {log_archive_source_path} --directory={os.path.dirname(log_source_path)}'
                f' {os.path.basename(log_source_path)}'
            )

            async with self.client.start_sftp_client() as sftp_client:
                await sftp_client.get(
                    log_archive_source_path, log_archive_local_path
                )

            await self.run(f'rm -rf {LOG_ARCHIVE_DIR}')
            log.info(f'The log archive has been sent to :{log_archive_local_path}')
            return str(log_archive_local_path)
        except Exception as e:
            log.error(f'Attempt to transfer database logs failed" :{str(e)}')
            return None

    def close(self) -> None:
        if hasattr(self, 'tunnel'):
            self.tunnel.stop()
        if hasattr(self, 'client'):
            self.client.close()
        log.info('Terminating the SSH connection')
