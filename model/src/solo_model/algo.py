from collections.abc import Sequence
from typing import Any

from backtest import Algo, DosVar, OrderReport, TradeReport
from scheme import ResearchContext

from .params import ModelParams

__all__ = ["ModelAlgo"]


class ModelAlgo[C: ResearchContext[Any]](Algo[ModelParams, C]):
    def initialize(self) -> None:
        pass

    def on_snapshot(self, msg: DosVar) -> None:
        pass

    def on_order(self, orders: Sequence[OrderReport]) -> None:
        pass

    def on_trade(self, trades: Sequence[TradeReport]) -> None:
        pass
