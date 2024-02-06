import logging
from typing import Any
from typing import Union
from typing import Literal
from pathlib import Path

from pydantic import BaseModel

from pg_perfbench.compatibility import StrEnum
from pg_perfbench.const import SHELL_COMMANDS_PATH
from pg_perfbench.const import SQL_COMMANDS_PATH

log = logging.getLogger(__name__)


class StateTypes(StrEnum):
    EXPANDED = 'expanded'
    COLLAPSED = 'collapsed'
    HIDDEN = 'hidden'


class ReportTypes(StrEnum):
    PLAIN_TEXT = 'plain_text'
    TABLE = 'table'
    CHART = 'chart'
    LINK = 'link'


class BaseReportItem(BaseModel):
    header: str
    item_type: str
    data: Any
    state: str

    def set_data(self, data: Any) -> None:
        ...


class BaseReportPlainText(BaseReportItem):
    item_type: Literal[ReportTypes.PLAIN_TEXT]
    data: str | list[list[str]]

    def set_data(self, text: str):
        self.data = text


class BaseReportTable(BaseReportItem):
    item_type: Literal[ReportTypes.TABLE]
    theader: list[str]
    data: list[list[str | float | Any]] | str

    def set_data(self, data: list[Any]):
        ...


class BaseReportChart(BaseReportItem):
    item_type: Literal[ReportTypes.CHART]
    data: dict | str
    description: str

    def set_data(self, data: dict[Any]) -> None:
        self.data['series'].append(data)


def read_file(file: str, file_path: Path) -> str:
    with open(file_path / file) as file_content:
        return file_content.read()


class BaseReportShellCommand(BaseModel):
    shell_command_file: str

    def get_shell_raw_script(self) -> str:
        command = read_file(file=self.shell_command_file, file_path=SHELL_COMMANDS_PATH)
        return command


class BaseReportSQLCommand(BaseModel):
    sql_command_file: str

    def get_sql_raw_script(self) -> str:
        command = read_file(file=self.sql_command_file, file_path=SQL_COMMANDS_PATH)
        return command

    def set_data(self, fetch_result):
        ...

    async def fetch(self, dbconn, cmd: str):
        ...


class BaseReportPythonCommand(BaseModel):
    python_command: str

    def get_python_func_name(self):
        return self.python_command


class ItemPlainTextShell(BaseReportShellCommand, BaseReportPlainText):
    async def set_data(self, connection):
        try:
            self.data = await connection.bash_command(self.get_shell_raw_script())
        except Exception as e:
            log.error(f'{self.shell_command_file} execution error: {str(e.text_error)}')
            self.data = str(e.text_error)


class ItemPlainTextSQL(BaseReportSQLCommand, BaseReportPlainText):
    async def set_data(self, dbconn):
        try:
            self.data = await dbconn.fetchval(self.get_sql_raw_script())
        except Exception as e:
            text_error = f'{self.sql_command_file} execution error: {str(e)}'
            log.error(text_error)
            self.data = text_error


class ItemPlainTextPython(BaseReportPythonCommand, BaseReportPlainText):
    ...


class ItemTableShell(BaseReportShellCommand, BaseReportTable):
    ...


class ItemTableSQL(BaseReportSQLCommand, BaseReportTable):
    async def set_data(self, dbconn):
        try:
            fetch_result = await dbconn.fetch(self.get_sql_raw_script())
            self.theader = [key for key in fetch_result[0].keys()]
            self.data = [list(record) for record in fetch_result]
        except Exception as e:
            text_error = f'{self.sql_command_file} execution error: {str(e)}'
            log.error(text_error)
            self.data = text_error
            self.item_type = ReportTypes.PLAIN_TEXT


class ItemTablePython(BaseReportPythonCommand, BaseReportTable):
    def set_data(self, table_data):
        self.theader = table_data.theader
        self.data = table_data.data


class ItemLink(BaseReportItem, BaseReportPythonCommand):
    item_type: Literal[ReportTypes.LINK]
    description: str
    def set_data(self, data: Any) -> None:
        self.data = data


class ItemChartShell(BaseReportShellCommand, BaseReportChart):
    ...


class ItemChartSQL(BaseReportSQLCommand, BaseReportChart):
    ...


class ItemChartPython(BaseReportPythonCommand, BaseReportChart):
    ...


class SectionItemReports(BaseModel):
    reports: dict[
        str,
        Union[
            ItemPlainTextShell,
            ItemPlainTextSQL,
            ItemPlainTextPython,
            ItemTableShell,
            ItemTableSQL,
            ItemTablePython,
            ItemChartShell,
            ItemChartSQL,
            ItemChartPython,
            ItemLink
        ],
    ]
