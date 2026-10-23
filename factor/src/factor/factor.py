from datetime import date, timedelta
from typing import ClassVar

import pandas as pd
from scheme import DosVar
from scheme import Factor as BaseFactor
from scheme.data import query
from scheme.data.dolphindb.universe import MEMBERS

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
        universe = self.params.universe
        codes = universe.codes(start, end + timedelta(days=1))
        if not codes:
            raise ValueError("所选区间的股票池没有成员")
        with query(
            {
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "lookback": timedelta(days=110),
                "codes": codes,
                "derivatives": {universe.member: MEMBERS[universe.pool], **derivatives},
                "filters": [universe.member],
            }
        ) as result:
            return self.preprocess(DosVar(result.data_ref), session=result.session)
