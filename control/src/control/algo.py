from typing import Any, Generic, TypeVar

from scheme import base

from .params import ControlParams

__all__ = ["ControlAlgo"]

C = TypeVar("C", bound=base.ResearchContext[Any], infer_variance=True)


class ControlAlgo(base.ControlAlgo[ControlParams, C], Generic[C]):
    """初始实现接受全部订单；在 on_target 中增加逐单拒单条件。"""

    def on_target(self, target: base.Target) -> None:
        self.ctx.orders = self.target_orders(target, lot_size=self.params.lot_size)
