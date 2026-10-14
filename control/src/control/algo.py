from typing import Any, Generic, TypeVar

from scheme import ControlAlgo as BaseControlAlgo
from scheme import ResearchContext, Target

from .params import ControlParams

__all__ = ["ControlAlgo"]

C = TypeVar("C", bound=ResearchContext[Any], infer_variance=True)


class ControlAlgo(BaseControlAlgo[ControlParams, C], Generic[C]):
    """初始实现接受全部订单；在 on_target 中增加逐单拒单条件。"""

    def on_target(self, target: Target) -> None:
        self.ctx.orders = self.target_orders(target, lot_size=self.params.lot_size)
