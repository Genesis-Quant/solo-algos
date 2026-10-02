from datetime import date, timedelta
from typing import Literal

from pydantic import ConfigDict, Field
from scheme.base import FactorAnalysisParams as BaseFactorAnalysisParams
from scheme.base import FactorParams as BaseFactorParams
from scheme.base import ReportForm

from scheme import StockPool, Universe

__all__ = ["FactorAnalysisParams", "FactorParams", "FactorReportForm"]


class FactorParams(BaseFactorParams):
    """当前因子的运行参数；固定 20 日动量无需额外算法字段。"""


class FactorAnalysisParams(FactorParams, BaseFactorAnalysisParams):
    """当前因子的运行参数、分析设置与研究入口。"""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class FactorReportForm(ReportForm[FactorAnalysisParams]):
    """当前因子项目的报告表单；build 显式构造本项目分析参数。"""

    start: date = Field(title="开始日期")
    end: date = Field(title="结束日期（不含）")
    pool: Literal[
        StockPool.ALL, StockPool.SSE50, StockPool.CSI300, StockPool.CSI500, StockPool.CSI1000
    ] = Field(default=StockPool.ALL, title="股票池")
    lookback: timedelta = Field(default=timedelta(0), title="回溯周期")
    columns: list[str] = Field(
        default_factory=lambda: ["momentum"], min_length=1, title="因子列"
    )
    return_periods: list[int] = Field(
        default_factory=lambda: [1, 5, 20], min_length=1, title="收益持有期"
    )
    groups: int = Field(default=5, ge=2, title="分组数量")
    n_select: int = Field(default=2, ge=1, title="极端股票数")
    weight: Literal["equal", "market_value"] = Field(
        default="equal",
        title="加权方式",
        json_schema_extra={"x-enum-labels": ["等权", "市值加权"]},
    )
    calendar_symbol: str = Field(default="000300.XSHG", title="交易日历代码")

    def build(self) -> FactorAnalysisParams:
        return FactorAnalysisParams(
            **self.model_dump(exclude={"pool", "lookback"}),
            universe=Universe.model_validate({"pool": self.pool, "lookback": self.lookback}),
        )
