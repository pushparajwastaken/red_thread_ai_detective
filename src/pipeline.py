"""Real end-to-end wiring for Sprint 1 (integration lead).

Connects the actual member implementations through ``members.khushi.integration``:

    Richa  load_case            (members.richa.case_engine)
    Anand  build_npc_context    (members.anand.npc_knowledge)
    Gagan  retrieve_evidence    (members.gagan.retriever)
    Anshul generate_dialogue    (members.anshul.dialogue_generator; offline mock by default)
    Harsh  validate_dialogue / make_fallback (members.harsh.validator)

No stubs are used. Until the lead copies the approved modules into their final
location, this is the single place to change imports. ``interrogate`` keeps the
contract signature from shared/interfaces.md (extra keyword args are optional).
"""
from __future__ import annotations

from typing import Iterable, Optional

from members.khushi.integration import Deps, TurnTrace, interrogate_traced
from shared.contracts import DEFAULT_TIMEOUT_S, CaseState, DialogueResult

__all__ = ["real_deps", "interrogate", "interrogate_with_trace", "load_case"]


def real_deps() -> Deps:
    from members.anand.npc_knowledge import build_npc_context
    from members.anshul.dialogue_generator import generate_dialogue
    from members.gagan.retriever import retrieve_evidence
    from members.harsh.validator import make_fallback, validate_dialogue
    return Deps(build_npc_context, retrieve_evidence, generate_dialogue,
                validate_dialogue, make_fallback)


def load_case(case_id: str) -> CaseState:
    from members.richa.case_engine import load_case as _load
    return _load(case_id)


def interrogate(case: CaseState, npc_id: str, question: str, *,
                presented_evidence_ids: Iterable[str] = (),
                timeout_s: float = DEFAULT_TIMEOUT_S,
                deps: Optional[Deps] = None) -> DialogueResult:
    return interrogate_with_trace(case, npc_id, question,
                                  presented_evidence_ids=presented_evidence_ids,
                                  timeout_s=timeout_s, deps=deps)[0]


def interrogate_with_trace(case: CaseState, npc_id: str, question: str, *,
                           presented_evidence_ids: Iterable[str] = (),
                           timeout_s: float = DEFAULT_TIMEOUT_S,
                           deps: Optional[Deps] = None,
                           request_id: str = "") -> tuple[DialogueResult, TurnTrace]:
    return interrogate_traced(case, npc_id, question,
                              presented_evidence_ids=presented_evidence_ids,
                              timeout_s=timeout_s, deps=deps or real_deps(),
                              request_id=request_id)
