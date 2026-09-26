from scheme.base import ModelReportForm as BaseModelReportForm

from .params import ModelParams

__all__ = ["ModelReportForm"]


class ModelReportForm(ModelParams, BaseModelReportForm):
    """复用算法参数，附加 Scheme 的研究表单设置。"""
