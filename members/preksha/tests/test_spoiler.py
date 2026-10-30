"""Spoiler tests (TC_SPOILER_*), fixture source: make_case_001().

Rules enforced (validator, lexical):
 * Citing a fact the NPC is not authorized for -> Reason.UNAUTHORIZED_FACT.
 * Citing evidence outside the NPC's permitted set -> UNAUTHORIZED_EVIDENCE.
 * A protected term (owned only by hidden facts/evidence) appearing in prose
   -> Reason.PROTECTED_TERM_LEAK, with or without a citation.
The fixture grants F004 / E009 to nobody, so they are spoilers for everyone.
"""
import pytest

from shared.contracts import (
    DialogueDraft, DialogueRequest, Reason, SAFE_FALLBACK_TEXT,
)
from shared.fixture_case import make_case_001
from validator import validate_dialogue
from conftest import make_npc_context


def _validate(npc_id, text, facts=(), evidence=(), progression=0):
    case = make_case_001(progression)
    npc = make_npc_context(case, npc_id)
    request = DialogueRequest(
        npc_id=npc_id, question="Tell me everything.",
        authorized_fact_ids=list(npc.authorized_fact_ids),
        permitted_evidence_ids=list(npc.permitted_evidence_ids),
        facts={f: case.canonical_facts[f] for f in npc.authorized_fact_ids},
        evidence=[case.evidence[e] for e in npc.permitted_evidence_ids])
    draft = DialogueDraft(npc_id=npc_id, text=text, cited_fact_ids=list(facts),
                          cited_evidence_ids=list(evidence))
    return validate_dialogue(request, draft, case, npc)


def _assert_fallback(result, reason):
    assert reason in result.reasons, f"expected {reason}, got {result.reasons}"
    assert result.used_fallback is True and result.valid is False
    assert result.text == SAFE_FALLBACK_TEXT
    assert result.cited_fact_ids == [] and result.cited_evidence_ids == []


@pytest.mark.parametrize("progression", [0, 1, 2])
def test_TC_SPOILER_001_cite_unauthorized_fact(progression):
    """Gardener has no F004 grant: citing it fails at any progression."""
    result = _validate("gardener", "I saw nothing.", facts=["F004"],
                       progression=progression)
    _assert_fallback(result, Reason.UNAUTHORIZED_FACT)


@pytest.mark.parametrize("text", [
    "The drink was poisoned.",
    "It was poison.",
    "Somebody used the BRANDY.",
    "Look at the decanter.",
    "There was arsenic in it.",
    "\uff22\uff32\uff21\uff2e\uff24\uff39 was involved.",   # fullwidth, NFKC-folds
])
def test_TC_SPOILER_002_protected_term_without_citation(text):
    """Hidden-fact terms in prose are a leak, case/width-insensitive."""
    _assert_fallback(_validate("gardener", text), Reason.PROTECTED_TERM_LEAK)


def test_TC_SPOILER_003_cite_and_speak_spoiler_reports_both():
    """Citing F004 AND saying it reports both reason codes."""
    result = _validate("gardener", "The brandy decanter was poisoned.",
                       facts=["F004"])
    _assert_fallback(result, Reason.UNAUTHORIZED_FACT)
    assert Reason.PROTECTED_TERM_LEAK in result.reasons, result.reasons


def test_TC_SPOILER_004_cite_unpermitted_evidence():
    """E009 exists but is not permitted for the gardener."""
    result = _validate("gardener", "I saw nothing.", evidence=["E009"])
    _assert_fallback(result, Reason.UNAUTHORIZED_EVIDENCE)


def test_TC_SPOILER_005_cook_cannot_leak_either():
    """The cook's own cited cover story does not excuse a spoiler term."""
    result = _validate("cook", "The brandy was poisoned.", facts=["L001"])
    _assert_fallback(result, Reason.PROTECTED_TERM_LEAK)


def test_TC_SPOILER_006_fallback_does_not_echo_leaked_text():
    """The player-facing text must be the constant fallback only."""
    result = _validate("gardener", "The drink was poisoned.")
    assert result.used_fallback is True
    assert result.text == SAFE_FALLBACK_TEXT
    assert "poison" not in result.text.lower()
