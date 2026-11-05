from scheme import base

from .params import ExecutionAnalysisParams

__all__ = ["ExecutionReportForm"]


class ExecutionReportForm(base.ExecutionReportForm[ExecutionAnalysisParams]):
    """当前 Execution 项目的报告表单；由 Scheme 统一构造分析参数。"""
