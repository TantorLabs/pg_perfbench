import asyncio
import logging
from pathlib import Path
from types import TracebackType
from typing import Self

import docker
from docker.errors import DockerException

from pg_perfbench.connections import Connectable
from pg_perfbench.context.schemas.connections import DockerParams
from pg_perfbench.exceptions import BashCommandException
from pg_perfbench.operations.db import run_command

log = logging.getLogger(__name__)


class DockerConnection(Connectable):
    params: DockerParams

    def __init__(self, connection_params: DockerParams) -> None:
        self.connection_params = connection_params
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

    async def copy_files_to_container(self, source_paths: Path, destination_paths: Path) -> None:
        if not self.container:
            log.error('Container is not running.')
            return
        try:
            for source_path, destination_path in zip(source_paths, destination_paths):
                self.container.put_archive('/', source_path)
                log.info(
                    f'Copied {source_path} to {self.connection_params.container_name}:'
                    f'{destination_path}',
                )
        except DockerException as e:
            log.error(f'Error when copying files to Docker container: {e!s}')
        except Exception as e:
            log.error(f'Error when copying files to Docker container: {e!s}')

    async def start(self) -> None:
        self.docker_client = docker.from_env()
        try:

            self.container = self.docker_client.containers.run(
                image=self.connection_params.image_name,
                name=self.connection_params.container_name,
                detach=True,
                privileged=True,
                ports={
                    f'{str(self.connection_params.tunnel.remote.port)}/tcp': str(
                        self.connection_params.tunnel.local.port
                    )
                },
                environment={'POSTGRES_HOST_AUTH_METHOD': 'trust',
                             'ARG_PG_BIN_PATH': self.connection_params.work_paths.pg_bin_path},
                volumes={
                    '/sbin/sysctl': {'bind': '/sbin/sysctl', 'mode': 'ro'},
                    f'/tmp/data/{self.connection_params.container_name}_data': {
                        'bind': str(self.connection_params.work_paths.pg_data_path),
                        'mode': 'rw',
                    },
                },
            )
            log.info(f'Started Docker container: {self.connection_params.container_name}')
        except docker.errors.NotFound:
            log.error(
                f'Container {self.connection_params.container_name} not found.'
                f' Make sure it\'s running.',
            )
            raise Exception
        except DockerException as e:
            log.error(f'Error when connecting via Docker: {e!s}')
            raise Exception
        except Exception as e:
            log.error(f'Error when connecting to the database inside the Docker container: {e!s}')
            raise Exception

    async def run(self, cmd: str) -> str:
        if self.container:
            try:
                if 'sudo' in cmd:
                    exec_command = cmd.replace('sudo', '')
                else:
                    exec_command = f"su - postgres -c '{cmd}'"
                if 'start' in cmd:
                    exec_result = self.container.exec_run(exec_command)
                    await asyncio.sleep(1)
                    log.info(f"Docker Result: {exec_result.output.decode('utf-8').strip()}")
                    return exec_result.output
                exec_result = self.container.exec_run(exec_command)
                log.info(f"Docker Result: {exec_result.output.decode('utf-8').strip()}")
                return exec_result.output
            except Exception as e:
                log.error(f'Error executing {cmd}: {e!s}')
        return None

    async def drop_cache(self) -> None:
        self.close()
        await run_command('sync')
        await run_command('sudo /bin/sh -c "echo 3 | /usr/bin/tee /proc/sys/vm/drop_caches"')
        await self.start()

    async def bash_command(self, cmd: str) -> str:
        result = self.container.exec_run(
            cmd=f'bash -c "{cmd}"',
            stdin=True,
            tty=True,
            detach=False,
            stdout=True,
            stderr=True,
        )
        if result.exit_code != 0:
            raise BashCommandException(result.exit_code, result.output.decode('utf-8'))

        return result.output.decode('utf-8')

    def close(self) -> None:
        if self.container:
            self.container.stop()
            self.container.remove()
            log.info(
                f'Stopped and removed Docker container: {self.connection_params.container_name}',
            )
