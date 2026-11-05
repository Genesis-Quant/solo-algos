from pydantic import ConfigDict, Field
from scheme import base

__all__ = ["OptimizeAnalysisParams", "OptimizeParams"]


class OptimizeParams(base.OptimizeParams):
    gross_exposure: float = Field(default=0.98, ge=0, le=1, title="总仓位")


class OptimizeAnalysisParams(OptimizeParams, base.OptimizeAnalysisParams):
    """当前算法参数与完整研究设置；额外字段供其他 Algo 读取。"""

    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
