from datetime import time
from typing import Any, Generic, TypeVar

import pandas as pd
from scheme import ExecutionAlgo as BaseExecutionAlgo
from scheme import Order, ResearchContext

from .params import ExecutionParams

__all__ = ["ExecutionAlgo"]

C = TypeVar("C", bound=ResearchContext[Any], infer_variance=True)


class ExecutionAlgo(BaseExecutionAlgo[ExecutionParams, C], Generic[C]):
    """初始实现不拆单，在可交易快照提交订单；可在此实现拆单逻辑。"""

    def can_execute(self) -> bool:
        now = pd.Timestamp(self.backtest.time).time()
        return time(9, 30) <= now < time(11, 30) or time(13) <= now < time(15)

    def on_orders(self, orders: list[Order]) -> None:
        now = pd.Timestamp(self.backtest.time).to_pydatetime()
        self.backtest.submit_orders(
            [order.model_copy(update={"time": now}) for order in orders]
        )
