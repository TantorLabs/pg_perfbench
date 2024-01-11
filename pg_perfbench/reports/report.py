import json
import logging
import time
from pathlib import Path
from typing import Any
from datetime import datetime

from pg_perfbench.const import REPORT_FOLDER, get_datetime_report
from pg_perfbench.const import REPORT_TEMPLATE_FOLDER
from pg_perfbench.const import TEMPLATE_JSON_PATH
from pg_perfbench.const import TEMPLATE_JSON_NAME
from pg_perfbench.reports.schemas import Report
from pg_perfbench.exceptions import CommonException
from pg_perfbench.exceptions import ValidationError
from pg_perfbench.exceptions import format_pydantic_error


log = logging.getLogger(__name__)


def _get_report_json_template() -> dict[str, Any]:
    with open(REPORT_TEMPLATE_FOLDER / 'report_struct.json', encoding='utf-8') as file:
        return json.load(file)


def _get_report_html_template() -> str:
    with open(REPORT_TEMPLATE_FOLDER / 'report.html', encoding='utf-8') as file:
        return file.read()


def _save_json_report(report: Report, new_report_path: Path) -> None:

    with open(TEMPLATE_JSON_PATH) as json_struct:
        full_json = json.load(json_struct)

    if 'description' in full_json:
        full_json['description'] = report.description

    for sect_k, sect_v in report.sections.items():
        for report_k, report_v in sect_v.reports.items():
            for obj_k, obj_v in report_v:
                if (obj_k == 'data' or obj_k == 'theader' or obj_k == 'item_type'):
                    full_json['sections'][sect_k]['reports'][report_k][obj_k] = obj_v

    with open(new_report_path, 'w+') as new_json:
        json.dump(full_json, new_json, indent=4, ensure_ascii=False)


def _save_html_report(new_report_json_path: str, path: Path) -> None:
    with open(new_report_json_path) as file_json:
        report_json = file_json.read()

    content = _get_report_html_template().replace('__REPORT_DATA', report_json)
    with open(path, 'w+') as file:
        file.write(content)


def save_report(report: Report) -> None:
    REPORT_FOLDER.mkdir(parents=True, exist_ok=True)
    current_datetime = get_datetime_report('%Y-%m-%d_%H:%M:%S')
    new_report_json_path = REPORT_FOLDER / f'report_{current_datetime}.json'
    new_report_html_path = REPORT_FOLDER / f'report_{current_datetime}.html'

    _save_json_report(report, new_report_json_path)
    _save_html_report(new_report_json_path, new_report_html_path)
    log.info(
        'Reports generated: %s, %s', str(new_report_json_path.name), str(new_report_html_path.name)
    )
    log.info('The report is saved in the "report" folder')


def get_report_structure_from_json() -> Report:
    try:
        with open(TEMPLATE_JSON_PATH) as json_struct:
            data_json = json.load(json_struct)
        model = Report(**data_json)
        logging.info(f'Template {TEMPLATE_JSON_NAME} is configured correctly')
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
