from pydantic import ConfigDict, Field
from scheme import base

__all__ = ["ControlAnalysisParams", "ControlParams"]


class ControlParams(base.ControlParams):
    lot_size: int = Field(default=100, ge=1, title="每手股数")


class ControlAnalysisParams(ControlParams, base.ControlAnalysisParams):
    """当前算法参数与完整研究设置；额外字段供其他 Algo 读取。"""

    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
