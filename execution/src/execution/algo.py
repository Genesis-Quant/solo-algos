from datetime import time
from typing import Any

import pandas as pd
from scheme import ExecutionAlgo as BaseExecutionAlgo
from scheme import Order, ResearchContext
from .params import ExecutionParams

__all__ = ["ExecutionAlgo"]


class ExecutionAlgo[C: ResearchContext[Any]](BaseExecutionAlgo[ExecutionParams, C]):
    """初始实现不拆单，在可交易快照提交订单；可在此实现拆单逻辑。"""

    def process(self) -> bool:
        now = pd.Timestamp(self.backtest.time).time()
        if not (time(9, 30) <= now < time(11, 30) or time(13) <= now < time(15)):
            return False
        return super().process()

    def on_orders(self, orders: list[Order]) -> None:
        now = pd.Timestamp(self.backtest.time).to_pydatetime()
        for order in orders:
            self.backtest.submit_order(order.model_copy(update={"time": now}))
