from pydantic import BaseModel
from scheme.base import ExecutionReportForm as BaseExecutionReportForm

__all__ = ["ExecutionReportForm"]


class ExecutionReportForm[P: BaseModel](BaseExecutionReportForm[P]):
    """当前项目的研究参数表单，可增加算法字段或覆盖默认值。"""
