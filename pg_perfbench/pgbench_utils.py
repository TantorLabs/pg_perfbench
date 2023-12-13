import itertools
from pathlib import Path
import warnings

from pg_perfbench.context.schemas.db import DBParameters
from pg_perfbench.context.schemas.workload import WorkloadParams

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic.main")

def get_init_execution_command(db: DBParameters, workload: WorkloadParams) -> str:
    # FIXME: this one looks a bit off this place. Maybe rename this module?
    init_command = str(workload.init_command)
    arg_values = {}
    arg_values.update(db.model_dump())
    arg_values.update(workload.model_dump())
    for key, value in arg_values.items():
        if isinstance(key, str):
            placeholder = ''.join(['ARG_', str(key).upper()])
            init_command = init_command.replace(placeholder, str(value))
    return init_command


def _format_command(cmd: str, keys: tuple[str, ...], arguments: tuple[int, ...]) -> str:
    assert len(keys) == len(arguments), 'Given keys number does not much number of given arguments'

    for key, value in zip(keys, arguments):
        # cmd.append(f'-{key}')
        # cmd.append(str(value))
        placeholder = ''.join(['ARG_', key.upper()])
        cmd = cmd.replace(placeholder, str(value))
    return cmd


def get_pgbench_commands(db: DBParameters, workload: WorkloadParams) -> list[str]:
    # fmt: off
    pgbench_command = str(workload.workload_command)
    arg_values = {}
    arg_values.update(db.model_dump())
    arg_values.update(workload.model_dump())
    # fmt: on
    for key, value in arg_values.items():
        if isinstance(key, str):
            placeholder = ''.join(['ARG_', str(key).upper()])
            pgbench_command = pgbench_command.replace(placeholder, str(value))

    benchmark_options = workload.options.get_dict()
    if benchmark_options is not None:
        return [
            _format_command(str(pgbench_command), tuple(benchmark_options.keys()), values)
            for values in itertools.product(*benchmark_options.values())
        ]

    return [pgbench_command]


def get_pgbench_options(db: DBParameters, workload: WorkloadParams) -> list[str]:
    # fmt: off
    pgbench_command = str(workload.workload_command)
    arg_values = {}
    arg_values.update(workload.model_dump())
    # fmt: on
    # for key, value in arg_values.items():
    #     if isinstance(key, str):
    #         placeholder = ''.join(['ARG_', str(key).upper()])
    #         pgbench_command = pgbench_command.replace(placeholder, str(value))

    benchmark_options = workload.options.get_dict()
    if benchmark_options is not None:
        return [
            _format_command(str(pgbench_command), tuple(benchmark_options.keys()), values)
            for values in itertools.product(*benchmark_options.values())
        ]

    return [pgbench_command]