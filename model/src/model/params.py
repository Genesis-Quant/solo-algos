from pydantic import Field
from scheme.base import ModelParams as BaseModelParams

__all__ = ["ModelParams"]


class ModelParams(BaseModelParams):
    """在此定义当前算法使用的参数字段。"""

    n_select: int = Field(default=10, ge=1, title="选股数量")
