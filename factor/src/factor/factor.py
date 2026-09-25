from datetime import date, timedelta

import pandas as pd
from scheme import Factor as BaseFactor
from scheme import FactorParams
from scheme.data import query
from scheme.data.dolphindb.symbols import engine_symbol

__all__ = ["Factor"]


class Factor(BaseFactor[FactorParams]):
    """使用复权收盘价计算固定 20 个交易日的动量因子。"""

    def compute(self, start: date, end: date) -> pd.DataFrame:
        request = self.params.universe.query(start, end).model_dump(mode="python")
        request["lookback"] = max(request["lookback"], timedelta(days=110))
        request["derivatives"].update(
            {
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
        )
        with query(request) as result:
            panel = result.data[["time", "code", "momentum"]].copy()
        panel = panel.rename(columns={"time": "date", "code": "symbol"})
        panel["date"] = pd.to_datetime(panel["date"])
        panel["symbol"] = panel["symbol"].map(engine_symbol)
        return panel.set_index(["date", "symbol"]).sort_index()
