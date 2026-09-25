from abc import abstractmethod
from collections.abc import Sequence
from typing import Any

from scheme import DosVar, Order, OrderReport, ResearchContext, TradeReport
from scheme import ExecutionAlgo as BaseExecutionAlgo

from .params import ExecutionParams

__all__ = ["ExecutionAlgo"]


class ExecutionAlgo[C: ResearchContext[Any]](BaseExecutionAlgo[ExecutionParams, C]):
    @abstractmethod
    def on_orders(self, orders: list[Order]) -> None:
        """拆单后调用 backtest.submit_order；上游消息已由基类清空。"""
        ...

    def initialize(self) -> None:
        pass

    def on_snapshot(self, msg: DosVar) -> None:
        pass

    def on_order(self, orders: Sequence[OrderReport]) -> None:
        pass

    def on_trade(self, trades: Sequence[TradeReport]) -> None:
        pass
