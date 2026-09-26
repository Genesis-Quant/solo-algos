from collections.abc import Sequence
from datetime import timedelta
from typing import Any

import pandas as pd
from scheme import DosVar, OrderReport, ResearchContext, TradeReport
from scheme import ModelAlgo as BaseModelAlgo
from scheme.data import query
from scheme.data.dolphindb.symbols import source_symbol

from .params import ModelParams

__all__ = ["ModelAlgo"]


class ModelAlgo[C: ResearchContext[Any]](BaseModelAlgo[ModelParams, C]):
    """示例：收盘后选择股票池内近 20 个交易日收益最高的股票。"""

    def initialize(self) -> None:
        self.last_rebalance = None

    def on_snapshot(self, msg: DosVar) -> None:
        now = pd.Timestamp(self.backtest.time)
        if now.hour < 15 or self.last_rebalance == now.date():
            return
        members = self.backtest.universe.loc[now.normalize()]
        codes = members.index[members].tolist()
        if not codes:
            self.ctx.signal = {}
        else:
            with query(
                {
                    "start_date": (now.date() - timedelta(days=60)).isoformat(),
                    "end_date": now.date().isoformat(),
                    "codes": [source_symbol(code) for code in codes],
                    "factors": ["close", "adj_factor"],
                }
            ) as result:
                data = result.data
            adjusted = data.assign(price=data.close * data.adj_factor)
            prices = adjusted.pivot(
                index="time", columns="code", values="price"
            ).sort_index()
            scores = (
                prices.pct_change(20, fill_method=None).iloc[-1].dropna()
                if not prices.empty
                else pd.Series(dtype=float)
            )
            self.ctx.signal = {
                symbol: 1.0 for symbol in scores.nlargest(self.params.n_select).index
            }
        self.last_rebalance = now.date()

    def on_order(self, orders: Sequence[OrderReport]) -> None:
        pass

    def on_trade(self, trades: Sequence[TradeReport]) -> None:
        pass
