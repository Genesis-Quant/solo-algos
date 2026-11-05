from pydantic import ConfigDict
from scheme import base

__all__ = ["ExecutionAnalysisParams", "ExecutionParams"]


class ExecutionParams(base.ExecutionParams):
    """在此定义当前算法使用的参数字段。"""


class ExecutionAnalysisParams(ExecutionParams, base.ExecutionAnalysisParams):
    """当前算法参数与完整研究设置；额外字段供其他 Algo 读取。"""

    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
