"""Template form defaults must match the shared UI contract without running research."""

import importlib
from datetime import date, timedelta
from pathlib import Path

import pytest
from scheme import StockPool
from scheme.base import ReportForm
from scheme.manage.parameters import defaults, inspect_project

TEMPLATES = Path(__file__).resolve().parents[1]
CASES = [
    ("factor", {}),
    ("model", {}),
    ("optimize", {"model": "model_example:Model"}),
    ("control", {"model": "model_example:Model", "optimize": "optimize_example:Optimize"}),
    ("execution", {
        "model": "model_example:Model", "optimize": "optimize_example:Optimize",
        "control": "control_example:Control",
    }),
]


@pytest.mark.parametrize("kind,selections", CASES)
def test_template_form_defaults_round_trip_through_parameter_api(monkeypatch, kind, selections):
    directory = TEMPLATES / kind
    monkeypatch.syspath_prepend(str(directory / "src"))
    monkeypatch.setattr("scheme.execute.strategy.components.algo_options", lambda _: {})
    module = importlib.import_module(kind)
    form = getattr(module, f"{kind.title()}ReportForm")
    assert form.__bases__[0].__pydantic_generic_metadata__["origin"] is ReportForm
    initial = defaults(form)
    definition = inspect_project(directory)
    assert definition["values"]["form"] == initial
    assert not {"start", "end"} & set(definition["schemas"]["form"].get("required", []))
    assert initial["start"] == "2020-01-01"
    assert initial["end"] == "2027-01-01"
    assert initial["pool"] == StockPool.CSI300
    assert initial["lookback"] == "PT0S"
    built = form.model_validate({**initial, **selections}).build()
    assert (built.start, built.end) == (date(2020, 1, 1), date(2027, 1, 1))
    assert built.universe.pool == StockPool.CSI300
    assert built.universe.lookback == timedelta(0)
    if kind == "factor":
        assert initial == {
            "start": "2020-01-01", "end": "2027-01-01", "pool": StockPool.CSI300,
            "lookback": "PT0S", "columns": ["momentum"], "return_periods": [1, 5, 20],
            "groups": 5, "n_select": 10, "weight": "market_value",
            "calendar_symbol": "000300.XSHG",
        }
        assert built.columns == ["momentum"]
        assert built.n_select == 10
        assert built.weight == "market_value"
    else:
        assert initial["market_data"] == "stock_daily"
        assert initial["benchmark"] == "000300.SH"
        assert initial["batch_days"] == 1
        assert built.config == {"cash": 1_000_000.0, "commission": 0.0003, "tax": 0.0005}
    overridden = form.model_validate({
        **initial, **selections, "start": "2022-01-01", "end": "2023-01-01",
        "pool": StockPool.SSE50,
    }).build()
    assert (overridden.start, overridden.end) == (date(2022, 1, 1), date(2023, 1, 1))
    assert overridden.universe.pool == StockPool.SSE50
