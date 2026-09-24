from abc import abstractmethod
from datetime import date

import pandas as pd
from scheme import Factor as BaseFactor

from .params import FactorParams

__all__ = ["Factor"]


class Factor(BaseFactor[FactorParams]):
    @abstractmethod
    def compute(self, start: date, end: date) -> pd.DataFrame:
        """返回 [start, end) 的面板；索引为 date、symbol，列为因子名。"""
        ...
