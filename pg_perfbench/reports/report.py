import json
import logging
from pathlib import Path
from typing import Any

from pg_perfbench.const import REPORT_FOLDER, DEFAULT_REPORT_NAME
from pg_perfbench.const import REPORT_TEMPLATE_FOLDER
from pg_perfbench.const import (BENCHMARK_TEMPLATE_JSON_PATH, SYS_INFO_TEMPLATE_JSON_PATH, DB_INFO_TEMPLATE_JSON_PATH,
                                ALL_INFO_TEMPLATE_JSON_PATH)
from pg_perfbench.const import BENCHMARK_TEMPLATE_JSON_NAME
from pg_perfbench.const import WorkMode
from pg_perfbench.reports.schemas import BenchmarkReport, SysInfoReport, DBInfoReport, AllInfoReport
from pg_perfbench.exceptions import CommonException
from pg_perfbench.exceptions import ValidationError
from pg_perfbench.exceptions import format_pydantic_error


log = logging.getLogger(__name__)


def _get_report_json_template() -> dict[str, Any]:
    with open(REPORT_TEMPLATE_FOLDER / 'benchmark_report_struct.json', encoding='utf-8') as file:
        return json.load(file)


def _get_report_html_template() -> str:
    with open(REPORT_TEMPLATE_FOLDER / 'report.html', encoding='utf-8') as file:
        return file.read()


def _save_json_report(report: BenchmarkReport, new_report_path: Path, mode: WorkMode) -> None:

    if mode in {WorkMode.BENCHMARK, WorkMode.JOIN}:
        with open(BENCHMARK_TEMPLATE_JSON_PATH) as json_struct:
            report_json = json.load(json_struct)
    else:
        md_tmplt_dct = {
            WorkMode.COLLECT_SYS_INFO: SYS_INFO_TEMPLATE_JSON_PATH,
            WorkMode.COLLECT_DB_INFO: DB_INFO_TEMPLATE_JSON_PATH,
            WorkMode.COLLECT_ALL_INFO: ALL_INFO_TEMPLATE_JSON_PATH
        }
        with open(md_tmplt_dct[mode]) as json_struct:
            report_json = json.load(json_struct)


    if 'header' in report_json:
        report_json['header'] = report.header

    if 'description' in report_json:
        report_json['description'] = report.description

    if 'report_name' in report_json:
        report_json['report_name'] = report.report_name

    for sect_k, sect_v in report.sections.items():
        for report_k, report_v in sect_v.reports.items():
            report_json['sections'][sect_k]['reports'].setdefault(report_k, {})
            for obj_k, obj_v in report_v:
                report_json['sections'][sect_k]['reports'][report_k][obj_k] = obj_v

    with open(new_report_path, 'w+') as new_json:
        json.dump(report_json, new_json, indent=4, ensure_ascii=False)


def _save_html_report(new_report_json_path: str, path: Path) -> None:
    with open(new_report_json_path) as file_json:
        report_json = file_json.read()

    content = _get_report_html_template().replace('__REPORT_DATA', report_json)
    with open(path, 'w+') as file:
        file.write(content)


def save_report(report: BenchmarkReport, mode: WorkMode) -> None:
    REPORT_FOLDER.mkdir(parents=True, exist_ok=True)
    new_report_json_path = REPORT_FOLDER / f'{report.report_name}.json'
    new_report_html_path = REPORT_FOLDER / f'{report.report_name}.html'

    _save_json_report(report, new_report_json_path, mode)
    _save_html_report(new_report_json_path, new_report_html_path)
    log.info(
        'Reports generated: %s, %s', str(new_report_json_path.name), str(new_report_html_path.name)
    )
    log.info('The report is saved in the "report" folder')


def get_report_structure_from_json() -> BenchmarkReport:
    try:
        with open(BENCHMARK_TEMPLATE_JSON_PATH) as json_struct:
            data_json = json.load(json_struct)
        model = BenchmarkReport(**data_json)
        logging.info(f'Template {BENCHMARK_TEMPLATE_JSON_NAME} is configured correctly')
        return model
    except FileNotFoundError as e:
        raise CommonException(1, f'Error when reading json configuration: {e}')
    except ValidationError as e:
        raise CommonException(
            1, f'Error when reading json configuration: ' f'{format_pydantic_error(e)}'
        )
    except Exception as e:
        raise CommonException(
            1, f'Error when reading json configuration: {e}'
        )  # Incorrect Json configuration


def get_report_structure(path) -> BenchmarkReport | SysInfoReport:
    path_report_type = {
        BENCHMARK_TEMPLATE_JSON_PATH: BenchmarkReport,
        SYS_INFO_TEMPLATE_JSON_PATH: SysInfoReport,
        DB_INFO_TEMPLATE_JSON_PATH: DBInfoReport,
        ALL_INFO_TEMPLATE_JSON_PATH: AllInfoReport

    }
    try:
        with open(path) as json_struct:
            data_json = json.load(json_struct)
        model = path_report_type[path](**data_json)
        logging.info(f'Template {path.name} is configured correctly')
        return model
    except FileNotFoundError as e:
        raise CommonException(1, f'Error when reading json configuration: {e}')
    except ValidationError as e:
        raise CommonException(
            1, f'Error when reading json configuration: ' f'{format_pydantic_error(e)}'
        )
    except Exception as e:
        raise CommonException(
            1, f'Error when reading json configuration: {e}'
        )  # Incorrect Json configuration
