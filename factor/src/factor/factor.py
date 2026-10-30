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
    """计算近 5 周周收益波动率，在当日有效股票中做截面分位排名，再按行业和流通市值预处理。"""

    columns: ClassVar[list[str]] = ["volatility"]

    def compute(self, start: date, end: date) -> pd.DataFrame:
        if start > end:
            raise ValueError("日期区间必须满足 start <= end，采用 [start, end]")
        universe = self.params.universe

        # 具体参考：dsl skill
        # derivatives 的键是派生列名，值是计算该列的 DSL 节点；每个命名节点都会成为查询结果列，
        # 其它节点用列名字符串引用它。节点字段：
        # - type：计算类别。DIRECT 逐行计算；TS 按股票沿时间计算；CS 按交易日在股票之间计算。
        # - op：算子名称，如 binary.eq、unary.rolling_std；可用算子和参数以项目 Runtime 为准。
        # - fields：算子的输入。字符串引用基础字段（close、limit_status）、日期列 time 或命名节点，
        #   也可以直接嵌套节点或写常量。
        # - params：窗口长度、位移期数等非列参数；算子没有参数时省略。
        # - on：只有 TS/CS 可用的 BOOL filter。true 行才进入该算子的时间序列或截面，其余行结果为
        #   NULL，不删行。时序 filter 只放进 TS，截面 filter 只放进 CS。
        # 下面四个局部变量是 volatility 的嵌套节点，只被下一步使用，不单独输出。
        # 为了方便注释，所有节点都被拆开了，实际编写时请使用嵌套节点，只使用一个derivatives字典

        # 预设的股票池截面filter，根据传入的股票池构造
        member = MEMBERS[universe.pool]
        # 截面 filter（BOOL）：只要求当日属于 member；当日和下一交易日均非 ST、OHLC 完整，
        # 且下一交易日 limit_status 为 0 平盘、1 上涨或 4 下跌，剔除 2/3 涨停、5/6 跌停及空值。
        # shift(-1) 在完整交易日序列上取下一日，不加 on，不跳过停牌；当日涨跌停不在过滤条件中。
        # 这是含未来信息的研究样本筛选，不能用于当日可交易信号；CS on valid 也会受未来样本域影响。
        valid = {
            "type": "DIRECT",
            "op": "multiary.and",
            "fields": {
                "cols": [
                    universe.member,
                    *(
                        {
                            "type": "DIRECT",
                            "op": "binary.eq",
                            "fields": {
                                "left": "is_st"
                                if periods == 0
                                else {
                                    "type": "TS",
                                    "op": "unary.shift",
                                    "fields": {"col": "is_st"},
                                    "params": {"periods": periods},
                                },
                                "right": 0,
                            },
                        }
                        for periods in (0, -1)
                    ),
                    *(
                        {
                            "type": "DIRECT",
                            "op": "unary.not_null",
                            "fields": {
                                "col": price
                                if periods == 0
                                else {
                                    "type": "TS",
                                    "op": "unary.shift",
                                    "fields": {"col": price},
                                    "params": {"periods": periods},
                                },
                            },
                        }
                        for periods in (0, -1)
                        for price in ("open", "high", "low", "close")
                    ),
                    {
                        "type": "DIRECT",
                        "op": "unary.isin",
                        "fields": {
                            "col": {
                                "type": "TS",
                                "op": "unary.shift",
                                "fields": {"col": "limit_status"},
                                "params": {"periods": -1},
                            },
                        },
                        "params": {"values": [0, 1, 4]},
                    },
                ]
            },
        }
        # 时序 filter（BOOL）：交易日是否为周五（weekday 以周一为 0）。
        # 只在时间序列中选取周采样点，近似每周最后一个交易日；周五休市的节假日周没有采样点。
        # 为什么时序filter没有要求是member？为了保证特征计算结果正确，用原始时序数据计算特征，再在截面过滤
        is_friday = {
            "type": "DIRECT",
            "op": "binary.eq",
            "fields": {
                "left": {"type": "DIRECT", "op": "unary.weekday", "fields": {"col": "time"}},
                "right": 4,
            },
        }

        # DIRECT：后复权收盘价 = 收盘价 × 复权因子。
        adjusted_close = {
            "type": "DIRECT",
            "op": "binary.mul",
            "fields": {"left": "close", "right": "adj_factor"},
        }
        # TS + 时序 filter：只在周五子序列上取相邻两期的对数收益，即周收益；非周五行为 NULL。
        weekly_return = {
            "type": "TS",
            "op": "unary.log_return",
            "fields": {"col": adjusted_close},
            "params": {"periods": 1},
            "on": "is_friday",
        }
        # TS + 时序 filter：window 按周五观测计数，即最近 5 条周收益的样本标准差。
        # 任一周价格缺失（如周五停牌）时窗口不足 5 条，结果为 NULL。
        weekly_volatility = {
            "type": "TS",
            "op": "unary.rolling_std",
            "fields": {"col": weekly_return},
            "params": {"window": 5},
            "on": "is_friday",
        }
        # TS：由于要求每个交易日都有因子，把周五的值沿用到之后的交易日，每天使用最近一个周五的波动率。
        # 2010 年以来任一交易日，距最近交易周五最多 8 个交易日，limit=8 覆盖节假日周；更长的空缺（如长期停牌）保持 NULL。
        daily_volatility = {
            "type": "TS",
            "op": "unary.ffill",
            "fields": {"col": weekly_volatility},
            "params": {"limit": 8},
        }
        # 最终因子（CS + 截面 filter）：近 5 周波动率在当日 valid 股票中的分位排名，取值 (0, 1]，
        # 波动率越高排名越大，并列取平均名次；非 valid 行不参与排名，结果为 NULL。
        volatility = {
            "type": "CS",
            "op": "unary.rank_pct",
            "fields": {"col": daily_volatility},
            "params": {"ascending": True, "ties_method": "average"},
            "on": "valid",
        }

        derivatives = {
            universe.member: member,
            "valid": valid,
            "is_friday": is_friday,
            "volatility": volatility,
        }
        codes = universe.codes(start, end + timedelta(days=1))
        if not codes:
            raise ValueError("所选区间的股票池没有成员")
        with query(
            {
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                # 日历天数，覆盖 6 个交易周五和最多 8 个交易日的沿用，节假日周也足够。
                "lookback": timedelta(days=110),
                # 为下一交易日筛选读取有界未来数据，结果和日历仍截回 [start, end]。
                # 20 个自然日内无下一交易日或下一日缺数据时 valid 为 false，不跳过停牌。
                "lookforward": timedelta(days=20),
                "codes": codes,
                "derivatives": derivatives,
                # 输出只保留 valid 行；filters 在全部派生列计算完成后才删行，不影响 TS 历史序列。
                "filters": ["valid"],
            }
        ) as result:
            # 使用默认的因子预处理，不需要自行实现去极值、标准化、中性化。
            return self.preprocess(DosVar(result.data_ref), session=result.session)
