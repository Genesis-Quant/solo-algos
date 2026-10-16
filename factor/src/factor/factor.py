from datetime import date, timedelta

import pandas as pd
from scheme.data.dolphindb.symbols import engine_symbol

from scheme import Factor as BaseFactor
from scheme import Universe

from .params import FactorParams

__all__ = ["Factor"]


class Factor(BaseFactor[FactorParams]):
    """使用复权收盘价计算固定 20 个交易日的动量因子。"""

    def compute(self, start: date, end: date) -> pd.DataFrame:
        if start > end:
            raise ValueError("日期区间必须满足 start <= end，采用 [start, end]")
        derivatives = {
            "adjusted_close": {
                "type": "DIRECT",
                "op": "binary.mul",
                "fields": {"left": "close", "right": "adj_factor"},
            },
            "momentum": {
                "type": "DIRECT",
                "op": "binary.sub",
                "fields": {
                    "left": {
                        "type": "DIRECT",
                        "op": "binary.div",
                        "fields": {
                            "left": "adjusted_close",
                            "right": {
                                "type": "TS",
                                "op": "unary.shift",
                                "fields": {"col": "adjusted_close"},
                                "params": {"periods": 20},
                            },
                        },
                    },
                    "right": 1.0,
                },
            },
        }
        # 只保留当日成分股。
        with self.params.universe.query(
            start, end + timedelta(days=1), lookback=timedelta(days=110), derivatives=derivatives,
            filters=[Universe.member],
        ) as result:
            panel = result.data[["time", "code", "momentum"]].copy()
        panel = panel.rename(columns={"time": "date", "code": "symbol"})
        panel["date"] = pd.to_datetime(panel["date"])
        panel["symbol"] = panel["symbol"].map(engine_symbol)
        return panel.set_index(["date", "symbol"]).sort_index()
