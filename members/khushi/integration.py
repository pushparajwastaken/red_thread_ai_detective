"""Module 6 - Integration: ``interrogate()``  (owner: Khushi, with the lead).

Wires the pipeline described in shared/interfaces.md::

    build_npc_context -> filter presented evidence -> retrieve_evidence
    -> DialogueRequest -> generate_dialogue -> validate_dialogue -> DialogueResult

Design rules enforced here
--------------------------
* ``interrogate()`` NEVER raises. Every failure ends in ``make_fallback`` with a
  reason code (SETUP_ERROR / GEN_ERROR / GEN_TIMEOUT / VALIDATOR_ERROR ...).
* The model only ever sees ``npc.authorized_fact_ids`` text and permitted
  evidence. The full CaseState never leaves this module (exclusion by construction).
* Exactly ONE generator call per turn: no retries, no regeneration loops, so
  latency and cost per turn are bounded.
* Wall-clock deadline enforced here (the generator is also asked to honour it).
* Model tokens are never shown before validation: ``generate_dialogue`` returns a
  complete draft, only ``DialogueResult.text`` reaches the player. Therefore the
  player-visible latency is ``metrics.total_ms``; ``ttft_ms`` is model-side only.
* Only this module may advance ``progression`` / ``discovered_evidence_ids``
  (see ``advance_progression`` / ``discover_evidence``), never from model text.
* ``cost_usd`` is passed through from the generator. It is never estimated.
"""
from __future__ import annotations

import re
import unicodedata
import uuid
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as _FutureTimeout
from dataclasses import asdict, dataclass, replace
from time import perf_counter
from typing import Any, Callable, Iterable, Optional

from shared.contracts import (
    DEFAULT_TIMEOUT_S, SAFE_FALLBACK_TEXT, CaseState, DialogueDraft,
    DialogueRequest, DialogueResult, EvidenceItem, NPCContext, Reason, TurnMetrics,
)

MAX_QUESTION_CHARS = 500   # caps prompt size (cost, latency) and injection surface
RETRIEVAL_TOP_K = 3


# ------------------------------------------------------------ input heuristic
_ZERO_WIDTH = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u200e\u200f\u2060\ufeff"), None)
_INJECTION_PATTERNS = tuple(re.compile(p) for p in (
    r"(ignore|disregard|forget|override)\s+(all\s+|any\s+|the\s+|your\s+)?"
    r"(previous|prior|above|earlier|system|safety)?\s*(rules|instructions|prompts?|directions|guidelines)",
    r"\bsystem\s+prompt\b",
    r"(reveal|show|print|repeat|output|display)\s+(me\s+)?(your|the)\s+"
    r"(system\s+|hidden\s+|initial\s+|secret\s+)?(prompt|instructions|rules)",
    r"\byou\s+are\s+now\b",
    r"\b(developer|debug|admin|god|dan)\s+mode\b",
    r"\bjailbreak\b",
    r"as\s+your\s+(police\s+)?(captain|commander|chief|boss|creator|developer|admin)",
    r"\bi\s+(command|order)\s+you\b",
    r"\bpretend\s+(to\s+be|that\s+you|you\s+are)\b",
    r"\bnew\s+instructions?\b",
))


def looks_like_injection(text: Any) -> bool:
    """Cheap heuristic for LOGGING ONLY. It never changes behaviour.

    The validator is the control. Blocking here would add false positives and a
    new oracle; a real classifier (ONNX / NeMo Guardrails) can replace this later.
    """
    try:
        if type(text) is not str:
            return False
        norm = unicodedata.normalize("NFKC", text).translate(_ZERO_WIDTH).casefold()
        norm = re.sub(r"\s+", " ", norm)
        return any(p.search(norm) for p in _INJECTION_PATTERNS)
    except Exception:
        return False


# ----------------------------------------------------------------- wiring
@dataclass
class Deps:
    """The five collaborators. Swap stubs for the real modules without code changes."""
    build_npc_context: Callable[[CaseState, str], NPCContext]
    retrieve_evidence: Callable[..., list]
    generate_dialogue: Callable[[DialogueRequest], DialogueDraft]
    validate_dialogue: Callable[..., DialogueResult]
    make_fallback: Callable[..., DialogueResult]
    flag_input: Callable[[Any], bool] = looks_like_injection


def default_deps() -> Deps:
    """Stubs for modules not delivered yet + Harsh's real validator.

    When the lead copies the real modules into src/, change ONLY the imports here.
    """
    from members.harsh.validator import make_fallback, validate_dialogue
    from members.khushi.stubs import (
        MockGenerator, stub_build_npc_context, stub_retrieve_evidence,
    )
    return Deps(stub_build_npc_context, stub_retrieve_evidence, MockGenerator("ok"),
                validate_dialogue, make_fallback)


# ------------------------------------------------------------------ tracing
@dataclass
class TurnTrace:
    """Per-turn telemetry for logging. Never contains fact IDs or player text."""
    request_id: str = ""
    npc_id: str = ""
    setup_ms: float = 0.0
    retrieval_ms: float = 0.0
    generation_ms: float = 0.0
    validation_ms: float = 0.0
    total_ms: float = 0.0
    ttft_ms: Optional[float] = None
    cost_usd: Optional[float] = None
    timed_out: bool = False
    injection_suspected: bool = False     # heuristic on the player's text, informational only
    evidence_injection_suspected: bool = False   # same heuristic on evidence content (indirect)
    question_truncated: bool = False
    presented_dropped: int = 0
    evidence_sent: int = 0
    used_fallback: bool = True
    reasons: tuple = ()

    def to_dict(self) -> dict:
        d = asdict(self)
        d["reasons"] = ";".join(self.reasons)
        return d


# ---------------------------------------------------------- state advancement
def discover_evidence(case: CaseState, evidence_id: Any) -> bool:
    """Add evidence to the player's inventory by deterministic rule (never from model text)."""
    if type(evidence_id) is not str or evidence_id not in case.evidence:
        return False
    if evidence_id in case.discovered_evidence_ids:
        return False
    if case.evidence[evidence_id].reveal_at > case.progression:
        return False
    case.discovered_evidence_ids.append(evidence_id)
    return True


def advance_progression(case: CaseState, to: Any) -> bool:
    """Move the story forward. Monotonic: it can never go backwards."""
    if type(to) is not int or to <= case.progression:
        return False
    case.progression = to
    return True


# --------------------------------------------------------------- internals
def _bare_fallback(npc_id: Any, reasons: list[str]) -> DialogueResult:
    """Last resort when even make_fallback is unavailable."""
    return DialogueResult(
        npc_id=npc_id if type(npc_id) is str else "", text=SAFE_FALLBACK_TEXT,
        cited_fact_ids=[], valid=False, used_fallback=True, latency_ms=0.0,
        reasons=list(reasons), metrics=None,
    )


def _fallback(deps: Any, npc_id: Any, reasons: list[str],
              metrics: Optional[TurnMetrics] = None) -> DialogueResult:
    try:
        res = deps.make_fallback(npc_id, reasons, metrics)
        if type(res) is DialogueResult:
            return res
    except Exception:
        pass
    return _bare_fallback(npc_id, reasons)


def _call_with_deadline(fn: Callable, arg: Any, budget_s: float):
    """Run fn(arg) on a worker thread. Returns (value, None) or (None, reason)."""
    if budget_s <= 0:
        return None, Reason.GEN_TIMEOUT
    ex = ThreadPoolExecutor(max_workers=1, thread_name_prefix="redthread-gen")
    fut = ex.submit(fn, arg)
    try:
        return fut.result(timeout=budget_s), None
    except _FutureTimeout:
        return None, Reason.GEN_TIMEOUT
    except Exception:
        return None, Reason.GEN_ERROR
    finally:
        # A Python thread cannot be killed: the generator must honour timeout_s itself.
        ex.shutdown(wait=False, cancel_futures=True)


def _clean_timeout(timeout_s: Any) -> float:
    ok = type(timeout_s) in (int, float) and 0 < timeout_s < float("inf")
    return float(timeout_s) if ok else DEFAULT_TIMEOUT_S


def _filter_presented(case: CaseState, npc: NPCContext, presented: Iterable[Any]) -> tuple[list[str], int]:
    """Keep only evidence the player holds, that is revealed, AND the NPC may see."""
    try:
        wanted = [e for e in dict.fromkeys(presented)]
    except Exception:
        return [], 0
    kept = [
        e for e in wanted
        if type(e) is str
        and e in case.discovered_evidence_ids
        and e in case.evidence
        and case.evidence[e].reveal_at <= case.progression
        and e in npc.permitted_evidence_ids
    ]
    return kept, len(wanted) - len(kept)


def _authoritative_evidence(case: CaseState, npc: NPCContext, ids: list[str]) -> list[EvidenceItem]:
    """Resolve evidence by ID from the case (never trust returned content) as fresh copies."""
    out, seen = [], set()
    for eid in ids:
        if eid in seen or eid not in npc.permitted_evidence_ids or eid not in case.evidence:
            continue
        seen.add(eid)
        item = case.evidence[eid]
        out.append(replace(item, fact_ids=list(item.fact_ids), terms=list(item.terms)))
    return out


def _pipeline(case, npc_id, question, presented_evidence_ids, timeout_s, deps, trace, t0):
    # ---- 0. input checks -------------------------------------------------
    if type(case) is not CaseState or type(npc_id) is not str or not npc_id \
            or type(question) is not str:
        return _fallback(deps, npc_id, [Reason.SETUP_ERROR])
    trace.injection_suspected = bool(deps.flag_input(question))
    if len(question) > MAX_QUESTION_CHARS:
        question = question[:MAX_QUESTION_CHARS]
        trace.question_truncated = True
    deadline = t0 + _clean_timeout(timeout_s)

    # ---- 1. NPC context ---------------------------------------------------
    s = perf_counter()
    try:
        npc = deps.build_npc_context(case, npc_id)
        if type(npc) is not NPCContext or npc.npc_id != npc_id:
            return _fallback(deps, npc_id, [Reason.SETUP_ERROR])
        presented, dropped = _filter_presented(case, npc, presented_evidence_ids)
        trace.presented_dropped = dropped
    except Exception:
        return _fallback(deps, npc_id, [Reason.SETUP_ERROR])
    trace.setup_ms = (perf_counter() - s) * 1000

    # ---- 2. evidence retrieval + request ----------------------------------
    s = perf_counter()
    try:
        retrieved = deps.retrieve_evidence(
            question, list(npc.permitted_evidence_ids), case=case, top_k=RETRIEVAL_TOP_K)
        retrieved_ids = [e.evidence_id for e in retrieved]
        evidence = _authoritative_evidence(case, npc, presented + retrieved_ids)
        facts = {fid: case.canonical_facts[fid] for fid in npc.authorized_fact_ids}
        request = DialogueRequest(
            npc_id=npc_id, question=question,
            authorized_fact_ids=list(npc.authorized_fact_ids),
            permitted_evidence_ids=list(npc.permitted_evidence_ids),
            facts=facts, evidence=evidence, presented_evidence_ids=list(presented),
            persona=npc.persona, request_id=trace.request_id,
            timeout_s=max(deadline - perf_counter(), 0.001),
        )
        trace.evidence_sent = len(evidence)
        trace.evidence_injection_suspected = any(deps.flag_input(e.content) for e in evidence)
    except Exception:
        return _fallback(deps, npc_id, [Reason.SETUP_ERROR])
    trace.retrieval_ms = (perf_counter() - s) * 1000

    # ---- 3. generation (single call, hard deadline) ------------------------
    s = perf_counter()
    draft, failure = _call_with_deadline(
        deps.generate_dialogue, request, deadline - perf_counter())
    trace.generation_ms = (perf_counter() - s) * 1000
    if failure is not None:
        trace.timed_out = failure == Reason.GEN_TIMEOUT
        return _fallback(deps, npc_id, [failure])
    gen_metrics = getattr(draft, "metrics", None)
    if type(gen_metrics) is TurnMetrics:
        trace.ttft_ms, trace.cost_usd = gen_metrics.ttft_ms, gen_metrics.cost_usd

    # ---- 4. validation -----------------------------------------------------
    s = perf_counter()
    try:
        result = deps.validate_dialogue(request, draft, case, npc)
        if type(result) is not DialogueResult:
            raise TypeError("validator returned a non-result")
    except Exception:
        trace.validation_ms = (perf_counter() - s) * 1000
        return _fallback(deps, npc_id, [Reason.VALIDATOR_ERROR])
    trace.validation_ms = (perf_counter() - s) * 1000
    return result


def _finalize(result: DialogueResult, trace: TurnTrace, t0: float) -> DialogueResult:
    """Stamp whole-call wall-clock into metrics.total_ms and latency_ms (equal)."""
    total_ms = (perf_counter() - t0) * 1000
    trace.total_ms = total_ms
    base = result.metrics if type(result.metrics) is TurnMetrics else TurnMetrics(mode="dynamic")
    metrics = replace(
        base, total_ms=total_ms,
        generation_ms=base.generation_ms or trace.generation_ms,
        validation_ms=base.validation_ms or trace.validation_ms,
    )
    trace.used_fallback = result.used_fallback
    trace.reasons = tuple(result.reasons)
    return replace(result, latency_ms=total_ms, metrics=metrics)


# --------------------------------------------------------------- public API
def interrogate_traced(case: CaseState, npc_id: str, question: str, *,
                       presented_evidence_ids: Iterable[str] = (),
                       timeout_s: float = DEFAULT_TIMEOUT_S,
                       deps: Optional[Deps] = None,
                       request_id: str = "") -> tuple[DialogueResult, TurnTrace]:
    """Same as ``interrogate`` but also returns a TurnTrace for logging/benchmarks."""
    t0 = perf_counter()
    trace = TurnTrace(request_id=request_id or uuid.uuid4().hex[:12],
                      npc_id=npc_id if type(npc_id) is str else "")
    d: Any = deps
    try:
        d = deps or default_deps()
        result = _pipeline(case, npc_id, question, presented_evidence_ids,
                           timeout_s, d, trace, t0)
    except Exception:           # nothing may ever escape to the game loop
        result = _fallback(d, npc_id, [Reason.SETUP_ERROR])
    try:
        result = _finalize(result, trace, t0)
    except Exception:
        result = _bare_fallback(npc_id, [Reason.VALIDATOR_ERROR])
        trace.used_fallback, trace.reasons = True, tuple(result.reasons)
    return result, trace


def interrogate(case: CaseState, npc_id: str, question: str, *,
                presented_evidence_ids: Iterable[str] = (),
                timeout_s: float = DEFAULT_TIMEOUT_S,
                deps: Optional[Deps] = None) -> DialogueResult:
    """Contract signature from shared/interfaces.md (extra keyword args are optional)."""
    return interrogate_traced(case, npc_id, question,
                              presented_evidence_ids=presented_evidence_ids,
                              timeout_s=timeout_s, deps=deps)[0]


# ------------------------------------------------------------ summary helper
def _pct(values: list[float], q: float) -> Optional[float]:
    if not values:
        return None
    s = sorted(values)
    return s[min(len(s) - 1, max(0, int(round(q * len(s) + 0.5)) - 1))]


def summarize_traces(traces: list[TurnTrace]) -> dict:
    """n, median/p95 total_ms, fallback rate, and cost (None if ANY turn is unknown)."""
    n = len(traces)
    totals = [t.total_ms for t in traces]
    costs = [t.cost_usd for t in traces]
    unknown = sum(c is None for c in costs)
    return {
        "n": n,
        "total_ms_median": _pct(totals, 0.5), "total_ms_p95": _pct(totals, 0.95),
        "fallback_rate": (sum(t.used_fallback for t in traces) / n) if n else None,
        "timeout_count": sum(t.timed_out for t in traces),
        "injection_flagged": sum(t.injection_suspected for t in traces),
        "cost_usd_total": (sum(costs) if n and unknown == 0 else None),
        "turns_with_unknown_cost": unknown,
    }