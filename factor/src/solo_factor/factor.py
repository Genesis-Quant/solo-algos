from abc import ABC, abstractmethod
from datetime import date

import pandas as pd

from .params import FactorParams

__all__ = ["Factor"]


class Factor(ABC):
    def __init__(self, params: FactorParams) -> None:
        self.params = params

    @abstractmethod
    def compute(self, start: date, end: date) -> pd.DataFrame:
        """返回 [start, end) 的面板；索引为 date、symbol，列为因子名。"""
        ...
