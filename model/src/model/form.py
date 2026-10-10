from scheme.base import ModelReportForm as BaseModelReportForm

from .params import ModelAnalysisParams

__all__ = ["ModelReportForm"]


class ModelReportForm(BaseModelReportForm[ModelAnalysisParams]):
    """当前 Model 项目的报告表单；由 Scheme 统一构造分析参数。"""
