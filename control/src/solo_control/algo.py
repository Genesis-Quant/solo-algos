from abc import abstractmethod
from collections.abc import Sequence
from typing import Any

from scheme import ControlAlgo as BaseControlAlgo
from scheme import DosVar, OrderReport, ResearchContext, Target, TradeReport

from .params import ControlParams

__all__ = ["ControlAlgo"]


class ControlAlgo[C: ResearchContext[Any]](BaseControlAlgo[ControlParams, C]):
    @abstractmethod
    def on_target(self, target: Target) -> None:
        """根据目标权重生成并检查订单，写入 ctx.orders；上游消息已清空。"""
        ...

    def initialize(self) -> None:
        pass

    def on_snapshot(self, msg: DosVar) -> None:
        pass

    def on_order(self, orders: Sequence[OrderReport]) -> None:
        pass

    def on_trade(self, trades: Sequence[TradeReport]) -> None:
        pass
