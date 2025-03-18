import json
import re
import subprocess
import os

from pg_perfbench.const import (
    SHELL_COMMANDS_PATH, SQL_COMMANDS_PATH, DEFAULT_LOG_ARCHIVE_NAME,
    LOCAL_DB_LOGS_PATH, WorkloadTypes
)
from pg_perfbench.report.processing import parse_json_in_order


def get_script_text(full_script_path) -> str:
    # check if file exists before reading
    if not os.path.exists(full_script_path):
        raise FileNotFoundError(f"Script file not found: {full_script_path}")

    try:
        with open(full_script_path, 'r', encoding='utf-8') as file_content:
            return file_content.read()
    except OSError as e:
        raise OSError(f"Failed to open or read script file {full_script_path}: {e}")


async def run_shell_command(conn, item):
    # check necessary fields in item
    shell_cmd_file = item.get('shell_command_file')
    if not shell_cmd_file:
        print("Missing 'shell_command_file' in item. Skipping execution.")
        return

    raw_script_text = get_script_text(SHELL_COMMANDS_PATH / shell_cmd_file)

    try:
        if item.get('item_type') == 'plain_text':
            # for plain_text, simply run the command and store output
            item['data'] = await conn.run_command(raw_script_text)

        elif item.get('item_type') == 'table':
            # for table, we expect JSON output from shell command
            data_str = await conn.run_command(raw_script_text)
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON from shell command output: {str(e)}")
                return

            if not isinstance(data, list):
                print("Unexpected data format from shell command. A list of dicts is expected.")
                return

            # Ensure 'theader' is a list in item
            if 'theader' not in item or not isinstance(item['theader'], list):
                item['theader'] = []

            if 'data' not in item or not isinstance(item['data'], list):
                item['data'] = []

            # Build table headers and rows
            for obj in data:
                if not isinstance(obj, dict):
                    print(f"Skipping invalid object in shell command output: {obj}")
                    continue
                for key in obj.keys():
                    if key not in item['theader']:
                        item['theader'].append(key)

            for obj in data:
                if isinstance(obj, dict):
                    row = []
                    for key in item['theader']:
                        row.append(obj.get(key, None))
                    item['data'].append(row)

        else:
            print(f"Unknown item_type in shell_command: {item.get('item_type')}")

    except Exception as e:
        print(f'Execution of command \"{shell_cmd_file}\" was failed:\n {str(e)}')


async def run_sql_command(dbconn, item):
    sql_cmd_file = item.get('sql_command_file')
    if not sql_cmd_file:
        print("Missing 'sql_command_file' in item. Skipping execution.")
        return

    raw_script_text = get_script_text(SQL_COMMANDS_PATH / sql_cmd_file)

    try:
        item_type = item.get('item_type')
        if item_type == 'plain_text':
            # fetch a single value
            item['data'] = await dbconn.fetchval(raw_script_text)

        elif item_type == 'table':
            # fetch multiple rows
            fetch_result = await dbconn.fetch(raw_script_text)
            if fetch_result:
                item['theader'] = [key for key in fetch_result[0].keys()]
                item['data'] = [list(record) for record in fetch_result]
            else:
                # If no data returned
                item['theader'] = []
                item['data'] = []

        else:
            print(f"Unknown item_type in sql_command: {item_type}")

    except Exception as e:
        print(f'Execution of command \"{sql_cmd_file}\" was failed:\n {str(e)}')


def args(report_data, item):
    # build a table of (arg, value) from report_data['args']
    if 'args' not in report_data or not isinstance(report_data['args'], dict):
        item['data'] = "No 'args' in report_data or invalid type"
        return

    item['theader'] = ['arg', 'value']
    item['data'] = [[key, str(value)] for key, value in report_data['args'].items()]


def get_workload_cmds(report_data):
    # retrieve workload commands with replaced placeholders
    workload_conf = report_data.get('workload_conf', {})
    if not workload_conf or not isinstance(workload_conf, dict):
        return []

    workload_command = workload_conf.get('workload_command')
    iter_list = workload_conf.get('pgbench_iter_list')
    iter_name = workload_conf.get('pgbench_iter_name')

    if not workload_command or not iter_list or not iter_name:
        return []

    pgbench_cmds = []
    placeholder = f'ARG_{str(iter_name).upper()}'
    for iteration in iter_list:
        workload_cmd_iter = workload_command.replace(placeholder, str(iteration))
        pgbench_cmds.append(workload_cmd_iter)

    return pgbench_cmds


def pgbench_options_table(report_data, item):
    # build a table "iteration number -> pgbench_options"
    pgbench_cmds = get_workload_cmds(report_data)
    item['theader'] = ['iteration number', 'pgbench_options']
    item['data'] = [[idx, cmd] for idx, cmd in enumerate(pgbench_cmds)]


def workload_tables(report_data, item):
    # show .sql content or commands for init phase
    workload_conf = report_data.get('workload_conf', {})
    if not workload_conf or not isinstance(workload_conf, dict):
        item['data'] = "No 'workload_conf' found in report_data"
        return

    btype = workload_conf.get('benchmark_type')
    if btype == WorkloadTypes.CUSTOM:
        init_command = str(workload_conf.get('init_command', ''))
        init_command = init_command.replace(
            'ARG_WORKLOAD_PATH', str(workload_conf.get('workload_path', ''))
        )
        pattern = re.compile(r'(?:(?:-f|--file=)\s*)?(\S+\.sql)')
        matches = pattern.findall(init_command)
        matches = [match for match in matches if match]

        data = ''
        for m in matches:
            if not os.path.exists(m):
                data += f"File not found: {m}\n\n"
                continue
            try:
                with open(m, 'r', encoding='utf-8') as f:
                    content = f.read()
                data += f'{m} :\n{content}\n\n'
            except OSError as e:
                data += f'Error reading file {m}: {str(e)}\n\n'

        item['data'] = data

    elif btype == WorkloadTypes.DEFAULT:
        item['data'] = str(workload_conf.get('init_command', ''))

    else:
        item['data'] = f"Unknown or missing benchmark_type: {btype}"


def workload(report_data, item):
    # show .sql content or commands for workload phase
    workload_conf = report_data.get('workload_conf', {})
    if not workload_conf or not isinstance(workload_conf, dict):
        item['data'] = "No 'workload_conf' found in report_data"
        return

    btype = workload_conf.get('benchmark_type')
    if btype == WorkloadTypes.CUSTOM:
        pgbench_command = str(workload_conf.get('workload_command', ''))
        pgbench_command = pgbench_command.replace(
            'ARG_WORKLOAD_PATH', str(workload_conf.get('workload_path', ''))
        )
        pattern = re.compile(r'(?:(?:-f|--file=)\s*)?(\S+\.sql)')
        matches = pattern.findall(pgbench_command)
        matches = [match for match in matches if match]

        data = ''
        for m in matches:
            if not os.path.exists(m):
                data += f"File not found: {m}\n\n"
                continue
            try:
                with open(m, 'r', encoding='utf-8') as f:
                    content = f.read()
                data += f'{m} :\n{content}\n\n'
            except OSError as e:
                data += f'Error reading file {m}: {str(e)}\n\n'

        item['data'] = data

    elif btype == WorkloadTypes.DEFAULT:
        item['data'] = str(workload_conf.get('workload_command', ''))

    else:
        item['data'] = f"Unknown or missing benchmark_type: {btype}"


def benchmark_result(report_data, item):
    # turn 'pgbench_outputs' into a table
    if 'pgbench_outputs' not in report_data:
        item['data'] = "No 'pgbench_outputs' in report_data"
        return

    results = report_data['pgbench_outputs']
    if not isinstance(results, list):
        item['data'] = "pgbench_outputs is not a list"
        return

    item['theader'] = [
        'clients',
        'duration',
        'number of transactions actually processed',
        'latency average',
        'initial connection time',
        'tps',
    ]
    item['data'] = results


def chart_tps_clients(report_data, item):
    # fill chart data with tps vs iteration
    if ('workload_conf' not in report_data or
            'pgbench_iter_list' not in report_data['workload_conf']):
        item['data'] = "Missing 'workload_conf' or 'pgbench_iter_list'"
        return

    if 'pgbench_outputs' not in report_data:
        item['data'] = "Missing 'pgbench_outputs'"
        return

    iter_list = report_data['workload_conf']['pgbench_iter_list']
    outputs = report_data['pgbench_outputs']

    if not isinstance(iter_list, list) or not isinstance(outputs, list):
        item['data'] = "Invalid 'pgbench_iter_list' or 'pgbench_outputs' type"
        return

    if len(iter_list) != len(outputs):
        item['data'] = "Mismatched length between 'pgbench_iter_list' and 'pgbench_outputs'"
        return

    param_name = report_data['workload_conf'].get('pgbench_iter_name', 'iteration')
    report_name = report_data.get('report_conf', {}).get('report_name', 'N/A')

    # build the chart structure in 'item["data"]'
    item['data'].update(
        {
            'title': {
                'text': f'tps({param_name})'
            },
            'xaxis': {
                'title': {
                    'text': param_name
                }
            },
            'series': [
                {
                    'name': f'{report_name},tps',
                    'data': [
                        [x, round(val[5], 1)]
                        for x, val in zip(iter_list, outputs)
                        if isinstance(val, list) and len(val) >= 6
                    ],
                }
            ]
        }
    )


async def collect_logs(logger, connect, remote_logs_path, report_name: str = DEFAULT_LOG_ARCHIVE_NAME):
    # check if remote_logs_path is provided
    if not remote_logs_path:
        print("Remote logs path is not provided. Skipping log collection.")
        return None

    if logger:
        logger.info(f"Copying logs from {remote_logs_path} -> {LOCAL_DB_LOGS_PATH}/{report_name}")

    data = await connect.copy_db_log_files(remote_logs_path, LOCAL_DB_LOGS_PATH, report_name)
    if data:
        report_item = {
            'header': 'database logs',
            'description': 'Local path to the database log archive',
            'item_type': 'link',
            'state': 'collapsed',
            'python_command': 'collect_logs',
            'data': data
        }

        if logger:
            logger.info(f"The log archive has been collected to: {report_item['data']}")
        return {
            'logs': report_item
        }
    else:
        logger.error('Error collecting db log files')
        return None


async def execute_steps_in_order(logger, command_steps, report_data, conn, db) -> None:
    # validate command_steps is a list
    if not isinstance(command_steps, list):
        if logger:
            logger.error("Command_steps is not a valid list. Skipping.")
        return

    for step in command_steps:
        cmd_type = step.get('cmd_type')
        report_obj = step.get('report_obj')
        if not report_obj:
            if logger:
                logger.warning("Missing 'report_obj' in step. Skipping.")
            continue

        if cmd_type == 'shell_command':
            await run_shell_command(conn, report_obj)

        elif cmd_type == 'sql_command':
            # skip if db is None
            if db:
                await run_sql_command(db, report_obj)
            else:
                if logger:
                    logger.error("No database connection provided for sql_command. Skipping.")

        elif cmd_type == 'python_command':
            func_name = report_obj.get('python_command')
            possible_func = globals().get(func_name)
            if callable(possible_func):
                possible_func(report_data, report_obj)
            else:
                report_obj['data'] = f'Not found or is not a function: {func_name}'
        else:
            output_str = f'Unknown command type {cmd_type}'
            report_obj['data'] = output_str


async def fill_info_report(logger, conn, db, workload_conf, report):
    # We parse the report to get steps in order
    command_steps, json_data = parse_json_in_order(report)
    if not command_steps:
        # If there's nothing to process
        return
    # Then execute them as usual
    await execute_steps_in_order(logger, command_steps, workload_conf, conn, db)
