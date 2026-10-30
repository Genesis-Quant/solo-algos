from scheme.base import FactorAnalysisParams as BaseFactorAnalysisParams
from scheme.base import FactorParams as BaseFactorParams

__all__ = ["FactorAnalysisParams", "FactorParams"]


class FactorParams(BaseFactorParams):
    """当前因子的运行参数；近 5 周波动率截面排名无需额外算法字段。"""


class FactorAnalysisParams(FactorParams, BaseFactorAnalysisParams):
    """当前因子的运行参数、分析设置与研究入口；配置沿用基类。"""
