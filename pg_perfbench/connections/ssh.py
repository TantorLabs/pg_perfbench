import asyncio
import logging
from types import TracebackType
from typing import Self

import asyncssh
from asyncssh import SSHClientConnection
from sshtunnel import SSHTunnelForwarder

from pg_perfbench.connections.common import Connectable
from pg_perfbench.context.schemas.connections import SSHConnectionParams
from pg_perfbench.exceptions import BashCommandException

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
        log.info('Establishing an SSH connection')
        try:
            self.client = await asyncssh.connect(
                host=self.params.host,
                port=self.params.port,
                username=self.params.user,
                client_keys=self.params.key,
                known_hosts=None,
            )

            self.tunnel = SSHTunnelForwarder(
                (self.params.host, self.params.port),
                ssh_username=self.params.user,
                ssh_pkey=self.params.key,
                remote_bind_address=(self.params.tunnel.remote.host, self.params.tunnel.remote.port),
                local_bind_address=(self.params.tunnel.local.host, self.params.tunnel.local.port),
            )
            self.tunnel.start()
        except Exception as e:
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
            f'stop -D {self.params.work_paths.pg_data_directory_path}',
        )
        await self.run('sync')
        await self.run('sudo /bin/sh -c "echo 3 | /usr/bin/tee /proc/sys/vm/drop_caches"')
        await self.run(
            f'{self.params.work_paths.pg_bin_path}/pg_ctl start -D '
            f'{self.params.work_paths.pg_data_directory_path}'
        )

    def close(self) -> None:
        if hasattr(self, 'tunnel'):
            self.tunnel.stop()
        if hasattr(self, 'client'):
            self.client.close()
        log.info('Terminating the SSH connection')
