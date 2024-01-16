import os
import json
import logging
import difflib

from pg_perfbench.reports import schemas as report_schemas
from pg_perfbench.context import JoinContext
from pg_perfbench.const import PROJECT_ROOT_FOLDER
from pg_perfbench.const import get_datetime_report

log = logging.getLogger(__name__)

JOIN_TASKS_PATH = os.path.join(str(PROJECT_ROOT_FOLDER), 'join_tasks/')

REF_REPORT_IDX = 0

SECTION = 0
REPORT = 2


def _read_report_files(
    input_dir: str = '', ref_report: str = ''
) -> tuple[list[str], list[report_schemas.Report]] | None:
    rep_list = []
    rep_names_list = [file for file in os.listdir(input_dir) if file.endswith('.json')
                      if 'join' not in file]
    if ref_report and ref_report in rep_names_list:
        ref_index = rep_names_list.index(ref_report)
        rep_names_list[REF_REPORT_IDX], rep_names_list[ref_index] = rep_names_list[ref_index], rep_names_list[REF_REPORT_IDX]
    else:
        log.info('Not specified or incorrectly entered --reference-report')

    for file_name in rep_names_list:
        file_path = os.path.join(input_dir, file_name)
        with open(file_path, 'r') as file:
            report_data = json.load(file)
            report = report_schemas.Report(**report_data)
            rep_list.append(report)

    return rep_names_list, rep_list


def _comparing_reports(
    ref_rep: report_schemas.Report,
    compr_rep: report_schemas.Report,
    compare_items: list[list[str]],
) -> bool:

    for item in compare_items:
        sect_name = item[SECTION]
        rep_name = item[REPORT]
        if not _compare_report_data(
            ref_rep.sections[sect_name].reports[rep_name].data,
            compr_rep.sections[sect_name].reports[rep_name].data
        ):
            log.error(f'Comparison of reports failed for item: {sect_name}.{rep_name}')
            return False
    return True


def _compare_report_data(
    ref_data: str | list[list[str]], cmpr_data: str | list[list[str]]
) -> bool:
    if isinstance(ref_data, str) and isinstance(cmpr_data, str):
        if ref_data == cmpr_data:
            return True
        else:
            diff = difflib.ndiff(ref_data.splitlines(), cmpr_data.splitlines())
            print('\n'.join(diff))
            return False

    elif isinstance(ref_data, list) and isinstance(cmpr_data, list):
        if len(ref_data) != len(cmpr_data):
            print('The lengths of the main lists do not match.')
            return False

        all_equal = True
        for index, (sub_list1, sub_list2) in enumerate(zip(ref_data, cmpr_data)):
            if sub_list1 != sub_list2:
                print(f'Mismatch in sublist {index}: {sub_list1} != {sub_list2}')
                all_equal = False

        return all_equal

    return False


def join_reports(join_ctx: JoinContext) -> report_schemas.Report | None:
    joined_report = None
    rep_names, rep_list = _read_report_files(
        join_ctx.input_dir, join_ctx.reference_report
    )
    compare_items = [
        item.split('.')
        for item in json.load(open(os.path.join(JOIN_TASKS_PATH, join_ctx.join_task), 'r')
        ).get('items', [])
    ]

    if compare_items is None:
        return None

    joined_report = rep_list[REF_REPORT_IDX]

    joined_report.header = f'Result of joined reports {get_datetime_report("%d/%m/%Y %H:%M:%S")}'
    joined_report.description = rep_names[REF_REPORT_IDX]
    log.info(f'Reference report:{rep_names[REF_REPORT_IDX]}')
    for name, report in zip(rep_names[REF_REPORT_IDX+1:], rep_list[REF_REPORT_IDX+1:]):
        log.info(f'Comparing reports:{rep_names[REF_REPORT_IDX]}, {name}')
        if not _comparing_reports(rep_list[REF_REPORT_IDX], report, compare_items):
            log.error('Comparison of reports failed')
            return None

        joined_report.description = '\n'.join([joined_report.description, name])
        joined_report.sections['result'].reports['chart'].data['series'].append(
            report.sections['result'].reports['chart'].data['series'][0]
        )

    return joined_report
