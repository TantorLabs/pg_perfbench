import asyncio
import logging
import os
import zipfile
from pathlib import Path
from types import TracebackType
from typing import Self

import docker
from docker.errors import DockerException

from pg_perfbench.connections import Connectable
from pg_perfbench.const import MAIN_REPORT_NAME
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

    async def copy_files_to_container(self, source_paths: Path, destination_paths: Path) -> None:
        if not self.container:
            log.error('Container is not running.')
            return
        try:
            for source_path, destination_path in zip(source_paths, destination_paths):
                self.container.put_archive('/', source_path)
                log.info(
                    f'Copied {source_path} to {self.params.container_name}:'
                    f'{destination_path}',
                )
        except DockerException as e:
            log.error(f'Error when copying files to Docker container: {e!s}')
        except Exception as e:
            log.error(f'Error when copying files to Docker container: {e!s}')

    async def start(self) -> None:
        self.docker_client = docker.from_env()
        try:

            mount_files = {
                '/sbin/sysctl': {'bind': '/sbin/sysctl', 'mode': 'ro'},
                f'/tmp/data/{self.params.container_name}_data': {
                    'bind': str(self.params.work_paths.pg_data_path),
                    'mode': 'rw',
                },
            }

            if self.params.work_paths.custom_config:
                if config_format_check(self.params.work_paths.custom_config):
                    config_data_path = os.path.join(self.params.work_paths.pg_data_path,'postgresql.conf')
                    mount_files[self.params.work_paths.custom_config] = {'bind': config_data_path, 'mode': 'rw'}
                    log.info(f"Custom config moved to the data directory:{config_data_path}")

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
                environment={'POSTGRES_HOST_AUTH_METHOD': 'trust',
                             'ARG_PG_BIN_PATH': self.params.work_paths.pg_bin_path},
                volumes=mount_files,
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

    async def copy_db_log_files(self, source_logs_path, local_path) -> str | None:
        logs_archive_path: str = ''
        tmp_local_log_dir = os.path.join('/tmp', f'tmp_logs_files_{MAIN_REPORT_NAME}')

        log_files = await self.bash_command(f"ls {source_logs_path}")
        log_files = log_files.split("\r\n")
        log_files = [file for file in log_files if file.endswith(".log")]
        if log_files is []:
            return None
        os.makedirs(tmp_local_log_dir)

        for log_file in log_files:
            source_file_path = os.path.join(source_logs_path, log_file)
            local_file_path = os.path.join(tmp_local_log_dir, log_file)
            stream, _ = self.container.get_archive(source_file_path)
            with open(local_file_path, 'wb') as f:
                for chunk in stream:
                    f.write(chunk)

        logs_archive_name = f'archive_logs_{MAIN_REPORT_NAME}'
        logs_archive_path = os.path.join(local_path, logs_archive_name)

        if not os.path.exists(local_path):
            os.makedirs(local_path)

        with zipfile.ZipFile(logs_archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(tmp_local_log_dir):
                for file in files:
                    if file.endswith('.log'):
                        file_path = os.path.join(root, tmp_local_log_dir, file)
                        zipf.write(file_path, os.path.relpath(file_path, local_path))
                        os.remove(file_path)
        log.info(f"Copied {source_logs_path} to {logs_archive_path}")

        if not os.path.exists(tmp_local_log_dir):
            os.rmdir(tmp_local_log_dir)

        return logs_archive_path

    def close(self) -> None:
        if self.container:
            self.container.stop()
            self.container.remove()
            log.info(
                f'Stopped and removed Docker container: {self.params.container_name}',
            )
