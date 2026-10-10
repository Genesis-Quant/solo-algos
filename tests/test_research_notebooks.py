"""Template notebook contracts, exercised without market queries or real research."""

import ast
import json
import sys
from datetime import date
from pathlib import Path
from types import ModuleType, SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import BaseModel, ConfigDict, model_validator

TEMPLATES = Path(__file__).resolve().parents[1]
KINDS = ("factor", "model", "optimize", "control", "execution")


def notebook(kind):
    return json.loads((TEMPLATES / kind / "research.ipynb").read_text(encoding="utf-8"))


def code_cells(kind):
    return [cell for cell in notebook(kind)["cells"] if cell["cell_type"] == "code"]


def method_calls(tree):
    return {
        node.func.attr for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }


@pytest.mark.parametrize("kind", KINDS)
def test_templates_have_valid_unexecuted_workflows(kind):
    cells = code_cells(kind)
    calls = set()
    for cell in cells:
        assert cell["execution_count"] is None
        assert cell["outputs"] == []
        tree = ast.parse("".join(cell["source"]))
        compile(tree, f"{kind}/{cell['id']}", "exec")
        calls.update(method_calls(tree))
    assert {"build", "run", "show"} <= calls
    assert ("save" in calls) == (kind == "factor")
    assert sum("solo-parameters" in c["metadata"].get("tags", []) for c in cells) == 1
    assert notebook(kind)["metadata"]["kernelspec"]["name"] == "python3"


def import_bootstrap(kind):
    tree = ast.parse("".join(code_cells(kind)[0]["source"]))
    current_import = next(i for i, node in enumerate(tree.body)
                          if isinstance(node, ast.ImportFrom) and node.module == kind)
    clear_modules = next(i for i, node in enumerate(tree.body) if isinstance(node, ast.For))
    assert clear_modules < current_import
    # Execute only source setup, then the normal import after backend package renaming.
    tree.body = tree.body[:clear_modules + 1]
    return tree


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("explicit_module", [False, True])
def test_source_bootstrap_replaces_only_current_package(kind, explicit_module, tmp_path, monkeypatch):
    package_name = f"{kind}_current"
    config = '[project]\nname = "fallback-current"\n' if explicit_module else (
        f'[project]\nname = "{package_name.replace("_", "-")}"\n')
    if explicit_module:
        config += f'[tool.uv.build-backend]\nmodule-name = "{package_name}"\n'
    (tmp_path / "pyproject.toml").write_text(config, encoding="utf-8")
    package = tmp_path / "src" / package_name
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        "from .params import rebalance_days\n"
        "def run():\n    raise AssertionError('research must not run on import')\n"
        "def show():\n    raise AssertionError('report must not show on import')\n",
        encoding="utf-8",
    )
    (package / "params.py").write_text("rebalance_days = 7\n", encoding="utf-8")
    stale = ModuleType(package_name)
    stale.rebalance_days = 1
    unrelated = ModuleType(package_name + "_dependency")
    monkeypatch.setitem(sys.modules, package_name, stale)
    monkeypatch.setitem(sys.modules, package_name + ".params", ModuleType(package_name + ".params"))
    monkeypatch.setitem(sys.modules, package_name + "_dependency", unrelated)
    monkeypatch.setitem(sys.modules, package_name + "_dependency.child", unrelated)
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.chdir(tmp_path)
    tree = import_bootstrap(kind)
    first_cell = ast.parse("".join(code_cells(kind)[0]["source"]))
    assert not {"run", "show", "save"} & method_calls(first_cell)
    static_import = ast.parse(f"from {package_name} import rebalance_days")
    tree.body.extend(static_import.body)
    namespace = {}
    exec(compile(tree, kind, "exec"), namespace)
    assert namespace["package_name"] == package_name
    assert namespace["rebalance_days"] == 7
    assert sys.modules[package_name] is not stale
    assert Path(sys.modules[package_name].__file__).parent == package
    assert sys.path[0] == str((tmp_path / "src").resolve())
    assert sys.modules[package_name + "_dependency"] is unrelated
    assert sys.modules[package_name + "_dependency.child"] is unrelated


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("has_project", [False, True])
def test_source_bootstrap_missing_project_or_src_is_actionable(kind, has_project, tmp_path, monkeypatch):
    if has_project:
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "current"\n', encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError, match="pyproject.toml.*src|src.*pyproject.toml"):
        exec(compile(import_bootstrap(kind), kind, "exec"), {})


class Universe(BaseModel):
    pool: str = "preset"
    filters: list[str]

    @model_validator(mode="before")
    @classmethod
    def normalize_preset(cls, value):
        # Re-serializing this preset loses a notebook's custom filters.
        if isinstance(value, dict) and value.get("pool") == "preset":
            return {**value, "filters": ["preset_member"]}
        return value


class Analysis(BaseModel):
    model_config = ConfigDict(extra="allow")
    start: date
    end: date
    universe: Universe

    def run(self, algo):
        return algo(self)


class ModelParams(BaseModel):
    start: date
    end: date
    universe: Universe
    n_select: int = 10


class OptimizeParams(BaseModel):
    n_select: int = 10
    risk_limit: float = 0.5


class ControlParams(BaseModel):
    max_order: int = 100


def analysis():
    universe = Universe.model_construct(pool="preset", filters=["custom_member"])
    return Analysis(start="2026-06-01", end="2026-06-06", universe=universe)


def helpers(kind):
    def project_parameters(model, source, *, overrides=None):
        return model.model_validate(SimpleNamespace(**{**dict(source), **(overrides or {})}),
                                    from_attributes=True)

    namespace = {"project_parameters": project_parameters, "parameter_type": lambda cls: cls.Params}
    cell = next(c for c in code_cells(kind) if c["id"] == "upstream-helpers")
    exec(compile("".join(cell["source"]), kind, "exec"), namespace)
    return namespace


@pytest.mark.parametrize("kind", KINDS[2:])
def test_upstream_selection_is_explicit_and_actionable(kind):
    select = helpers(kind)["selected_upstream"]
    with pytest.raises(ValueError, match="dev"):
        select("model", None, {})
    options = {"first:Algo": "first", "second:Algo": "second"}
    with pytest.raises(ValueError, match="first:Algo.*second:Algo"):
        select("model", None, options)
    with pytest.raises(ValueError, match="显式"):
        select("model", None, {"first:Algo": "first"})
    namespace = helpers(kind)
    namespace["import_module"] = lambda module: SimpleNamespace(Algo=SimpleNamespace(Params=ModelParams))
    assert namespace["selected_upstream"]("model", "second:Algo", options) is ModelParams


@pytest.mark.parametrize("kind", KINDS[2:])
def test_upstream_merge_preserves_universe_and_required_dates(kind):
    base = analysis()
    upstream = [(ModelParams, {"n_select": 7})]
    if kind != "optimize":
        upstream.append((OptimizeParams, {"n_select": 7, "risk_limit": 0.25}))
    if kind == "execution":
        upstream.append((ControlParams, {"max_order": 20}))
    merged = helpers(kind)["merge_upstream"](base, upstream)
    assert merged.universe is base.universe
    assert merged.universe.filters == ["custom_member"]
    assert (merged.start, merged.end) == (base.start, base.end)
    assert merged.n_select == 7
    assert "n_select" not in dict(base)
    seen = []
    report = merged.run(lambda params: seen.append(params) or SimpleNamespace(show=lambda: seen.append("show")))
    report.show()
    assert seen == [merged, "show"]


@pytest.mark.parametrize("kind", KINDS[2:])
def test_upstream_conflicts_and_invalid_overrides_fail(kind):
    merge = helpers(kind)["merge_upstream"]
    with pytest.raises(ValueError, match="同名参数冲突.*n_select"):
        merge(analysis(), [(ModelParams, {"n_select": 7}), (OptimizeParams, {"n_select": 8})])
    with pytest.raises(ValueError, match="同名参数冲突.*n_select"):
        merge(analysis(), [(ModelParams, {"n_select": 7}), (OptimizeParams, {})])
    with pytest.raises(ValueError, match="start"):
        merge(analysis(), [(ModelParams, {"start": date(2025, 1, 1)})])
    with pytest.raises(ValueError, match="typo"):
        merge(analysis(), [(ModelParams, {"typo": 3})])
    class CurrentAnalysis(Analysis):
        n_select: int = 10
    current = CurrentAnalysis.model_validate(dict(analysis()))
    with pytest.raises(ValueError, match="同名参数冲突.*n_select"):
        merge(current, [(ModelParams, {"n_select": 7})])


@pytest.mark.parametrize("kind", KINDS)
def test_notebook_form_dates_build_and_report_cells_with_mocks(kind):
    namespace = helpers(kind) if kind in KINDS[2:] else {}
    namespace["StockPool"] = SimpleNamespace(CSI300="CSI300", SSE50="SSE50")
    if kind in KINDS[2:]:
        count = KINDS.index(kind) - 1
        for upstream_kind, params_type in list(zip(("model", "optimize", "control"),
                                                 (ModelParams, OptimizeParams, ControlParams)))[:count]:
            namespace[f"{upstream_kind}_entry"] = f"{upstream_kind}:Algo"
            namespace[f"{upstream_kind}_options"] = {f"{upstream_kind}:Algo": "installed"}
        namespace["import_module"] = lambda module: SimpleNamespace(Algo=SimpleNamespace(Params={
            "model": ModelParams, "optimize": OptimizeParams, "control": ControlParams,
        }[module]))
    seen = []
    class Form:
        def __init__(self, **values):
            self.values = values
        def build(self):
            seen.append("build")
            return Analysis(start=self.values["start"], end=self.values["end"], universe=analysis().universe)
    title = kind.title()
    namespace[f"{title}ReportForm"] = Form
    namespace[f"{title}AnalysisParams"] = Analysis
    namespace["Factor" if kind == "factor" else f"{title}Algo"] = lambda params: (
        seen.append("run") or SimpleNamespace(show=lambda: seen.append("show")))
    for cell in code_cells(kind):
        tree = ast.parse("".join(cell["source"]))
        if any(isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef)) for n in tree.body):
            continue
        # The researcher fills in each entry; leave all other template statements unchanged.
        if kind in KINDS[2:]:
            tree.body = [n for n in tree.body if not (
                isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
                and n.targets[0].id.endswith("_entry"))]
        if "save" not in method_calls(tree):
            exec(compile(tree, kind, "exec"), namespace)
    assert seen == ["build", "run", "show"]
    expected_start = date(2026, 1, 1) if kind == "factor" else date(2026, 6, 1)
    expected_end = date(2026, 7, 1) if kind == "factor" else date(2026, 6, 6)
    assert (namespace["params"].start, namespace["params"].end) == (expected_start, expected_end)


@pytest.mark.parametrize("kind", KINDS[2:])
def test_merge_with_scheme_projection_and_real_template_analysis(kind, monkeypatch):
    import importlib

    scheme = pytest.importorskip("scheme")
    from scheme.execute.strategy.assembly import project_parameters

    monkeypatch.syspath_prepend(str(TEMPLATES / kind / "src"))
    module = importlib.import_module(kind)
    preset = scheme.Universe(pool=scheme.StockPool.SSE50)
    universe = preset.model_copy(update={
        "codes": ["600000.SH"], "filters": ["custom_member"],
        "derivatives": {"custom_member": preset.derivatives["stock_pool_member"]},
    })
    selections = {upstream: f"{upstream}:Algo" for upstream in KINDS[1:KINDS.index(kind)]}
    template_params = getattr(module, f"{kind.title()}AnalysisParams")(
        start="2026-06-01", end="2026-06-06", universe=universe, **selections,
    )

    class RequiredModelParams(BaseModel):
        start: date
        end: date
        universe: scheme.Universe
        n_select: int = 10

    namespace = helpers(kind)
    namespace["project_parameters"] = project_parameters
    merged = namespace["merge_upstream"](template_params, [(RequiredModelParams, {"n_select": 7})])
    projected = project_parameters(RequiredModelParams, merged)
    assert projected.universe is universe
    assert projected.universe.codes == ["600000.SH"]
    assert projected.universe.filters == ["custom_member"]
    assert (projected.start, projected.end, projected.n_select) == (
        date(2026, 6, 1), date(2026, 6, 6), 7,
    )


def test_factor_export_is_opt_in_and_unique_notebook_local(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    seen = []
    cell = next(c for c in code_cells("factor") if "save" in method_calls(ast.parse("".join(c["source"]))))
    tree = ast.parse("".join(cell["source"]))
    namespace = {
        "Path": Path, "uuid4": uuid4, "display": lambda _: None,
        "pd": SimpleNamespace(DataFrame=lambda value: value),
        "report": SimpleNamespace(save=lambda path: seen.append(path) or [], filenames=[]),
    }
    exec(compile(tree, "export", "exec"), namespace)
    assert seen == []
    tree.body[0].value = ast.Constant(value=True)
    ast.fix_missing_locations(tree)
    for _ in range(2):
        exec(compile(tree, "export", "exec"), namespace)
    assert len(set(seen)) == 2
    assert all(path.parent == tmp_path / "reports" for path in seen)
