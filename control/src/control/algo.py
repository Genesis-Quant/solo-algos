from typing import Any

from scheme import ResearchContext, Target
from scheme import ControlAlgo as BaseControlAlgo
from .params import ControlParams

__all__ = ["ControlAlgo"]


class ControlAlgo[C: ResearchContext[Any]](BaseControlAlgo[ControlParams, C]):
    """初始实现接受全部订单；在 on_target 中增加逐单拒单条件。"""

    def on_target(self, target: Target) -> None:
        self.ctx.orders = self.target_orders(target, lot_size=self.params.lot_size)
