from scheme import base

__all__ = ["FactorAnalysisParams", "FactorParams"]


class FactorParams(base.FactorParams):
    """当前因子的运行参数；近 5 周波动率截面排名无需额外算法字段。"""


class FactorAnalysisParams(FactorParams, base.FactorAnalysisParams):
    """当前因子的运行参数、分析设置与研究入口；配置沿用基类。"""
