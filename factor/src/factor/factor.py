from datetime import date, timedelta
from typing import ClassVar

import pandas as pd
from scheme import DosVar, Universe
from scheme import Factor as BaseFactor

from .params import FactorParams

__all__ = ["Factor"]


class Factor(BaseFactor[FactorParams]):
    """计算固定 20 日动量，再按当日行业和流通市值预处理。"""

    columns: ClassVar[list[str]] = ["momentum"]

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
            start, end + timedelta(days=1), lookback=timedelta(days=110),
            derivatives=derivatives, filters=[Universe.member],
        ) as result:
            return self.preprocess(DosVar(result.data_ref), session=result.session)
