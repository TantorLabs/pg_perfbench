import json
from typing import List

from pg_perfbench.const import REPORT_FOLDER, REPORT_TEMPLATE_FOLDER
import os


def get_report_structure(file_path):
    # Check if file_path exists before reading
    if not os.path.exists(file_path):
        # Raise an error if the template file is missing
        raise FileNotFoundError(
            f'Report template file not found at: {file_path}'
        )

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Basic validation: check if data is a dictionary
    if not isinstance(data, dict):
        raise ValueError(
            'Invalid report structure: the loaded JSON must be a dictionary.'
        )

    return data


def _save_json_report(new_report_path, report_json):
    # Use try-except to handle potential I/O errors
    try:
        with open(new_report_path, 'w', encoding='utf-8') as new_json:
            json.dump(report_json, new_json, indent=4, ensure_ascii=False)
    except OSError as e:
        # Log or raise the error for debugging
        raise OSError(
            f'Failed to write JSON report to {new_report_path}: {str(e)}'
        )


def _get_report_html_template() -> str:
    # Check if the template folder exists
    template_file = REPORT_TEMPLATE_FOLDER / 'report.html'
    if not os.path.exists(template_file):
        raise FileNotFoundError(
            f'HTML report template not found at: {template_file}'
        )

    with open(template_file, encoding='utf-8') as file:
        return file.read()


def _save_html_report(new_report_json_path: str, path) -> None:
    # Check if JSON report file exists before reading
    if not os.path.exists(new_report_json_path):
        raise FileNotFoundError(
            f'JSON report file not found at: {new_report_json_path}'
        )

    with open(new_report_json_path, 'r', encoding='utf-8') as file_json:
        report_json = file_json.read()

    content = _get_report_html_template().replace('__REPORT_DATA', report_json)

    try:
        with open(path, 'w+', encoding='utf-8') as file:
            file.write(content)
    except OSError as e:
        raise OSError(f'Failed to write HTML report: {str(e)}')


def save_report(logger, report_struct, dest_dir=''):

    if 'report_name' not in report_struct or not report_struct['report_name']:
        raise ValueError(
            "The 'report_name' field is missing or empty in the report structure."
        )

    if dest_dir == '':
        dest_dir = str(REPORT_FOLDER)

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)
        logger.info(f'Report directory was created: {dest_dir}')

    report_name = report_struct['report_name']

    new_report_json_path = os.path.join(dest_dir, f'{report_name}.json')
    new_report_html_path = os.path.join(dest_dir, f'{report_name}.html')

    _save_json_report(str(new_report_json_path), report_struct)
    _save_html_report(str(new_report_json_path), str(new_report_html_path))

    logger.info(
        'Reports generated: %s.json, %s.html',
        str(report_name),
        str(report_name),
    )
    logger.info("The report is saved in the 'report' folder")


def dump_updated_json(data: dict, output_file: str) -> None:
    # Use try-except to handle potential I/O errors
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        raise OSError(
            f'Failed to write updated JSON file {output_file}: {str(e)}'
        )


def parse_json_in_order(report) -> (List[dict], dict):
    # Validate the top-level structure
    if not isinstance(report, dict):
        raise ValueError('Report object must be a dictionary.')

    command_steps = []
    # Make sure "sections" is a dictionary or empty
    sections = report.get('sections')
    if not sections or not isinstance(sections, dict):
        # Return empty steps and the original report if no valid 'sections'
        return command_steps, report

    for section_name, section_obj in sections.items():
        # Check type of section_obj to avoid attribute errors
        if not isinstance(section_obj, dict):
            continue

        reports = section_obj.get('reports', {})
        if not isinstance(reports, dict):
            continue

        for report_name, report_obj in reports.items():
            if not isinstance(report_obj, dict):
                # Skip invalid items
                continue

            # Determine which command file/field is present
            if 'shell_command_file' in report_obj:
                cmd_type = 'shell_command'
                cmd_value = report_obj['shell_command_file']
            elif 'sql_command_file' in report_obj:
                cmd_type = 'sql_command'
                cmd_value = report_obj['sql_command_file']
            elif 'python_command' in report_obj:
                cmd_type = 'python_command'
                cmd_value = report_obj['python_command']
            else:
                # Skip items that do not contain any recognized command keys
                continue

            step_info = {
                'section': section_name,
                'report': report_name,
                'cmd_type': cmd_type,
                'cmd_value': cmd_value,
                'report_obj': report_obj,
            }
            command_steps.append(step_info)

    return command_steps, report
