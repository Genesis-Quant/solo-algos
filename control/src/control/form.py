from scheme.base import ControlReportForm as BaseControlReportForm

from .params import ControlAnalysisParams

__all__ = ["ControlReportForm"]


class ControlReportForm(BaseControlReportForm[ControlAnalysisParams]):
    """当前 Control 项目的报告表单；由 Scheme 统一构造分析参数。"""
