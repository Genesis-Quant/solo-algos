from pydantic import BaseModel
from scheme.base import ControlReportForm as BaseControlReportForm

__all__ = ["ControlReportForm"]


class ControlReportForm[P: BaseModel](BaseControlReportForm[P]):
    """当前项目的研究参数表单，可增加算法字段或覆盖默认值。"""
