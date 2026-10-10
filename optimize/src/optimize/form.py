from scheme.base import OptimizeReportForm as BaseOptimizeReportForm

from .params import OptimizeAnalysisParams

__all__ = ["OptimizeReportForm"]


class OptimizeReportForm(BaseOptimizeReportForm[OptimizeAnalysisParams]):
    """当前 Optimize 项目的报告表单；由 Scheme 统一构造分析参数。"""
