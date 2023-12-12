from pydantic import BaseModel, Field
from typing import List, Dict

class ChartSeriesItem(BaseModel):
    name: str = Field(alias="name")
    data: list[list[float]] = Field(alias="data")

class ChartZoom(BaseModel):
    enabled: bool = Field(alias="enabled")

class ChartStroke(BaseModel):
    curve: str = Field(alias="curve")
    width: int = Field(alias="width")

class ChartTitle(BaseModel):
    text: str = Field(alias="text")
    align: str = Field(alias="align")

class ChartRowColors(BaseModel):
    colors: List[str] = Field(alias="colors")
    opacity: float = Field(alias="opacity")

class ChartRow(BaseModel):
    row: ChartRowColors = Field(alias="row")

class ChartYAxisTitle(BaseModel):
    title: Dict[str, str] = Field(alias="title")

class ChartXAxisTitle(BaseModel):
    title: Dict[str, str] = Field(alias="title")

class ChartView(BaseModel):
    height: int = Field(alias="height")
    type: str = Field(alias="type")
    zoom: ChartZoom = Field(alias="zoom")

class ChartData(BaseModel):
    series: List[ChartSeriesItem] = Field(alias="series")
    chart: ChartView = Field(alias="chart")
    dataLabels: ChartZoom = Field(alias="dataLabels")
    stroke: ChartStroke = Field(alias="stroke")
    title: ChartTitle = Field(alias="title")
    grid: ChartRow = Field(alias="grid")
    yaxis: ChartYAxisTitle = Field(alias="yaxis")
    xaxis: ChartXAxisTitle = Field(alias="xaxis")
