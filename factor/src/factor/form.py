from scheme.base import FactorReportForm as BaseFactorReportForm

from .params import FactorAnalysisParams

__all__ = ["FactorReportForm"]


class FactorReportForm(BaseFactorReportForm[FactorAnalysisParams]):
    """当前因子项目的报告表单；由 Scheme 统一构造分析参数。"""
