"""ID tests (TC_IDS_*), fixture source: make_case_001().

Rules enforced (validator):
 * IDs are exact, case-sensitive strings: never stripped, folded or repaired.
 * A cited ID that does not exist in CaseState -> UNKNOWN_FACT_ID or
   UNKNOWN_EVIDENCE_ID.
 * Duplicate (or empty) IDs inside one citation list make the draft
   structurally invalid -> SCHEMA_INVALID, handled without raising.
"""
import pytest

from shared.contracts import (
    DialogueDraft, DialogueRequest, Reason, SAFE_FALLBACK_TEXT,
)
from shared.fixture_case import make_case_001
from validator import validate_dialogue
from conftest import make_npc_context


def _validate(text="I saw nothing.", facts=(), evidence=(), npc_id="gardener"):
    case = make_case_001()
    npc = make_npc_context(case, npc_id)
    request = DialogueRequest(
        npc_id=npc_id, question="What did you see?",
        authorized_fact_ids=list(npc.authorized_fact_ids),
        permitted_evidence_ids=list(npc.permitted_evidence_ids),
        facts={f: case.canonical_facts[f] for f in npc.authorized_fact_ids},
        evidence=[case.evidence[e] for e in npc.permitted_evidence_ids])
    draft = DialogueDraft(npc_id=npc_id, text=text, cited_fact_ids=list(facts),
                          cited_evidence_ids=list(evidence))
    return validate_dialogue(request, draft, case, npc)


def _assert_fallback(result, *reasons):
    """Fallback invariants, plus at least one of the given reason codes."""
    assert any(r in result.reasons for r in reasons), \
        f"expected one of {reasons}, got {result.reasons}"
    assert result.used_fallback is True and result.valid is False
    assert result.text == SAFE_FALLBACK_TEXT
    assert result.cited_fact_ids == [] and result.cited_evidence_ids == []


@pytest.mark.parametrize("bad_id", ["f001", "F001 ", " F001", "F-001"],
                         ids=["lowercase", "trailing_space", "leading_space", "hyphen"])
def test_TC_IDS_001_fact_ids_are_case_and_whitespace_exact(bad_id):
    """'f001' and padded variants are NOT repaired into 'F001'."""
    result = _validate(facts=[bad_id])
    _assert_fallback(result, Reason.UNKNOWN_FACT_ID, Reason.UNAUTHORIZED_FACT)


def test_TC_IDS_002_unknown_fact_id():
    """Citing F999 (absent from CaseState) -> UNKNOWN_FACT_ID."""
    _assert_fallback(_validate(facts=["F999"]), Reason.UNKNOWN_FACT_ID)


@pytest.mark.parametrize("bad_id", ["E999", "e001", "E001 "],
                         ids=["absent", "lowercase", "trailing_space"])
def test_TC_IDS_003_unknown_evidence_id(bad_id):
    """Citing an evidence ID that is absent or mis-cased -> UNKNOWN_EVIDENCE_ID."""
    _assert_fallback(_validate(evidence=[bad_id]), Reason.UNKNOWN_EVIDENCE_ID)


def test_TC_IDS_004_unknown_id_beside_valid_id_still_fails():
    """A real citation does not excuse an unknown one in the same list."""
    result = _validate("I saw a figure by the greenhouse.",
                       facts=["F001", "F999"])
    _assert_fallback(result, Reason.UNKNOWN_FACT_ID)


def test_TC_IDS_005_duplicate_fact_citation_is_schema_invalid():
    """cited_fact_ids=['F001','F001'] -> SCHEMA_INVALID, no exception."""
    result = _validate("I saw a figure by the greenhouse.",
                       facts=["F001", "F001"])
    _assert_fallback(result, Reason.SCHEMA_INVALID)


def test_TC_IDS_006_duplicate_evidence_citation_is_schema_invalid():
    """cited_evidence_ids=['E001','E001'] -> SCHEMA_INVALID, no exception."""
    result = _validate("A glove lay by the door.", evidence=["E001", "E001"])
    _assert_fallback(result, Reason.SCHEMA_INVALID)


@pytest.mark.parametrize("kind", ["facts", "evidence"])
def test_TC_IDS_007_empty_string_id_is_schema_invalid(kind):
    """An empty-string ID is not an identifier -> SCHEMA_INVALID."""
    result = _validate(**{kind: [""]})
    _assert_fallback(result, Reason.SCHEMA_INVALID)


def test_TC_IDS_008_exact_ids_are_accepted():
    """Positive control: exact, authorized IDs validate and are echoed."""
    result = _validate("I saw a figure by the greenhouse.",
                       facts=["F001"], evidence=["E001"])
    assert Reason.OK in result.reasons, result.reasons
    assert result.used_fallback is False and result.valid is True
    assert result.cited_fact_ids == ["F001"]
    assert result.cited_evidence_ids == ["E001"]
