from scheme.base import ExecutionReportForm as BaseExecutionReportForm

from .params import ExecutionParams

__all__ = ["ExecutionReportForm"]


class ExecutionReportForm(ExecutionParams, BaseExecutionReportForm):
    """复用算法参数，附加 Scheme 的研究表单设置。"""
