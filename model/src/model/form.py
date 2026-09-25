from pydantic import BaseModel
from scheme.base import ModelReportForm as BaseModelReportForm

__all__ = ["ModelReportForm"]


class ModelReportForm[P: BaseModel](BaseModelReportForm[P]):
    """当前项目的研究参数表单，可增加算法字段或覆盖默认值。"""
