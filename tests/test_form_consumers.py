"""Exercise workspace Forms through the real backend script, without research or output.

Run with the existing Scheme venv: backend's venv does not contain Scheme's runtime
and backtest dependencies. Missing dependencies fail these tests; they are skipped only
when the algos repository is checked out without the sibling Solo backend repository.
All project fixtures and subprocess working directories belong to pytest's tmp_path.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace

import pytest

SCHEME = Path(__file__).resolve().parents[1] / "scheme"
WORKSPACE = SCHEME.parents[1]
BACKEND = WORKSPACE / "backend"
INSPECTOR = BACKEND / "core/apps/strategies/parameters.py"
pytestmark = pytest.mark.skipif(
    not INSPECTOR.is_file(), reason="需要 Solo 工作区中的 backend 仓库",
)
KINDS = ("model", "optimize", "control", "execution")
ENTRIES = {kind: f"form_consumers_fixture:{kind.title()}Algo" for kind in KINDS}
COMMON_WIRE = {
    "start_on", "end_on", "stock_pool", "history", "price_feed", "benchmark_code",
    "batch_size", "initial_cash", "broker_fee", "stamp_tax",
}
BUSINESS_WIRE = {"days", "options", "labels", "research_note"}
MODEL_VALUES = {
    "start_on": "2026-06-01", "end_on": "2026-06-03",
    "stock_pool": "上证 50", "history": "P8D", "price_feed": "stock_snapshot",
    "benchmark_code": "000905.SH", "batch_size": 3, "initial_cash": "123000",
    "broker_fee": 0.001, "stamp_tax": 0.002, "days": 17,
    "options": {"input_count": 11}, "labels": ["selected"],
    "research_note": "analysis only",
}
COMMON = {
    "start": "2026-06-01", "end": "2026-06-03", "pool": "上证 50",
    "lookback": "P8D", "market_data": "stock_snapshot", "benchmark": "000905.SH",
    "batch_days": 3, "cash": 123000.0, "commission": 0.001, "tax": 0.002,
}
RUNTIME = {"window": 17, "options": {"count": 11}, "labels": ["selected"]}

# Real generic Scheme Algo/Params/Analysis/Form bases, not fake scheme modules or
# a monkeypatched parameter_type. Forms inherit build() without reimplementing it.
PROJECT_SOURCE = dedent("""\
    from copy import deepcopy
    from datetime import date
    from types import new_class

    from pydantic import AliasChoices, AliasPath, BaseModel, ConfigDict, Field, create_model
    from scheme import StockPool, Universe
    from scheme.base import (
        ControlAlgo, ControlAnalysisParams, ControlParams, ControlReportForm,
        ExecutionAlgo, ExecutionAnalysisParams, ExecutionParams, ExecutionReportForm,
        Factor, FactorAnalysisParams, FactorParams, FactorReportForm,
        ModelAlgo, ModelAnalysisParams, ModelParams, ModelReportForm,
        OptimizeAlgo, OptimizeAnalysisParams, OptimizeParams, OptimizeReportForm,
        ResearchContext,
    )

    class Options(BaseModel):
        model_config = ConfigDict(extra="forbid")
        count: int = Field(
            validation_alias=AliasChoices(AliasPath("legacy", "count"), "input_count", "old_count"),
            serialization_alias="reported_count", gt=0,
        )

    def forbidden(*args, **kwargs):
        raise AssertionError("Consumer tests must not compute or process research")

    cases = (
        ("factor", FactorParams, FactorAnalysisParams, FactorReportForm, Factor),
        ("model", ModelParams, ModelAnalysisParams, ModelReportForm, ModelAlgo),
        ("optimize", OptimizeParams, OptimizeAnalysisParams, OptimizeReportForm, OptimizeAlgo),
        ("control", ControlParams, ControlAnalysisParams, ControlReportForm, ControlAlgo),
        ("execution", ExecutionParams, ExecutionAnalysisParams, ExecutionReportForm, ExecutionAlgo),
    )
    for kind, params_base, analysis_base, form_base, algo_base in cases:
        runtime = create_model(
            kind.title() + "Runtime", __base__=params_base, __module__=__name__,
            __config__=ConfigDict(extra="allow", serialize_by_alias=True),
            window=(int, Field(
                validation_alias=AliasChoices(AliasPath("legacy", "window"), "days", "legacy_days"),
                serialization_alias="reported_days", gt=0, title="Trading window",
                json_schema_extra={"unit": "days"},
            )),
            options=(Options, Field(default_factory=lambda: Options(input_count=7))),
            labels=(list[str], Field(default_factory=lambda: ["base"])),
        )
        fields = {
            "start": (date, Field(default=date(2020, 1, 1),
                                 validation_alias=AliasChoices("start_on", "legacy_start"),
                                 serialization_alias="reported_start")),
            "end": (date, Field(default=date(2027, 1, 1), alias="end_on")),
        }
        if kind == "factor":
            fields["columns"] = (list[str], Field(default_factory=lambda: ["momentum"], min_length=1))
        else:
            fields["research_note"] = (str, "research only")
            for name, alias in (("market_data", "price_feed"), ("benchmark", "benchmark_code"),
                                ("batch_days", "batch_size")):
                spec = deepcopy(analysis_base.model_fields[name])
                spec.validation_alias = alias
                fields[name] = (spec.annotation, spec)
        for name, spec in analysis_base.model_fields.items():
            if (spec.json_schema_extra or {}).get("x-algo-kind"):
                spec = deepcopy(spec)
                spec.validation_alias = "selected_" + name
                fields[name] = (spec.annotation, spec)
        analysis = create_model(
            kind.title() + "Analysis", __base__=(runtime, analysis_base),
            __module__=__name__, **fields,
        )
        automatic = form_base[analysis]
        overrides = {}
        for name, alias in (("pool", "stock_pool"), ("lookback", "history"),
                            ("cash", "initial_cash"), ("commission", "broker_fee"),
                            ("tax", "stamp_tax")):
            if name in automatic.model_fields:
                spec = deepcopy(automatic.model_fields[name])
                spec.validation_alias = alias
                overrides[name] = (spec.annotation, spec)
        form = create_model(
            kind.title() + "ReportForm", __base__=automatic, __module__=__name__, **overrides,
        )
        assert "build" not in form.__dict__
        assert form.analysis_model() is analysis
        bases = (algo_base[runtime],) if kind == "factor" else (
            algo_base[runtime, ResearchContext[float]],
        )
        algo = new_class(
            "Factor" if kind == "factor" else kind.title() + "Algo", bases,
            exec_body=lambda namespace: namespace.update(
                __module__=__name__, compute=forbidden, process=forbidden,
            ),
        )
        globals()[kind.title() + "Runtime"] = runtime
        globals()[kind.title() + "Analysis"] = analysis
        globals()[kind.title() + "ReportForm"] = form
        globals()[algo.__name__] = algo
""")

LEGACY_SOURCE = dedent("""\
    from datetime import date
    from pydantic import Field
    from scheme.base import ReportForm
    from form_consumers_fixture import ModelAlgo, ModelAnalysis

    class ModelReportForm(ReportForm[ModelAnalysis]):
        start: date = Field(alias="start_on")
        end: date = Field(alias="end_on")
        window: int = Field(alias="days", gt=0)
        cash: float = Field(default=250000, alias="initial_cash", gt=0)

        def build(self):
            return ModelAnalysis(
                start_on=self.start, end_on=self.end, days=self.window,
                config={"cash": self.cash}, research_note="legacy root",
            )
""")

# Install guards before importing Scheme. Universe.query() only validates the DSL;
# evaluate(), Analysis.run(), sockets, dotenv reads and filesystem writes are forbidden.
BOOTSTRAP = dedent("""\
    import os
    import runpy
    import sys
    from pathlib import Path

    source = Path(sys.argv.pop(1)).resolve()
    target = sys.argv.pop(1)

    def forbidden(*args, **kwargs):
        raise AssertionError("Consumer inspection must not execute research")

    def guard(event, args):
        if event.startswith("socket.") and event not in {"socket.__new__"}:
            raise AssertionError("Consumer inspection must not access services")
        if event in {"subprocess.Popen", "os.mkdir", "os.remove", "os.rename", "os.rmdir"}:
            raise AssertionError("Consumer inspection must not create persistent output")
        if event == "open":
            path, mode, flags = args
            if isinstance(path, (str, bytes, os.PathLike)):
                if any(part.startswith(".env") for part in Path(os.fsdecode(path)).parts):
                    raise AssertionError("Consumer inspection must not read dotenv files")
            if (isinstance(mode, str) and any(char in mode for char in "wax+")) or (
                isinstance(flags, int) and flags & (
                    os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
                )
            ):
                raise AssertionError("Consumer inspection must not write files")

    sys.addaudithook(guard)
    import scheme
    from scheme.base import (
        ControlAnalysisParams, ExecutionAnalysisParams, FactorAnalysisParams,
        ModelAnalysisParams, OptimizeAnalysisParams, StrategyAnalysisParams,
    )
    from scheme.base.internal import form
    from scheme.execute.strategy import assembly

    for module in (scheme, form, assembly):
        assert Path(module.__file__).resolve().is_relative_to(source), module.__file__
    for model in (ControlAnalysisParams, ExecutionAnalysisParams, FactorAnalysisParams,
                  ModelAnalysisParams, OptimizeAnalysisParams, StrategyAnalysisParams):
        model.run = forbidden
    scheme.Universe.evaluate = forbidden
    if target == "scheme.manage":
        runpy.run_module(target, run_name="__main__")
    else:
        runpy.run_path(target, run_name="__main__")
""")


@pytest.fixture
def consumer(tmp_path):
    (tmp_path / "form_consumers_fixture.py").write_text(PROJECT_SOURCE, encoding="utf-8")
    (tmp_path / "form_consumers_legacy.py").write_text(LEGACY_SOURCE, encoding="utf-8")
    project = tmp_path / "factor_project"
    package = project / "src/form_consumers_factor"
    package.mkdir(parents=True)
    (project / "pyproject.toml").write_text(
        '[project]\nname = "form-consumers-factor"\n', encoding="utf-8",
    )
    (package / "__init__.py").write_text(
        "from form_consumers_fixture import Factor, FactorReportForm\n", encoding="utf-8",
    )
    inherited = ("SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "COMSPEC", "PATHEXT")
    environment = {name: os.environ[name] for name in inherited if name in os.environ}
    environment.update(
        PYTHONPATH=os.pathsep.join(map(str, (SCHEME / "src", BACKEND, tmp_path))),
        PYTHON_DOTENV_DISABLED="1", PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8",
    )

    def execute(kind, *, legacy=False, **payload):
        if kind == "factor":
            target = ["scheme.manage", "parameters", "--project", str(project)]
            if "values" in payload:
                target.append("--validate")
                data = {"form": payload["values"]}
            else:
                data = None
        else:
            module = "form_consumers_legacy" if legacy else "form_consumers_fixture"
            target = [str(INSPECTOR)]
            data = {
                "kind": kind, "entry": f"{module}:{kind.title()}Algo", "entries": ENTRIES,
                **payload,
            }
        return subprocess.run(
            [sys.executable, "-B", "-c", BOOTSTRAP, str(SCHEME / "src"), *target],
            cwd=tmp_path, env=environment, input=json.dumps(data), capture_output=True,
            text=True, encoding="utf-8", timeout=30, check=False,
        )

    def inspect(kind, **payload):
        result = execute(kind, **payload)
        assert result.returncode == 0, result.stderr or result.stdout
        return json.loads(result.stdout)

    return SimpleNamespace(execute=execute, inspect=inspect)


def test_model_publishes_common_and_automatic_business_fields(consumer):
    definition = consumer.inspect("model")
    schema, values = definition["schema"], definition["values"]
    assert set(schema["properties"]) == COMMON_WIRE | BUSINESS_WIRE
    assert schema["required"] == ["days"]
    assert schema["additionalProperties"] is False
    assert schema["properties"]["days"] == {
        "type": "integer", "exclusiveMinimum": 0, "title": "Trading window", "unit": "days",
    }
    assert schema["properties"]["start_on"]["default"] == "2020-01-01"
    assert schema["properties"]["end_on"]["default"] == "2027-01-01"
    options = schema["properties"]["options"]
    if "$ref" in options:
        options = schema["$defs"][options["$ref"].rsplit("/", 1)[-1]]
    assert set(options["properties"]) == {"input_count"}
    assert options["required"] == ["input_count"]
    assert values["options"] == {"input_count": 7}
    assert values["labels"] == ["base"]
    assert values["stock_pool"] == "沪深 300"
    assert values["history"] == "PT0S"
    assert "days" not in values
    submitted = consumer.inspect("model", values={**values, "days": 17})
    assert submitted["params"] == {"window": 17, "options": {"count": 7}, "labels": ["base"]}
    assert submitted["common"]["start"] == "2020-01-01"
    assert submitted["common"]["cash"] == 1_000_000


@pytest.mark.parametrize("kind", KINDS[1:])
def test_downstream_hides_common_and_all_stage_fields(consumer, kind):
    definition = consumer.inspect(kind)
    assert set(definition["schema"]["properties"]) == BUSINESS_WIRE
    assert definition["schema"]["required"] == ["days"]
    assert definition["values"] == {
        "options": {"input_count": 7}, "labels": ["base"], "research_note": "research only",
    }


@pytest.mark.parametrize("kind", KINDS[1:])
@pytest.mark.parametrize("selected", [True, False], ids=["selected", "builtin-fallback"])
def test_validated_common_handoff_selector_injection_and_runtime_projection(consumer, kind, selected):
    model = consumer.inspect("model", values=MODEL_VALUES)
    assert model["common"] == COMMON
    assert model["params"] == RUNTIME
    assert model["backtest"]["benchmark"] == "000905.XSHG"
    assert model["backtest"]["research_note"] == "analysis only"
    assert "reported_days" not in model["backtest"]
    # Neither undeclared common inputs nor an untrusted selector may leak downstream.
    common = {
        **model["common"], "window": 99, "initial_cash": 1,
        "model": "untrusted:Model", "selected_model": "untrusted:Model", "unknown": 99,
    }
    entries = ENTRIES if selected else {name: None for name in KINDS}
    result = consumer.inspect(
        kind, common=common, entries=entries,
        values={"days": 23, "research_note": "downstream only"},
    )
    assert set(result) == {"backtest", "params"}
    assert result["params"] == {"window": 23, "options": {"count": 7}, "labels": ["base"]}
    backtest = result["backtest"]
    assert (backtest["start"], backtest["end"]) == (COMMON["start"], COMMON["end"])
    assert backtest["universe"]["pool"] == COMMON["pool"]
    assert backtest["universe"]["lookback"] == COMMON["lookback"]
    assert backtest["config"] == {"cash": 123000, "commission": 0.001, "tax": 0.002}
    assert backtest["market_data"] == COMMON["market_data"]
    assert backtest["benchmark"] == "000905.XSHG"
    assert backtest["batch_days"] == 3
    assert backtest["research_note"] == "downstream only"
    upstream = {"optimize": ("model",), "control": ("model", "optimize"),
                "execution": ("model", "optimize", "control")}[kind]
    for name in upstream:
        assert backtest[name] == (ENTRIES[name] if selected else f"default:{name}")
    assert not {"unknown", "selected_model", "initial_cash", "reported_days"} & backtest.keys()


@pytest.mark.parametrize("kind", KINDS)
def test_saved_canonical_backtest_restores_aliases_and_resubmits(consumer, kind):
    values = MODEL_VALUES if kind == "model" else {
        "days": 17, "options": {"input_count": 11}, "labels": ["selected"],
        "research_note": "analysis only",
    }
    original = consumer.inspect(kind, values=values, common=COMMON)
    saved = {
        **original["backtest"], "days": 99, "reported_days": 99, "unknown": 99,
        "config": {**original["backtest"]["config"], "unknown": 99},
    }
    definition = consumer.inspect(kind, saved=saved)
    restored = definition["values"]
    assert restored["days"] == 17
    assert restored["options"] == {"input_count": 11}
    assert restored["labels"] == ["selected"]
    assert restored["research_note"] == "analysis only"
    assert set(restored) == (BUSINESS_WIRE | COMMON_WIRE if kind == "model" else BUSINESS_WIRE)
    if kind == "model":
        assert restored["initial_cash"] == 123000
        assert restored["broker_fee"] == 0.001
        assert restored["stamp_tax"] == 0.002
        assert restored["stock_pool"] == "上证 50"
        assert restored["history"] == "P8D"
    result = consumer.inspect(kind, values=restored, common=COMMON)
    assert result["params"] == original["params"] == RUNTIME
    assert result["backtest"] == original["backtest"]


@pytest.mark.parametrize("kind,field", [
    ("model", "window"), ("model", "legacy_days"), ("model", "reported_days"),
    ("model", "universe"), ("model", "config"), ("model", "optimize"),
    ("optimize", "start_on"), ("control", "initial_cash"), ("execution", "selected_model"),
])
def test_real_script_rejects_unpublished_inputs(consumer, kind, field):
    result = consumer.execute(kind, values={"days": 17, field: "untrusted"}, common=COMMON)
    assert result.returncode == 1
    assert not result.stdout
    assert "未声明字段" in result.stderr and field in result.stderr


@pytest.mark.parametrize("kind", (*KINDS, "factor"))
@pytest.mark.parametrize("dates,message", [
    ({"start_on": "not-a-date", "end_on": "2026-06-03"}, "start_on"),
    ({"start_on": "2026-06-01", "end_on": "2026-06-01"}, "start < end"),
    ({"start_on": "2026-06-03", "end_on": "2026-06-01"}, "start < end"),
], ids=["malformed", "equal", "reversed"])
def test_invalid_dates_fail_validation_without_research(consumer, kind, dates, message):
    # Downstream receives dates through the canonical validated-common channel.
    common = {**COMMON, "start": dates["start_on"], "end": dates["end_on"]}
    values = {"days": 17, **dates} if kind in {"model", "factor"} else {"days": 17}
    result = consumer.execute(kind, values=values, common=common)
    assert result.returncode == 1
    assert not result.stdout
    assert message in result.stderr
    assert "Consumer inspection must not" not in result.stderr


def test_factor_generic_form_keeps_real_scheme_cli_contract(consumer):
    definition = consumer.inspect("factor")
    assert definition["protocol"] == 2
    schema = definition["schemas"]["form"]
    assert {"start_on", "end_on", "stock_pool", "history", "days", "options", "labels"} <= set(
        schema["properties"]
    )
    assert not {"universe", "config", "cash", "research_note"} & schema["properties"].keys()
    assert schema["required"] == ["days"]
    values = {
        **definition["values"]["form"], "days": 17, "start_on": "2026-06-01",
        "end_on": "2026-06-03", "history": "P8D", "options": {"input_count": 11},
    }
    result = consumer.inspect("factor", values=values)
    assert set(result) == {"entry", "factor", "analysis"}
    assert result["entry"] == "form_consumers_factor:Factor"
    # Scheme CLI honors the runtime's serialize_by_alias policy; backend's script
    # deliberately returns canonical keys instead. Neither contract changes here.
    assert result["factor"]["reported_days"] == 17
    assert not {"window", "days"} & result["factor"].keys()
    assert result["factor"]["options"] == {"count": 11}
    assert result["factor"]["universe"] == result["analysis"]["universe"]
    assert result["analysis"]["columns"] == ["momentum"]
    assert not {"window", "options", "labels", "reported_days"} & result["analysis"].keys()


def test_legacy_reportform_root_remains_a_real_backend_consumer(consumer):
    definition = consumer.inspect("model", legacy=True, saved={
        "start": "2026-06-01", "end": "2026-06-03", "window": 17,
        "config": {"cash": 123000},
    })
    assert set(definition["schema"]["properties"]) == {"start_on", "end_on", "days", "initial_cash"}
    result = consumer.inspect("model", legacy=True, values=definition["values"])
    assert result["common"] == {"start": "2026-06-01", "end": "2026-06-03", "cash": 123000}
    assert result["params"] == {"window": 17, "options": {"count": 7}, "labels": ["base"]}
    assert result["backtest"]["research_note"] == "legacy root"
    assert result["backtest"]["config"] == {"cash": 123000}
