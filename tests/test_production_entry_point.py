"""There is exactly one production entry point, and it uses the real modules."""
import ast
import inspect
from pathlib import Path

import members.khushi.integration as khushi
import src.pipeline as pipeline
from shared.contracts import CaseState, DialogueResult

ROOT = Path(__file__).resolve().parents[1]


def test_contract_signature():
    sig = inspect.signature(pipeline.interrogate)
    names = list(sig.parameters)
    assert names[:3] == ["case", "npc_id", "question"]
    p = sig.parameters["presented_evidence_ids"]
    assert p.kind is inspect.Parameter.KEYWORD_ONLY and p.default == ()


def test_production_wiring_is_real_and_member_default_is_labelled_stub():
    real = pipeline.real_deps()
    mods = {f: getattr(real, f).__module__ for f in ("build_npc_context", "retrieve_evidence", "generate_dialogue",
                                                      "validate_dialogue", "make_fallback")}
    assert not any("stub" in m for m in mods.values()), mods
    stub_mods = {getattr(khushi.default_deps(), f).__module__ if hasattr(getattr(khushi.default_deps(), f), "__module__")
                 else "" for f in ("build_npc_context", "retrieve_evidence")}
    assert any("stubs" in m for m in stub_mods)          # still stubs ...
    assert khushi.DEFAULT_DEPS_ARE_STUBS is True         # ... and says so


def test_pipeline_interrogate_uses_real_deps_when_none_given(monkeypatch):
    seen = {}

    def spy(*a, **k):
        seen["deps"] = k["deps"]
        return DialogueResult(npc_id="x", text="t", cited_fact_ids=[], valid=False, used_fallback=True,
                              latency_ms=0.0), None
    monkeypatch.setattr(pipeline, "interrogate_traced", spy)
    pipeline.interrogate_with_trace(CaseState.__new__(CaseState), "gardener", "q")
    assert seen["deps"].generate_dialogue.__module__ == "members.anshul.dialogue_generator"


def _imports_and_names(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "members.khushi.integration":
            yield from (a.name for a in node.names)
        elif isinstance(node, ast.Attribute) and node.attr == "default_deps":
            yield "default_deps"
        elif isinstance(node, ast.Name) and node.id == "default_deps":
            yield "default_deps"


def test_no_production_code_depends_on_stub_defaults_or_calls_khushi_interrogate_directly():
    offenders = []
    for folder in ("src", "scripts"):
        for f in (ROOT / folder).rglob("*.py"):
            bad = {n for n in _imports_and_names(f) if n in {"default_deps", "interrogate"}}
            if bad:
                offenders.append((str(f.relative_to(ROOT)), sorted(bad)))
    assert offenders == [], offenders
