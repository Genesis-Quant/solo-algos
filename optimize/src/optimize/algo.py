from typing import Any

from scheme import OptimizeAlgo as BaseOptimizeAlgo
from scheme import ResearchContext, Signal
from .params import OptimizeParams

__all__ = ["OptimizeAlgo"]


class OptimizeAlgo[C: ResearchContext[Any]](BaseOptimizeAlgo[OptimizeParams, C]):
    """示例：按信号方向等权分配，保留现金。"""

    def on_signal(self, signals: Signal[Any]) -> None:
        import math

        if any(
            not isinstance(v, (int, float)) or not math.isfinite(v)
            for v in signals.values()
        ):
            raise ValueError("等权示例要求信号为有限数值")
        selected = {asset: value for asset, value in signals.items() if value != 0}
        weight = self.params.gross_exposure / len(selected) if selected else 0
        self.ctx.target = {
            asset: weight if value > 0 else -weight for asset, value in selected.items()
        }
