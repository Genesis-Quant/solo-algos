from pydantic import Field
from scheme.base import ControlParams as BaseControlParams

__all__ = ["ControlParams"]


class ControlParams(BaseControlParams):
    lot_size: int = Field(default=100, ge=1, title="每手股数")
