"""Unsupported-claim tests (TC_UNCITED_*), fixture source: make_case_001().

Rule enforced: a term owned by something the NPC IS allowed to know, but
whose owning fact/evidence is not cited in the draft -> Reason.UNCITED_ASSERTION
(distinct from PROTECTED_TERM_LEAK, which is for terms the NPC may NOT know).
Matching is lexical on normalized text; draft texts below avoid accidental
term hits (e.g. the word "will" belongs to F003's terms).
"""
import pytest

from shared.contracts import (
    DialogueDraft, DialogueRequest, Reason, SAFE_FALLBACK_TEXT,
)
from shared.fixture_case import make_case_001
from validator import validate_dialogue
from conftest import make_npc_context


def _validate(npc_id, text, facts=(), evidence=()):
    case = make_case_001()
    npc = make_npc_context(case, npc_id)
    request = DialogueRequest(
        npc_id=npc_id, question="What happened?",
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


def _assert_valid(result):
    assert Reason.OK in result.reasons, result.reasons
    assert result.used_fallback is False and result.valid is True


def test_TC_UNCITED_001_authorized_term_without_citation():
    """Gardener may know F001 but must cite it to say 'greenhouse'."""
    result = _validate("gardener", "I saw someone by the greenhouse.")
    _assert_fallback(result, Reason.UNCITED_ASSERTION)
    assert Reason.PROTECTED_TERM_LEAK not in result.reasons, result.reasons


def test_TC_UNCITED_002_wrong_authorized_citation():
    """Citing F002 does not support a claim owned by F001."""
    result = _validate("gardener", "A figure stood there.", facts=["F002"])
    _assert_fallback(result, Reason.UNCITED_ASSERTION)


def test_TC_UNCITED_003_term_matching_is_case_insensitive():
    """Normalization casefolds prose before matching terms."""
    result = _validate("gardener", "The GREENHOUSE door was open.")
    _assert_fallback(result, Reason.UNCITED_ASSERTION)


def test_TC_UNCITED_004_evidence_term_needs_evidence_citation():
    """'glove' is owned by E001; saying it uncited is unsupported."""
    result = _validate("gardener", "There was a glove on the ground.")
    _assert_fallback(result, Reason.UNCITED_ASSERTION)


def test_TC_UNCITED_005_cook_cover_story_needs_citation():
    """'kitchen' belongs to cover story L001; cite it or fail."""
    result = _validate("cook", "I stayed in the kitchen.")
    _assert_fallback(result, Reason.UNCITED_ASSERTION)


@pytest.mark.parametrize("npc_id,text,facts,evidence", [
    ("gardener", "I saw a figure by the greenhouse.", ["F001"], []),
    ("gardener", "A glove lay by the door.", [], ["E001"]),
    ("cook", "I stayed in the kitchen.", ["L001"], []),
    ("gardener", "I would rather not say.", [], []),
], ids=["fact_cited", "evidence_cited", "cover_story_cited", "no_terms_no_cites"])
def test_TC_UNCITED_006_supported_or_termless_replies_pass(npc_id, text, facts, evidence):
    """Positive controls: cited terms, or prose with no protected terms."""
    _assert_valid(_validate(npc_id, text, facts, evidence))
