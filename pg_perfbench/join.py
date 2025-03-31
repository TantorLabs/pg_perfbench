import os
import json
import difflib

from pg_perfbench.const import (
    PROJECT_ROOT_FOLDER,
    DEFAULT_REPORT_NAME,
    get_datetime_report,
)
from pg_perfbench.log import display_user_configuration
from pg_perfbench.report.processing import parse_json_in_order

JOIN_TASKS_PATH = os.path.join(str(PROJECT_ROOT_FOLDER), 'join_tasks')
REF_REPORT_IDX = 0


def _load_reports(
    logger, input_dir: str, reference_report: str
) -> tuple[list[str], list[dict]] | None:
    if not os.path.isdir(input_dir):
        logger.error(f'Invalid directory: {input_dir}')
        return None
    files = [
        f
        for f in sorted(os.listdir(input_dir))
        if f.endswith('.json') and 'join' not in f
    ]
    if not files:
        logger.error(f'No JSON files in {input_dir}')
        return None
    if reference_report in files:
        idx = files.index(reference_report)
        files[0], files[idx] = files[idx], files[0]
    reports = []
    for f in files:
        path = os.path.join(input_dir, f)
        try:
            with open(path, 'r', encoding='utf-8') as rf:
                data = json.load(rf)
                if isinstance(data, dict):
                    reports.append(data)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f'Cannot load {f}: {e}')
    return (files, reports) if reports else None


def _load_compare_items(logger, join_tasks_file: str) -> list[str] | None:
    path = os.path.join(JOIN_TASKS_PATH, join_tasks_file)
    if not os.path.isfile(path):
        logger.error(f'join_tasks not found: {path}')
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        items = data.get('items')
        return items if isinstance(items, list) else None
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f'Cannot parse join_tasks: {e}')
        return None


def _compare_data(logger, ref_data, cmp_data) -> bool:
    if isinstance(ref_data, str) and isinstance(cmp_data, str):
        if ref_data != cmp_data:
            diff = difflib.ndiff(ref_data.splitlines(), cmp_data.splitlines())
            logger.debug('\n'.join(diff))
            return False
        return True
    if isinstance(ref_data, list) and isinstance(cmp_data, list):
        if len(ref_data) != len(cmp_data):
            logger.debug('List length mismatch')
            return False
        for i, (r, c) in enumerate(zip(ref_data, cmp_data)):
            if r != c:
                logger.debug(f'Row mismatch at {i}: {r} != {c}')
                return False
        return True
    return False


def _compare_reports(
    logger, ref_rep: dict, cmp_rep: dict, compare_items: list[str]
) -> bool:
    ref_steps, _ = parse_json_in_order(ref_rep)
    cmp_steps, _ = parse_json_in_order(cmp_rep)
    if len(ref_steps) != len(cmp_steps):
        raise ValueError('Different step counts')
    for i, (s1, s2) in enumerate(zip(ref_steps, cmp_steps)):
        if s1['section'] != s2['section'] or s1['report'] != s2['report']:
            raise ValueError(f'Step mismatch at {i}')
        if s1['section'] == 'result':
            continue
        left = s1['report_obj'].get('data')
        right = s2['report_obj'].get('data')
        if not _compare_data(logger, left, right):
            ck = f'sections.{s1["section"]}.reports.{s1["report"]}.data'
            if ck in compare_items:
                raise ValueError(
                    f'Unlisted mismatch in "{s1["report"]}"\n'
                    f'reference report - {ref_rep["report_name"]}\n'
                    f'comparable report - {cmp_rep["report_name"]}'
                )
            else:
                if 'Diff' in s1['report_obj'].get('header', ''):
                    s1['report_obj']['data'].append(
                        [cmp_rep.get('report_name', 'Unnamed'), right]
                    )
                else:
                    s1['report_obj']['data'] = [
                        [ref_rep.get('report_name', 'Unnamed'), left],
                        [cmp_rep.get('report_name', 'Unnamed'), right],
                    ]
                    old_hdr = s1['report_obj'].get('header', '')
                    s1['report_obj']['header'] = f'{old_hdr} | Diff'
    return True


def _add_result(base: dict, inc: dict) -> None:
    chart_series = (
        base.get('sections', {})
        .get('result', {})
        .get('reports', {})
        .get('chart', {})
        .get('data', {})
        .get('series', [])
    )
    inc_series = (
        inc.get('sections', {})
        .get('result', {})
        .get('reports', {})
        .get('chart', {})
        .get('data', {})
        .get('series', [])
    )
    if inc_series:
        inc_series[0]['name'] = inc.get('report_name', 'Unnamed')
        chart_series.append(inc_series[0])

    base_outputs = (
        base.get('sections', {})
        .get('result', {})
        .get('reports', {})
        .get('pgbench_outputs', {})
    )
    inc_outputs = (
        inc.get('sections', {})
        .get('result', {})
        .get('reports', {})
        .get('pgbench_outputs', {})
    )
    if 'data' not in base_outputs or not isinstance(base_outputs['data'], list):
        base_outputs['data'] = []
    if 'data' in inc_outputs and isinstance(inc_outputs['data'], list):
        base_outputs['data'].append(
            [inc.get('report_name', 'Unnamed'), inc_outputs['data']]
        )

    base_logs = (
        base.get('sections', {})
        .get('result', {})
        .get('reports', {})
        .get('logs', {})
    )
    inc_logs = (
        inc.get('sections', {})
        .get('result', {})
        .get('reports', {})
        .get('logs', {})
    )

    if base_logs == {} and inc_logs != {}:
        base['sections']['result']['reports']['logs'] = {
            'header': 'database logs',
            'description': 'Local path to the database log archive',
            'item_type': 'link',
            'state': 'collapsed',
            'python_command': '',
            'data': [],
        }
        base_logs = base['sections']['result']['reports']['logs']
    if 'data' in base_logs and isinstance(inc_logs['data'], str):
        base_logs['data'].append(
            [inc.get('report_name', 'Unnamed'), inc_logs['data']]
        )


def _merge_reports(
    logger, names: list[str], reports: list[dict], compare_items: list[str]
) -> dict | None:
    ref = reports[0]
    if not isinstance(ref, dict):
        logger.error('Invalid reference report')
        return None
    try:
        ref['sections']['result']['reports']['chart']['data']['series'][0]['name'] = ref.get('report_name', 'Unnamed')
        ref['sections']['result']['reports']['pgbench_outputs']['data'] = [
            [
                ref.get('report_name', 'Unnamed'),
                ref['sections']['result']['reports']['pgbench_outputs'].get('data', [])
            ]
        ]
        if 'logs' in ref['sections']['result']['reports']:
            ref['sections']['result']['reports']['logs']['data'] = [
                [
                    ref.get('report_name', 'Unnamed'),
                    ref['sections']['result']['reports']['logs'].get('data', '')
                ]
            ]
    except Exception:
        logger.warning('Incomplete structure in reference report')
    for name, r in zip(names, reports):
        if names.index(name) == 0:
            continue
        try:
            _compare_reports(logger, reports[0], r, compare_items)
        except ValueError as ve:
            logger.error(f'Comparison failed: {ve}')
            return None
        _add_result(ref, r)
    ref['header'] = f'Result of joined reports {get_datetime_report("%d/%m/%Y %H:%M:%S")}'
    return ref


def join_reports(
    raw_args: dict,
    join_tasks: str,
    reference_report: str,
    input_dir: str,
    report_name: str,
    logger,
) -> dict | None:
    if raw_args and isinstance(raw_args, dict):
        display_user_configuration(raw_args, logger)

    if not join_tasks:
        logger.error('No join_tasks specified.')
        return None

    compare_items = _load_compare_items(logger, join_tasks)
    if not compare_items:
        logger.error('No compare_items found.')
        return None
    tasks_list = '\n'.join(compare_items)
    logger.info(
        f'Compare items "{join_tasks}" loaded successfully:\n{tasks_list}'
    )

    loaded = _load_reports(logger, input_dir, reference_report)
    if not loaded:
        logger.error('No reports loaded from input directory.')
        return None
    names, rpts = loaded
    logger.info(f'Loaded {len(names)} report(s): {", ".join(names)}')

    joined = _merge_reports(logger, names, rpts, compare_items)
    if not joined:
        logger.error('Merge of reports failed.')
        return None
    logger.info('Reports merged successfully.')

    joined['report_name'] = report_name or f'join_{DEFAULT_REPORT_NAME}'

    all_names = '\n'.join(names)
    tasks_path = os.path.join(JOIN_TASKS_PATH, join_tasks)
    try:
        with open(tasks_path, 'r', encoding='utf-8') as tf:
            tasks_content = tf.read()
        logger.info('Join tasks file read successfully.')
    except OSError as e:
        tasks_content = f'Cannot read tasks: {e}'
        logger.error(tasks_content)

    joined['description'] = f'\nComparison Reports:\n{all_names}\n\nJoined by:\n{tasks_content}'
    logger.info('Join reports process completed successfully.')
    return joined
