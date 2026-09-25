from datetime import date

from pydantic import Field
from scheme.base import FactorReportForm as BaseFactorReportForm

__all__ = ["FactorReportForm"]


class FactorReportForm(BaseFactorReportForm):
    """当前因子项目的报告表单默认值。"""

    start: date = Field(default=date(2026, 1, 1), title="开始日期")
    end: date = Field(default=date(2026, 7, 1), title="结束日期（不含）")
    columns: list[str] = Field(
        default_factory=lambda: ["momentum"], min_length=1, title="因子列"
    )
    n_select: int = Field(default=2, ge=1, title="极端股票数")
