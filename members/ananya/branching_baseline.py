"""Deterministic fixed-dialogue baseline for Red Thread.

Ananya Narula — Module 9: Branching Baseline.

The baseline deliberately does not call an LLM. It answers using a fixed question
registry so it can be compared with the dynamic dialogue system on the same case,
NPCs, question IDs, and scoring rubric.

Integration note:
- The shared contract remains authoritative.
- When test_cases/ is populated, answer_branching() loads that shared question
  set first.
- The local fixture question set is only a development fallback so this member
  component remains runnable while the shared test_cases directory is empty.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterable, Any

from shared.contracts import (
    CaseState,
    DialogueResult,
    SAFE_FALLBACK_TEXT,
    TurnMetrics,
)


MODULE_DIR = Path(__file__).resolve().parent
LOCAL_QUESTION_SET = MODULE_DIR / "branching_questions.json"
SHARED_QUESTION_SET = MODULE_DIR.parents[2] / "test_cases" / "branching_questions.json"


def _load_question_set() -> dict[str, dict[str, Any]]:
    """Load the shared question set, falling back to the local fixture.

    The shared question set is intentionally preferred. This allows the lead to
    add the team's real test cases without changing this implementation.
    """
    path = SHARED_QUESTION_SET if SHARED_QUESTION_SET.exists() else LOCAL_QUESTION_SET
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    if not isinstance(payload, dict) or "questions" not in payload:
        raise ValueError(f"Invalid branching question set: {path}")

    questions = payload["questions"]
    if not isinstance(questions, list):
        raise ValueError("branching question set 'questions' must be a list")

    result: dict[str, dict[str, Any]] = {}
    for item in questions:
        if not isinstance(item, dict) or not isinstance(item.get("question_id"), str):
            raise ValueError("Every branching question needs a string question_id")
        qid = item["question_id"]
        if qid in result:
            raise ValueError(f"Duplicate question_id: {qid}")
        result[qid] = item
    return result


def _fallback(npc_id: str, start: float, *, reason: str) -> DialogueResult:
    """Return the contract-safe fallback used for unavailable branches."""
    elapsed = (time.perf_counter() - start) * 1000.0
    metrics = TurnMetrics(
        mode="branching",
        model="fixed-tree",
        generation_ms=0.0,
        validation_ms=0.0,
        total_ms=elapsed,
    )
    return DialogueResult(
        npc_id=npc_id,
        text=SAFE_FALLBACK_TEXT,
        cited_fact_ids=[],
        valid=False,
        used_fallback=True,
        latency_ms=elapsed,
        cited_evidence_ids=[],
        reasons=[reason],
        metrics=metrics,
    )


def _is_fact_available(case: CaseState, fact_id: str, npc_id: str) -> bool:
    grant = case.npc_grants.get(npc_id)
    if grant is None or fact_id not in grant.fact_ids:
        return False
    return case.reveal_at(fact_id) <= case.progression


def _is_evidence_available(case: CaseState, evidence_id: str, npc_id: str) -> bool:
    grant = case.npc_grants.get(npc_id)
    item = case.evidence.get(evidence_id)
    if grant is None or item is None:
        return False
    return (
        evidence_id in grant.evidence_ids
        and evidence_id in case.discovered_evidence_ids
        and item.reveal_at <= case.progression
    )


def _render_answer(case: CaseState, question: dict[str, Any], npc_id: str) -> DialogueResult:
    """Build a trusted result from authored fixed-dialogue data.

    A fixed branch is only allowed to cite facts/evidence that are currently
    authorized for the requested NPC and progression.
    """
    answer = question.get("answer")
    fact_ids = list(question.get("fact_ids", []))
    evidence_ids = list(question.get("evidence_ids", []))

    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("Branch answer must contain non-empty answer text")

    if any(not _is_fact_available(case, fid, npc_id) for fid in fact_ids):
        raise PermissionError("branch cites unavailable fact")

    if any(not _is_evidence_available(case, eid, npc_id) for eid in evidence_ids):
        raise PermissionError("branch cites unavailable evidence")

    # Defense-in-depth: a malformed/incorrectly authored branch must not be
    # allowed to print terms belonging exclusively to facts that this NPC
    # cannot currently know. This makes the fixed baseline obey the same
    # epistemic boundary as the dynamic path.
    answer_lower = answer.lower()
    authorized = set(fact_ids)
    for fid, meta in case.fact_meta.items():
        if fid in authorized or _is_fact_available(case, fid, npc_id):
            continue
        if any(term.lower() in answer_lower for term in meta.terms):
            raise PermissionError("branch text contains unavailable fact term")

    elapsed = 0.0
    metrics = TurnMetrics(
        mode="branching",
        model="fixed-tree",
        generation_ms=0.0,
        validation_ms=0.0,
        total_ms=elapsed,
    )
    return DialogueResult(
        npc_id=npc_id,
        text=answer,
        cited_fact_ids=fact_ids,
        valid=True,
        used_fallback=False,
        latency_ms=elapsed,
        cited_evidence_ids=evidence_ids,
        reasons=["OK"],
        metrics=metrics,
    )


def answer_branching(
    case: CaseState,
    npc_id: str,
    question_id: str,
    *,
    presented_evidence_ids: Iterable[str] = (),
) -> DialogueResult:
    """Answer a question through a deterministic fixed dialogue tree.

    Parameters follow Module 9 of shared/interfaces.md exactly.

    The function never mutates CaseState. In particular, it does not advance
    progression or discover evidence; that remains an Integration concern.
    """
    start = time.perf_counter()

    try:
        if npc_id not in case.npc_grants:
            return _fallback(npc_id, start, reason="NPC_MISMATCH")

        questions = _load_question_set()
        question = questions.get(question_id)
        if question is None:
            return _fallback(npc_id, start, reason="SETUP_ERROR")

        if question.get("npc_id") != npc_id:
            return _fallback(npc_id, start, reason="NPC_MISMATCH")

        presented = list(presented_evidence_ids)

        # Evidence supplied to a branch must be both discovered and authorized.
        # It is data, never an instruction source.
        for eid in presented:
            if eid not in case.evidence:
                return _fallback(npc_id, start, reason="UNKNOWN_EVIDENCE_ID")
            if not _is_evidence_available(case, eid, npc_id):
                return _fallback(npc_id, start, reason="UNAUTHORIZED_EVIDENCE")

        required = set(question.get("required_evidence_ids", []))
        if not required.issubset(set(presented)):
            return _fallback(npc_id, start, reason="UNAUTHORIZED_EVIDENCE")

        return _render_answer(case, question, npc_id)

    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        return _fallback(npc_id, start, reason="SETUP_ERROR")
    except PermissionError:
        return _fallback(npc_id, start, reason="UNAUTHORIZED_FACT")
    except Exception:
        return _fallback(npc_id, start, reason="SETUP_ERROR")
