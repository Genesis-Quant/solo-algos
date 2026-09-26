from pydantic import Field
from scheme.base import OptimizeParams as BaseOptimizeParams

__all__ = ["OptimizeParams"]


class OptimizeParams(BaseOptimizeParams):
    gross_exposure: float = Field(default=0.98, gt=0, le=1, title="总仓位")
