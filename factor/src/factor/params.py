from scheme.base import FactorAnalysisParams as BaseFactorAnalysisParams
from scheme.base import FactorParams as BaseFactorParams
from scheme.base import FactorReportForm as BaseFactorReportForm

__all__ = ["FactorAnalysisParams", "FactorParams", "FactorReportForm"]


class FactorParams(BaseFactorParams):
    """当前因子的运行参数；固定 20 日动量无需额外算法字段。"""


class FactorAnalysisParams(FactorParams, BaseFactorAnalysisParams):
    """当前因子的运行参数、分析设置与研究入口；配置沿用基类。"""


class FactorReportForm(BaseFactorReportForm[FactorAnalysisParams]):
    """当前因子项目的报告表单；由 Scheme 统一构造分析参数。"""
