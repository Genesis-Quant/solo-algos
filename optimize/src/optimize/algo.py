from abc import abstractmethod
from collections.abc import Sequence
from typing import Any

from scheme import DosVar, OrderReport, ResearchContext, Signal, TradeReport
from scheme import OptimizeAlgo as BaseOptimizeAlgo

from .params import OptimizeParams

__all__ = ["OptimizeAlgo"]


class OptimizeAlgo[C: ResearchContext[Any]](BaseOptimizeAlgo[OptimizeParams, C]):
    @abstractmethod
    def on_signal(self, signals: Signal[Any]) -> None:
        """根据传入信号计算目标资产权重，写入 ctx.target；上游消息已由基类清空。"""
        ...

    def initialize(self) -> None:
        pass

    def on_snapshot(self, msg: DosVar) -> None:
        pass

    def on_order(self, orders: Sequence[OrderReport]) -> None:
        pass

    def on_trade(self, trades: Sequence[TradeReport]) -> None:
        pass
