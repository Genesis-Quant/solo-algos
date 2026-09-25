from pydantic import BaseModel
from scheme.base import OptimizeReportForm as BaseOptimizeReportForm

__all__ = ["OptimizeReportForm"]


class OptimizeReportForm[P: BaseModel](BaseOptimizeReportForm[P]):
    """当前项目的研究参数表单，可增加算法字段或覆盖默认值。"""
