import logging
import os
from types import TracebackType
from typing import Self

import docker
from docker.errors import DockerException

from pg_perfbench.connections import Connectable
from pg_perfbench.const import LOG_ARCHIVE_NAME, get_datetime_report
from pg_perfbench.context.schemes.connections import DockerParams
from pg_perfbench.exceptions import BashCommandException
from pg_perfbench.operations.common import config_format_check
from pg_perfbench.operations.db import run_command

log = logging.getLogger(__name__)


class DockerConnection(Connectable):
    params: DockerParams

    def __init__(self, connection_params: DockerParams) -> None:
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

    async def start(self) -> None:
        host_data_dir_name = f'{self.params.container_name}_{get_datetime_report("%Y-%m-%d_%H-%M-%S")}'
        host_mount_data_catalog = os.path.join('/tmp', 'data', host_data_dir_name)

        self.docker_client = docker.from_env()
        try:
            mount_files = {
                '/sbin/sysctl': {'bind': '/sbin/sysctl', 'mode': 'ro'},
                host_mount_data_catalog: {
                    'bind': str(self.params.work_paths.pg_data_path),
                    'mode': 'rw',
                },
            }

            if self.params.work_paths.custom_config:
                if config_format_check(self.params.work_paths.custom_config):
                    config_data_path = '/etc/postgresql/postgresql.conf'
                    mount_files[self.params.work_paths.custom_config] = {
                        'bind': config_data_path,
                        'mode': 'rw',
                    }
                    log.info(
                        f'Custom config moved to the data directory:{config_data_path}'
                    )

            self.container = self.docker_client.containers.run(
                image=self.params.image_name,
                name=self.params.container_name,
                detach=True,
                privileged=True,
                ports={
                    f'{str(self.params.tunnel.remote.port)}/tcp': str(
                        self.params.tunnel.local.port
                    )
                },
                environment={
                    'POSTGRES_HOST_AUTH_METHOD': 'trust',
                    'ARG_PG_BIN_PATH': self.params.work_paths.pg_bin_path,
                },
                volumes=mount_files,
                command=f' -c config_file={config_data_path}',
            )
            log.info(f'Started Docker container: {self.params.container_name}')

        except docker.errors.NotFound:
            log.error(
                f'Container {self.params.container_name} not found.'
                f' Make sure it\'s running.',
            )
            raise Exception
        except DockerException as e:
            log.error(f'Error when connecting via Docker: {e!s}')
            raise Exception
        except Exception as e:
            log.error(
                f'Error when connecting to the database inside the Docker container: {e!s}'
            )
            raise Exception

    async def run(self, cmd: str) -> str:
        if self.container:
            try:
                exec_result = self.container.exec_run(cmd)
                log.info(
                    f"Docker Result: {exec_result.output.decode('utf-8').strip()}"
                )
                return exec_result.output
            except Exception as e:
                log.error(f'Error executing {cmd}: {e!s}')
        return None

    async def drop_cache(self) -> None:
        self.close()
        await run_command('sync')
        await run_command(
            'sudo /bin/sh -c "echo 3 | /usr/bin/tee /proc/sys/vm/drop_caches"'
        )
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
            raise BashCommandException(
                result.exit_code, result.output.decode('utf-8')
            )

        return result.output.decode('utf-8')

    async def copy_db_log_files(
        self, log_source_path, local_path
    ) -> str | None:
        log_archive_local_path = os.path.join(local_path, LOG_ARCHIVE_NAME)
        log_archive_source_path = f'/{LOG_ARCHIVE_NAME}'
        try:
            if not os.path.exists(local_path):
                os.makedirs(local_path)

            await self.run(
                f'tar -czvf {LOG_ARCHIVE_NAME} --directory={os.path.dirname(log_source_path)} '
                f'{os.path.basename(log_source_path)}'
            )

            stream, _ = self.container.get_archive(log_archive_source_path)
            with open(log_archive_local_path, 'wb') as f:
                for chunk in stream:
                    f.write(chunk)

            await self.run(f'rm {log_archive_source_path}')
            log.info(f'The log archive has been sent to :{log_archive_local_path}')

            return str(log_archive_local_path)
        except Exception as e:
            log.error(f'Attempt to transfer database logs failed" :{str(e)}')
            return None

    def print_logs(self):
        docker_logs = 'Docker logs: \n'
        logs = self.container.logs()
        for line in logs.decode('utf-8').splitlines():
            docker_logs.join(f'{line}')
        log.info(docker_logs)

    def close(self) -> None:
        if self.container:
            self.print_logs()
            self.container.stop()
            self.container.remove()
            log.info(
                f'Stopped and removed Docker container: {self.params.container_name}',
            )
