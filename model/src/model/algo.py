from collections.abc import Sequence
from typing import Any

from scheme import DosVar, OrderReport, ResearchContext, TradeReport
from scheme import ModelAlgo as BaseModelAlgo

from .params import ModelParams

__all__ = ["ModelAlgo"]


class ModelAlgo[C: ResearchContext[Any]](BaseModelAlgo[ModelParams, C]):
    def initialize(self) -> None:
        pass

    def on_snapshot(self, msg: DosVar) -> None:
        pass

    def on_order(self, orders: Sequence[OrderReport]) -> None:
        pass

    def on_trade(self, trades: Sequence[TradeReport]) -> None:
        pass
