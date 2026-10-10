"""Project forms bind their AnalysisParams without running research or remote queries."""

import importlib
from datetime import date, timedelta
from inspect import get_annotations
from pathlib import Path

import pytest
import scheme.base as scheme_base
from pydantic import SkipValidation, ValidationError
from scheme import StockPool

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
BUSINESS_DEFAULTS = {
    "factor": {"columns": ["momentum"]},
    "model": {"n_select": 10},
    "optimize": {"gross_exposure": 0.98},
    "control": {"lot_size": 100},
    "execution": {},
}
BUSINESS_SCHEMAS = {
    "factor": {"columns": {"type": "array", "minItems": 1, "title": "因子列"}},
    "model": {"n_select": {"type": "integer", "minimum": 1, "title": "选股数量"}},
    "optimize": {"gross_exposure": {
        "type": "number", "exclusiveMinimum": 0, "maximum": 1, "title": "总仓位",
    }},
    "control": {"lot_size": {"type": "integer", "minimum": 1, "title": "每手股数"}},
    "execution": {},
}
BUSINESS_OVERRIDES = {
    "factor": {"columns": ["custom_factor"]},
    "model": {"n_select": 7},
    "optimize": {"gross_exposure": 0.75},
    "control": {"lot_size": 200},
    "execution": {},
}


def _project_types(monkeypatch, kind):
    monkeypatch.syspath_prepend(str(TEMPLATES / kind / "src"))
    module = importlib.import_module(kind)
    analysis = getattr(module, f"{kind.title()}AnalysisParams")
    form = getattr(module, f"{kind.title()}ReportForm")
    base_form = getattr(scheme_base, f"{kind.title()}ReportForm")
    return form, analysis, base_form


@pytest.fixture(params=CASES, ids=[kind for kind, _ in CASES])
def project_form(request, monkeypatch):
    kind, selections = request.param
    form, analysis, base_form = _project_types(monkeypatch, kind)
    return kind, selections, form, analysis, base_form


def test_project_form_is_a_named_bound_thin_subclass(project_form):
    kind, _, form, analysis, base_form = project_form
    assert form.__name__ == f"{kind.title()}ReportForm"
    assert form.__module__.split(".")[0] == kind
    assert form.__bases__ == (base_form[analysis],)
    assert get_annotations(form) == {}
    assert "build" not in form.__dict__
    assert not issubclass(form, analysis)
    assert set(form.model_fields) == set(base_form.model_fields) | set(BUSINESS_DEFAULTS[kind])


def test_project_form_schema_preserves_business_fieldinfo(project_form):
    kind, selections, form, analysis, _ = project_form
    schema = form.model_json_schema()
    properties = schema["properties"]
    assert set(properties) == set(form.model_fields)
    assert schema["additionalProperties"] is False
    assert not {"start", "end"} & set(schema.get("required", []))
    assert properties["start"]["default"] == "2020-01-01"
    assert properties["end"]["default"] == "2027-01-01"
    assert {"start", "end", "pool", "lookback"} <= set(properties)
    assert not {"universe", "config", "symbols"} & set(properties)
    assert all(not field.get("x-hidden") for field in properties.values())
    for name, expected in BUSINESS_SCHEMAS[kind].items():
        generated = form.model_fields[name].asdict()
        generated["metadata"] = [
            item for item in generated["metadata"] if not isinstance(item, SkipValidation)
        ]
        assert generated == analysis.model_fields[name].asdict()
        for key, value in expected.items():
            assert properties[name][key] == value
    for name in selections:
        assert name in schema["required"]
        assert properties[name]["x-algo-kind"] == name


def test_project_form_defaults_build_exact_project_analysis_type(project_form):
    kind, selections, form, analysis, _ = project_form
    pending = form.model_validate(selections)
    built = pending.build()
    assert type(built) is analysis
    assert (pending.start, pending.end) == (date(2020, 1, 1), date(2027, 1, 1))
    assert (built.start, built.end) == (pending.start, pending.end)
    assert built.universe.pool == pending.pool == StockPool.CSI300
    assert built.universe.lookback == pending.lookback == timedelta(0)
    assert not {"pool", "lookback", "cash", "commission", "tax"} & set(built.model_dump())
    for name, value in BUSINESS_DEFAULTS[kind].items():
        assert getattr(pending, name) == getattr(built, name) == value
    if kind == "factor":
        assert built.return_periods == [1, 5, 20]
        assert built.groups == 5
        assert built.n_select == 10
        assert built.weight == "market_value"
        assert built.calendar_symbol == "000300.XSHG"
    else:
        assert built.market_data == "stock_daily"
        assert built.benchmark == "000300.XSHG"
        assert built.batch_days == 1
        assert built.config == {"cash": 1_000_000.0, "commission": 0.0003, "tax": 0.0005}
        selector_defaults = {
            "optimize": "risk_parity", "control": "no_control", "execution": "direct_execution",
        }
        for name in {"model", "optimize", "control", "execution"} - {kind}:
            assert getattr(built, name) == selections.get(name, selector_defaults.get(name))


def test_project_form_overrides_build_through_scheme(project_form):
    kind, selections, form, analysis, _ = project_form
    values = {
        **selections, **BUSINESS_OVERRIDES[kind],
        "start": "2022-01-01", "end": "2023-01-01",
        "pool": StockPool.SSE50, "lookback": "P5D",
    }
    if kind != "factor":
        values.update({
            "market_data": "stock_snapshot", "benchmark": "000905.SH", "batch_days": 3,
            "cash": 350_000, "commission": 0.001, "tax": 0.002,
        })
    built = form.model_validate(values).build()
    assert type(built) is analysis
    assert (built.start, built.end) == (date(2022, 1, 1), date(2023, 1, 1))
    assert built.universe.pool == StockPool.SSE50
    assert built.universe.lookback == timedelta(days=5)
    for name, value in BUSINESS_OVERRIDES[kind].items():
        assert getattr(built, name) == value
    if kind != "factor":
        assert built.market_data == "stock_snapshot"
        assert built.benchmark == "000905.XSHG"
        assert built.batch_days == 3
        assert built.config == {"cash": 350_000, "commission": 0.001, "tax": 0.002}
    assert analysis.model_validate_json(built.model_dump_json()) == built


def test_project_form_forbids_hidden_and_undeclared_inputs(project_form):
    _, selections, form, _, _ = project_form
    for name in ("universe", "config", "symbols", "undeclared"):
        with pytest.raises(ValidationError) as error:
            form.model_validate({**selections, name: {}})
        assert any(
            item["loc"] == (name,) and item["type"] == "extra_forbidden"
            for item in error.value.errors()
        )


@pytest.mark.parametrize("kind,name,value", [
    ("factor", "columns", []),
    ("model", "n_select", 0),
    ("optimize", "gross_exposure", 0),
    ("optimize", "gross_exposure", 1.01),
    ("control", "lot_size", 0),
])
def test_project_business_field_constraints_are_not_lost(monkeypatch, kind, name, value):
    form, _, _ = _project_types(monkeypatch, kind)
    selections = dict(CASES)[kind]
    with pytest.raises(ValidationError) as error:
        form.model_validate({**selections, name: value}).build()
    assert any(item["loc"] == (name,) for item in error.value.errors())


def test_factor_columns_default_factory_is_project_specific_and_isolated(monkeypatch):
    form, analysis, base_form = _project_types(monkeypatch, "factor")
    assert base_form.model_fields["columns"].is_required()
    assert analysis.model_fields["columns"].get_default(call_default_factory=True) == ["momentum"]
    first, second = form(), form()
    assert first.columns is not second.columns
    first.columns.append("custom_factor")
    assert second.columns == ["momentum"]
    assert second.build().columns == ["momentum"]
