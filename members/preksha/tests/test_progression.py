"""Progression tests (TC_PROG_*), fixture source: make_case_001().

Rule enforced: an item with reveal_at=N is a spoiler while
case.progression < N. The fixture grants F004/E009 to nobody, so tests that
need an NPC to know them add a grant to a LOCAL case object (no shared file
is edited). Two independent gates apply: grant AND progression.
"""
import pytest

from shared.contracts import (
    DialogueDraft, DialogueRequest, NPCGrant, Reason, SAFE_FALLBACK_TEXT,
)
from shared.fixture_case import make_case_001
from validator import validate_dialogue
from conftest import make_npc_context

F004_TEXT = "The brandy decanter was poisoned."


def _case(progression, extra_facts=(), extra_evidence=()):
    case = make_case_001(progression)
    g = case.npc_grants["gardener"]
    case.npc_grants["gardener"] = NPCGrant(
        list(g.fact_ids) + list(extra_facts),
        list(g.evidence_ids) + list(extra_evidence), g.persona)
    return case


def _run(case, text, facts=(), evidence=()):
    npc = make_npc_context(case, "gardener")
    request = DialogueRequest(
        npc_id="gardener", question="What do you know?",
        authorized_fact_ids=list(npc.authorized_fact_ids),
        permitted_evidence_ids=list(npc.permitted_evidence_ids),
        facts={f: case.canonical_facts[f] for f in npc.authorized_fact_ids},
        evidence=[case.evidence[e] for e in npc.permitted_evidence_ids])
    draft = DialogueDraft(npc_id="gardener", text=text,
                          cited_fact_ids=list(facts),
                          cited_evidence_ids=list(evidence))
    return validate_dialogue(request, draft, case, npc)


def _assert_fallback(result, reason):
    assert reason in result.reasons, f"expected {reason}, got {result.reasons}"
    assert result.used_fallback is True and result.valid is False
    assert result.text == SAFE_FALLBACK_TEXT
    assert result.cited_fact_ids == [] and result.cited_evidence_ids == []


def test_TC_PROG_001_reveal_at_values():
    """F004 reveal_at is 2; unknown ids default to 0."""
    case = make_case_001()
    assert case.reveal_at("F004") == 2
    assert case.reveal_at("F001") == 0
    assert case.reveal_at("NOT_A_FACT") == 0


@pytest.mark.parametrize("progression", [0, 1])
def test_TC_PROG_002_f004_grant_blocked_before_reveal(progression):
    """Granting F004 below progression 2 -> AUTH_FUTURE."""
    case = _case(progression, extra_facts=["F004"])
    _assert_fallback(_run(case, F004_TEXT, facts=["F004"]), Reason.AUTH_FUTURE)


@pytest.mark.parametrize("progression", [2, 3])
def test_TC_PROG_003_f004_allowed_from_reveal(progression):
    """Granted F004 at progression >= 2 may be cited and spoken."""
    case = _case(progression, extra_facts=["F004"])
    result = _run(case, F004_TEXT, facts=["F004"])
    assert Reason.OK in result.reasons, result.reasons
    assert result.used_fallback is False and result.valid is True
    assert result.cited_fact_ids == ["F004"]


@pytest.mark.parametrize("progression,blocked", [(1, True), (2, False)])
def test_TC_PROG_004_e009_boundary(progression, blocked):
    """Granted E009 (reveal_at=2) flips from AUTH_FUTURE to valid at 2."""
    case = _case(progression, extra_evidence=["E009"])
    result = _run(case, "The lab found arsenic.", evidence=["E009"])
    if blocked:
        _assert_fallback(result, Reason.AUTH_FUTURE)
    else:
        assert Reason.OK in result.reasons, result.reasons
        assert result.used_fallback is False and result.cited_evidence_ids == ["E009"]


def test_TC_PROG_005_progression_alone_does_not_grant():
    """At progression 2 an NPC without the grant still cannot cite F004."""
    result = _run(make_case_001(2), "I saw nothing.", facts=["F004"])
    _assert_fallback(result, Reason.UNAUTHORIZED_FACT)
