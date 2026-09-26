from scheme.base import ControlReportForm as BaseControlReportForm

from .params import ControlParams

__all__ = ["ControlReportForm"]


class ControlReportForm(ControlParams, BaseControlReportForm):
    """复用算法参数，附加 Scheme 的研究表单设置。"""
