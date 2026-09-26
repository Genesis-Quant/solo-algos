from scheme.base import OptimizeReportForm as BaseOptimizeReportForm

from .params import OptimizeParams

__all__ = ["OptimizeReportForm"]


class OptimizeReportForm(OptimizeParams, BaseOptimizeReportForm):
    """复用算法参数，附加 Scheme 的研究表单设置。"""
