from collections.abc import Sequence

from backtest import Algo, DosVar, OrderReport, TradeReport
from scheme import ResearchContext

from .params import ExecutionParams

__all__ = ["ExecutionAlgo"]


class ExecutionAlgo[C: ResearchContext](Algo[ExecutionParams, C]):
    def initialize(self) -> None:
        pass

    def on_snapshot(self, msg: DosVar) -> None:
        pass

    def on_order(self, orders: Sequence[OrderReport]) -> None:
        pass

    def on_trade(self, trades: Sequence[TradeReport]) -> None:
        pass
