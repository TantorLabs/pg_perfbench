# ruff: noqa: ANN401
import logging
from inspect import isclass
from types import UnionType
from typing import Any
from typing import get_args
from typing import get_origin
from typing import Optional


import pydantic
from pydantic import BaseModel
from pydantic import Field
from pydantic.fields import FieldInfo

from pg_perfbench.context.schemes.connections import ConnectionParameters
from pg_perfbench.context.schemes.db import DBParameters
from pg_perfbench.context.schemes.workload import WorkloadParameters
from pg_perfbench.context.schemes.report import ReportParameters
from pg_perfbench.exceptions import format_pydantic_error
from pg_perfbench.const import REPORT_FOLDER

log = logging.getLogger(__name__)

RawArgs = dict[str, str | bool | None | list[int | None]]


def is_subclass(
    __cls: type,
    __cls_or_tuple: type | UnionType | tuple[type | UnionType | tuple[Any, ...], ...],
) -> bool:
    """Check if given object is a class and it is a subclass of another given argument."""
    return isclass(__cls) and issubclass(__cls, __cls_or_tuple)


def restructure_args_dict(
    fields: dict[str, FieldInfo],
    args: dict[str, str],
) -> dict[str, str | dict]:
    restructured: dict[str, Any] = {}
    for name, field in fields.items():
        key = field.alias or name
        field_type = field.annotation

        if isclass(field_type) and issubclass(field_type, BaseModel):
            restructured[key] = restructure_args_dict(field_type.model_fields, args)
            continue

        if get_origin(field_type) is UnionType:
            complex_dict: dict[str, Any] = {}
            for component in get_args(field_type):
                if is_subclass(component, BaseModel):
                    complex_dict |= restructure_args_dict(component.model_fields, args)
            restructured[key] = complex_dict

    if conflict := restructured.keys() & args.keys():
        raise ValueError(f'Arguments name conflict: {conflict}')

    return restructured | args


class Context(BaseModel):
    raw_args: RawArgs
    db: DBParameters
    workload: WorkloadParameters = Field(..., discriminator='benchmark_type')
    connection: ConnectionParameters
    report: ReportParameters

    @classmethod
    def from_args_map(
        cls: type['Context'],
        args_map: dict[str, str | None],
    ) -> Optional['Context']:
        # FIXME: Might be a better solution using validators to ensure 'benchmark' field
        meaningful_args = {k: v for k, v in args_map.items() if v is not None or k == 'benchmark'}

        restructured_args = restructure_args_dict(Context.model_fields, meaningful_args)
        restructured_args['raw_args'] = args_map

        try:
            return Context.model_validate(restructured_args)
        except pydantic.ValidationError as error:
            # TODO: add traceback print control
            log.error(
                format_pydantic_error(error), exc_info=True
            )  # noqa: G201

        return None


class JoinContext(BaseModel):
    raw_args: RawArgs
    report_name: str = Field(default='', alias='report_name')
    join_task: str = ''
    input_dir: str = Field(default=str(REPORT_FOLDER))
    reference_report: str = ''

    @classmethod
    def from_args_map(
        cls: type['JoinContext'],
        args_map: dict[str, str | None],
    ) -> Optional['JoinContext']:
        # FIXME: Might be a better solution using validators to ensure 'benchmark' field
        meaningful_args = {
            k: v
            for k, v in args_map.items()
            if v is not None or k == 'benchmark'
        }

        restructured_args = restructure_args_dict(
            Context.model_fields, meaningful_args
        )
        restructured_args['raw_args'] = args_map

        try:
            return JoinContext.model_validate(restructured_args)
        except pydantic.ValidationError as error:
            # TODO: add traceback print control
            log.error(
                format_pydantic_error(error), exc_info=True
            )  # noqa: G201

        return None

class CollectSysInfoContext(BaseModel):
    raw_args: RawArgs
    connection: ConnectionParameters
    report: ReportParameters

    @classmethod
    def from_args_map(
            cls: type['CollectSysInfoContext'],
            args_map: dict[str, str | None],
    ) -> Optional['CollectSysInfoContext']:
        # FIXME: Might be a better solution using validators to ensure 'benchmark' field
        meaningful_args = {k: v for k, v in args_map.items() if v is not None or k == 'benchmark'}

        restructured_args = restructure_args_dict(Context.model_fields, meaningful_args)
        restructured_args['raw_args'] = args_map

        try:
            return CollectSysInfoContext.model_validate(restructured_args)
        except pydantic.ValidationError as error:
            # TODO: add traceback print control
            log.error(
                format_pydantic_error(error), exc_info=True
            )  # noqa: G201

        return None

class CollectDBInfoContext(BaseModel):
    raw_args: RawArgs
    db: DBParameters
    connection: ConnectionParameters
    report: ReportParameters

    @classmethod
    def from_args_map(
            cls: type['CollectDBInfoContext'],
            args_map: dict[str, str | None],
    ) -> Optional['CollectDBInfoContext']:
        # FIXME: Might be a better solution using validators to ensure 'benchmark' field
        meaningful_args = {k: v for k, v in args_map.items() if v is not None or k == 'benchmark'}

        restructured_args = restructure_args_dict(Context.model_fields, meaningful_args)
        restructured_args['raw_args'] = args_map

        try:
            return CollectDBInfoContext.model_validate(restructured_args)
        except pydantic.ValidationError as error:
            # TODO: add traceback print control
            log.error(
                format_pydantic_error(error), exc_info=True
            )  # noqa: G201

        return None
