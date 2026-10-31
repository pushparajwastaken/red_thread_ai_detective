"""Component initialisation and health checks for the unified Red Thread application.

Every check EXERCISES the real module through its documented contract (it does not merely import
it). A check never substitutes a mock for a real implementation: it uses exactly the ``Deps`` the
application will use for play. A required component that fails makes interrogation unavailable;
an optional component that fails only disables the menu option that needs it.
"""
from __future__ import annotations

import importlib
import json
import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterator, Optional

from members.khushi.integration import Deps
from shared.contracts import (
    SAFE_FALLBACK_TEXT, CaseState, ContractError, DialogueDraft, DialogueRequest,
    DialogueResult, EvidenceItem, NPCContext, Reason, TurnMetrics, UnknownNPCError,
)
from src.pipeline import interrogate_with_trace

ROOT = Path(__file__).resolve().parents[1]

OK = "OK"
FAILED = "FAILED"
UNAVAILABLE = "UNAVAILABLE"
NOT_IMPLEMENTED = "NOT IMPLEMENTED"

PROBE_QUESTION = "What can you tell me?"

# Features the project documents as planned but that have no code in this repository.
NOT_IMPLEMENTED_FEATURES = (
    ("Tri-agent LLM pipeline", "single generator call only (presentation slide 8)"),
    ("Accusation / win check", "no culprit field or accusation evaluator exists"),
    ("Event log and memory layers", "nothing persists between turns except the session log of this app"),
    ("Database / persistence", "no case DB, vector store or save system"),
    ("Game client / FastAPI service", "no Unity/UI/HTTP code in the repository"),
    ("NLI judge and in-character fallback bank", "validator is lexical; fallback is one constant string"),
)


class CheckFailed(Exception):
    """A health check ran and found the component not working."""


# ------------------------------------------------------------------ provider
def provider_name() -> str:
    return os.environ.get("LLM_PROVIDER", "mock").strip().lower() or "mock"


def generation_mode() -> str:
    """Human-readable label of what actually generates dialogue. Never hides the mock."""
    p = provider_name()
    if p == "mock":
        return "OFFLINE DETERMINISTIC MOCK - no language model is running"
    if p == "ollama":
        return f"REAL MODEL via Ollama ({os.environ.get('LLM_MODEL') or 'default model'})"
    return f"UNKNOWN provider {p!r} (generation will fail closed)"


@contextmanager
def forced_mock_provider() -> Iterator[None]:
    """Temporarily force LLM_PROVIDER=mock (the scripted security scenarios require it)."""
    old = os.environ.get("LLM_PROVIDER")
    os.environ["LLM_PROVIDER"] = "mock"
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("LLM_PROVIDER", None)
        else:
            os.environ["LLM_PROVIDER"] = old


# ------------------------------------------------------------- optional loaders
def load_security_module():
    """tests/security_scenarios.py: the shared 50-scenario table (patched in tests)."""
    return importlib.import_module("tests.security_scenarios")


def load_benchmark_modules():
    """(question validator, branching baseline, fixture) used by the benchmark harness."""
    return (importlib.import_module("scripts.validate_benchmark_questions"),
            importlib.import_module("members.ananya.branching_baseline"),
            importlib.import_module("shared.fixture_case"))


# --------------------------------------------------------------------- report
@dataclass
class ComponentStatus:
    name: str
    source: str
    required: bool
    state: str
    detail: str = ""

    def render(self) -> str:
        tag = "required" if self.required else "optional"
        if self.state == OK:
            return f"[OK] {self.name} ({tag}) - {self.detail}"
        return f"[{self.state}] {self.name} ({tag})\n    Reason: {self.detail}"


@dataclass
class BootReport:
    case_id: str
    mode: str
    components: list[ComponentStatus] = field(default_factory=list)

    def get(self, name: str) -> Optional[ComponentStatus]:
        return next((c for c in self.components if c.name == name), None)

    def is_ok(self, name: str) -> bool:
        c = self.get(name)
        return c is not None and c.state == OK

    @property
    def failed_required(self) -> list[ComponentStatus]:
        return [c for c in self.components if c.required and c.state != OK]

    @property
    def ok(self) -> bool:
        return not self.failed_required

    def render(self) -> str:
        lines = [f"Red Thread - component initialisation (case: {self.case_id})",
                 f"Generation mode: {self.mode}", ""]
        lines += [c.render() for c in self.components]
        lines.append("")
        if self.ok:
            lines.append("Required components: all OK.")
        else:
            names = ", ".join(c.name for c in self.failed_required)
            lines.append(f"Required components NOT ready: {names}. Interrogation is disabled.")
        return "\n".join(lines)


@dataclass
class _Ctx:
    case_id: str
    deps: Deps
    case_loader: Callable[[str], CaseState]
    case: Optional[CaseState] = None
    contexts: dict = field(default_factory=dict)      # npc_id -> NPCContext


# --------------------------------------------------------------------- checks
def _metrics() -> TurnMetrics:
    return TurnMetrics(mode="dynamic", model="bootstrap-probe")


def _request_for(case: CaseState, npc: NPCContext, request_id: str = "bootstrap-probe") -> DialogueRequest:
    return DialogueRequest(
        npc_id=npc.npc_id, question=PROBE_QUESTION,
        authorized_fact_ids=list(npc.authorized_fact_ids),
        permitted_evidence_ids=list(npc.permitted_evidence_ids),
        facts={f: case.canonical_facts[f] for f in npc.authorized_fact_ids},
        persona=npc.persona, request_id=request_id)


def _check_contracts(ctx: _Ctx) -> str:
    DialogueResult(npc_id="probe", text=SAFE_FALLBACK_TEXT, cited_fact_ids=[], valid=False,
                   used_fallback=True, latency_ms=0.0)
    try:
        DialogueResult(npc_id="probe", text="x", cited_fact_ids=[], valid=True,
                       used_fallback=True, latency_ms=0.0)
    except ContractError:
        pass
    else:
        raise CheckFailed("DialogueResult accepted valid==used_fallback (invariant not enforced)")
    try:
        DialogueRequest(npc_id="probe", question="q", authorized_fact_ids=[], permitted_evidence_ids=[],
                        facts={"F001": "unauthorized text"})
    except ContractError:
        pass
    else:
        raise CheckFailed("DialogueRequest accepted an unauthorized fact")
    return "shared.contracts invariants enforced (result XOR, request exclusion)"


def _check_case_engine(ctx: _Ctx) -> str:
    case = ctx.case_loader(ctx.case_id)
    if type(case) is not CaseState or not case.canonical_facts or not case.npc_grants:
        raise CheckFailed("load_case did not return a populated CaseState")
    try:
        ctx.case_loader("__no_such_case__")
    except ContractError:
        pass
    else:
        raise CheckFailed("an unknown case id was accepted")
    ctx.case = case
    return (f"{case.case_id}: {len(case.canonical_facts)} facts, {len(case.evidence)} evidence, "
            f"{len(case.npc_grants)} suspects, progression {case.progression}")


def _check_npc_knowledge(ctx: _Ctx) -> str:
    case, deps = ctx.case, ctx.deps
    for npc_id, grant in case.npc_grants.items():
        npc = deps.build_npc_context(case, npc_id)
        if type(npc) is not NPCContext or npc.npc_id != npc_id:
            raise CheckFailed(f"build_npc_context returned a bad context for {npc_id!r}")
        if not set(npc.authorized_fact_ids) <= set(grant.fact_ids):
            raise CheckFailed(f"{npc_id!r}: authorized facts exceed the grant")
        if not set(npc.permitted_evidence_ids) <= set(grant.evidence_ids):
            raise CheckFailed(f"{npc_id!r}: permitted evidence exceeds the grant")
        if any(case.reveal_at(f) > case.progression for f in npc.authorized_fact_ids):
            raise CheckFailed(f"{npc_id!r}: a not-yet-revealed fact was authorized")
        ctx.contexts[npc_id] = npc
    try:
        deps.build_npc_context(case, "__nobody__")
    except UnknownNPCError:
        pass
    else:
        raise CheckFailed("an unknown suspect id was accepted")
    return f"{len(ctx.contexts)} suspect contexts built; grant and reveal_at gating verified"


def _check_retrieval(ctx: _Ctx) -> str:
    case, deps = ctx.case, ctx.deps
    if deps.retrieve_evidence("anything", [], case=case, top_k=3) != []:
        raise CheckFailed("retrieval returned evidence although none was permitted")
    for npc_id, npc in ctx.contexts.items():
        for eid in npc.permitted_evidence_ids:
            item = case.evidence[eid]
            if not item.terms:
                continue
            found = deps.retrieve_evidence(f"Tell me about the {item.terms[0]}",
                                           list(npc.permitted_evidence_ids), case=case, top_k=3)
            if not found or not all(type(e) is EvidenceItem for e in found):
                raise CheckFailed(f"{npc_id!r}: no permitted evidence retrieved for term {item.terms[0]!r}")
            if not {e.evidence_id for e in found} <= set(npc.permitted_evidence_ids):
                raise CheckFailed(f"{npc_id!r}: retrieval returned non-permitted evidence")
            return f"retrieved {[e.evidence_id for e in found]} for {npc_id!r}; permitted-only verified"
    return "no suspect has permitted evidence at this progression; empty-permission case verified"


def _first_npc_with_facts(ctx: _Ctx) -> Optional[NPCContext]:
    return next((n for n in ctx.contexts.values() if n.authorized_fact_ids), None)


def _check_generator(ctx: _Ctx) -> str:
    npc = _first_npc_with_facts(ctx) or next(iter(ctx.contexts.values()))
    draft = ctx.deps.generate_dialogue(_request_for(ctx.case, npc))
    if type(draft) is not DialogueDraft:
        raise CheckFailed("generate_dialogue did not return a DialogueDraft")
    if draft.status != "ok":
        raise CheckFailed(f"generation status {draft.status!r}: {draft.error or 'no detail'}")
    if not draft.text.strip():
        raise CheckFailed("generator returned empty text")
    return f"{generation_mode()}; draft returned for suspect {npc.npc_id!r}"


def _check_validator(ctx: _Ctx) -> str:
    case, deps = ctx.case, ctx.deps
    probe = None
    for npc in ctx.contexts.values():
        if not npc.authorized_fact_ids:
            continue
        fid = sorted(npc.authorized_fact_ids)[0]
        request = _request_for(case, npc)
        good = DialogueDraft(npc_id=npc.npc_id, text=case.canonical_facts[fid], cited_fact_ids=[fid],
                             metrics=_metrics())
        res = deps.validate_dialogue(request, good, case, npc)
        if type(res) is DialogueResult and res.valid and not res.used_fallback:
            probe = (npc, request)
            break
    if probe is None:
        raise CheckFailed("no suspect's authorized statement passed validation")
    npc, request = probe
    unknown = DialogueDraft(npc_id=npc.npc_id, text="I saw something.", cited_fact_ids=["F999"],
                            metrics=_metrics())
    r = deps.validate_dialogue(request, unknown, case, npc)
    if not (r.used_fallback and Reason.UNKNOWN_FACT_ID in r.reasons and r.text == SAFE_FALLBACK_TEXT):
        raise CheckFailed("an unknown fact citation was not rejected")
    other = next((f for f in case.canonical_facts if f not in npc.authorized_fact_ids), None)
    if other is not None:
        leak = DialogueDraft(npc_id=npc.npc_id, text=case.canonical_facts[other], cited_fact_ids=[other],
                             metrics=_metrics())
        r = deps.validate_dialogue(request, leak, case, npc)
        if not (r.used_fallback and Reason.UNAUTHORIZED_FACT in r.reasons):
            raise CheckFailed("a citation of an unauthorized fact was not rejected")
    fb = deps.make_fallback(npc.npc_id, [Reason.GEN_ERROR])
    if fb.text != SAFE_FALLBACK_TEXT or fb.valid or not fb.used_fallback:
        raise CheckFailed("make_fallback returned a non-standard result")
    return "accepts an authorized statement; rejects unknown and unauthorized citations; standard fallback"


def _check_pipeline(ctx: _Ctx) -> str:
    mock = provider_name() == "mock"
    npc_ids = list(ctx.contexts) if mock else list(ctx.contexts)[:1]
    valid, fallbacks = 0, []
    for npc_id in npc_ids:
        res, trace = interrogate_with_trace(ctx.case, npc_id, PROBE_QUESTION, deps=ctx.deps,
                                            request_id="bootstrap-probe")
        if type(res) is not DialogueResult:
            raise CheckFailed(f"interrogate returned {type(res).__name__}")
        if res.metrics is not None and res.latency_ms != res.metrics.total_ms:
            raise CheckFailed("latency_ms != metrics.total_ms")
        if res.valid:
            valid += 1
        else:
            fallbacks.append(f"{npc_id}:{'|'.join(res.reasons)}")
    if mock and valid == 0:
        raise CheckFailed(f"no suspect produced a validated reply ({'; '.join(fallbacks)})")
    note = f"{valid}/{len(npc_ids)} probe turns validated"
    if fallbacks:
        note += f"; safe fallback for {', '.join(fallbacks)}"
    return note


def _check_security(ctx: _Ctx) -> str:
    mod = load_security_module()
    scenario = mod.SCENARIOS[0]
    with forced_mock_provider():
        result, _ = mod.run_scenario(scenario)
    if mod.outcome(result) != mod.expected(scenario):
        raise CheckFailed(f"scenario {scenario.test_id} gave {mod.outcome(result)!r}")
    return f"{len(mod.SCENARIOS)} scenarios available; {scenario.test_id} executed"


def _check_benchmark(ctx: _Ctx) -> str:
    validator, baseline, fixture = load_benchmark_modules()
    path = ROOT / "test_cases" / "benchmark_questions.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    errors = validator.validate(doc)
    if errors:
        raise CheckFailed(f"question set invalid: {errors[0]}")
    script = ROOT / "scripts" / "run_benchmark.py"
    if not script.is_file():
        raise CheckFailed("scripts/run_benchmark.py is missing")
    q = doc["questions"][0]
    res = baseline.answer_branching(fixture.make_case_001(q["progression"]), q["npc_id"], q["question_id"],
                                    presented_evidence_ids=q["presented_evidence_ids"])
    if type(res) is not DialogueResult:
        raise CheckFailed("branching baseline did not return a DialogueResult")
    return f"{len(doc['questions'])} questions valid; branching baseline answered {q['question_id']}"


# ------------------------------------------------------------------ entry point
def run_health_checks(case_id: str, deps: Deps,
                      case_loader: Callable[[str], CaseState]) -> BootReport:
    """Initialise and exercise every component; never raises."""
    ctx = _Ctx(case_id=case_id, deps=deps, case_loader=case_loader)
    report = BootReport(case_id=case_id, mode=generation_mode())

    def run(name: str, source: str, required: bool, fn: Callable[[_Ctx], str],
            needs_case: bool = True, needs: tuple = ()) -> None:
        bad = [n for n in needs if not report.is_ok(n)]
        if needs_case and ctx.case is None:
            state, detail = (FAILED if required else UNAVAILABLE), "skipped: Case Engine did not initialise"
        elif bad:
            state, detail = (FAILED if required else UNAVAILABLE), f"skipped: {', '.join(bad)} not ready"
        else:
            try:
                state, detail = OK, fn(ctx)
            except CheckFailed as exc:
                state, detail = (FAILED if required else UNAVAILABLE), str(exc)
            except Exception as exc:  # noqa: BLE001 - a check must never crash startup
                state, detail = (FAILED if required else UNAVAILABLE), f"{type(exc).__name__}: {exc}"
        report.components.append(ComponentStatus(name, source, required, state, detail))

    run("Shared Contracts", "shared/contracts.py", True, _check_contracts, needs_case=False)
    run("Case Engine", "members/richa/case_engine.py", True, _check_case_engine, needs_case=False)
    run("NPC Knowledge", "members/anand/npc_knowledge.py", True, _check_npc_knowledge)
    run("Evidence Retrieval", "members/gagan/retriever.py", True, _check_retrieval, needs=("NPC Knowledge",))
    run("Dialogue Generator", "members/anshul/dialogue_generator.py", True, _check_generator,
        needs=("NPC Knowledge",))
    run("Security Validator", "members/harsh/validator.py", True, _check_validator, needs=("NPC Knowledge",))
    run("Interrogation Pipeline", "src/pipeline.py + members/khushi/integration.py", True, _check_pipeline,
        needs=("NPC Knowledge", "Evidence Retrieval", "Dialogue Generator", "Security Validator"))
    run("Security Validation Suite", "tests/security_scenarios.py", False, _check_security,
        needs_case=False, needs=("Interrogation Pipeline",))
    run("Benchmark Harness", "scripts/run_benchmark.py + members/ananya/branching_baseline.py", False,
        _check_benchmark, needs_case=False)

    if provider_name() == "ollama":
        gen = report.get("Dialogue Generator")
        report.components.append(ComponentStatus(
            "Real LLM Generation", "members/anshul/dialogue_generator.py (OllamaBackend)", False,
            gen.state if gen.state == OK else UNAVAILABLE, gen.detail))
    else:
        report.components.append(ComponentStatus(
            "Real LLM Generation", "members/anshul/dialogue_generator.py (OllamaBackend)", False, UNAVAILABLE,
            "not active (LLM_PROVIDER=mock). No lead-verified real-model result exists (a member-submitted "
            "benchmark is in members/chhavi/); set LLM_PROVIDER=ollama with a running Ollama server to try it"))
    for name, why in NOT_IMPLEMENTED_FEATURES:
        report.components.append(ComponentStatus(name, "-", False, NOT_IMPLEMENTED, why))
    return report
