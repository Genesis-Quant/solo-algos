from pydantic import ConfigDict, Field
from scheme.base import ModelAnalysisParams as BaseModelAnalysisParams
from scheme.base import ModelParams as BaseModelParams

__all__ = ["ModelAnalysisParams", "ModelParams"]


class ModelParams(BaseModelParams):
    """在此定义当前算法使用的参数字段。"""

    n_select: int = Field(default=10, ge=1, title="选股数量")


class ModelAnalysisParams(ModelParams, BaseModelAnalysisParams):
    """当前算法参数与完整研究设置；额外字段供其他 Algo 读取。"""

    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
