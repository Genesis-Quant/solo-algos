from pydantic import ConfigDict, Field
from scheme.base import OptimizeAnalysisParams as BaseOptimizeAnalysisParams
from scheme.base import OptimizeParams as BaseOptimizeParams

__all__ = ["OptimizeAnalysisParams", "OptimizeParams"]


class OptimizeParams(BaseOptimizeParams):
    gross_exposure: float = Field(default=0.98, gt=0, le=1, title="总仓位")


class OptimizeAnalysisParams(OptimizeParams, BaseOptimizeAnalysisParams):
    """当前算法参数与完整研究设置；额外字段供其他 Algo 读取。"""

    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
