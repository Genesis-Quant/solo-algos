from pydantic import ConfigDict
from scheme.base import ExecutionAnalysisParams as BaseExecutionAnalysisParams
from scheme.base import ExecutionParams as BaseExecutionParams

__all__ = ["ExecutionAnalysisParams", "ExecutionParams"]


class ExecutionParams(BaseExecutionParams):
    """在此定义当前算法使用的参数字段。"""


class ExecutionAnalysisParams(ExecutionParams, BaseExecutionAnalysisParams):
    """当前算法参数与完整研究设置；额外字段供其他 Algo 读取。"""

    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
