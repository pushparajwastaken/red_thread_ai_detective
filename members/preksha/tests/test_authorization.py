"""Authorization tests (TC_AUTH_*), fixture source: make_case_001().

Rules enforced:
 * DialogueRequest rejects facts / evidence / presented IDs outside its own
   ID lists (ContractError at construction).
 * validate_dialogue never lets a request or NPCContext enlarge authority
   beyond NPCGrant / discovered inventory (Reason.AUTH_MISMATCH).
"""
import pytest

from shared.contracts import (
    ContractError, DialogueDraft, DialogueRequest, NPCContext, Reason,
    SAFE_FALLBACK_TEXT,
)
from shared.fixture_case import make_case_001
from validator import validate_dialogue
from conftest import make_npc_context


def _request(case, npc, **over):
    kw = dict(
        npc_id=npc.npc_id, question="Where were you?",
        authorized_fact_ids=list(npc.authorized_fact_ids),
        permitted_evidence_ids=list(npc.permitted_evidence_ids),
        facts={f: case.canonical_facts[f] for f in npc.authorized_fact_ids},
        evidence=[case.evidence[e] for e in npc.permitted_evidence_ids],
    )
    kw.update(over)
    return DialogueRequest(**kw)


def _draft(text="I saw a figure by the greenhouse.", facts=("F001",)):
    return DialogueDraft(npc_id="gardener", text=text,
                         cited_fact_ids=list(facts), cited_evidence_ids=[])


def _assert_fallback(result, reason):
    assert reason in result.reasons, f"expected {reason}, got {result.reasons}"
    assert result.used_fallback is True and result.valid is False
    assert result.text == SAFE_FALLBACK_TEXT
    assert result.cited_fact_ids == [] and result.cited_evidence_ids == []


def test_TC_AUTH_001_request_rejects_extra_fact():
    """facts may only carry IDs listed in authorized_fact_ids."""
    case = make_case_001()
    with pytest.raises(ContractError):
        DialogueRequest("gardener", "q", ["F001"], [],
                        facts={"F001": case.canonical_facts["F001"],
                               "F004": case.canonical_facts["F004"]})


def test_TC_AUTH_002_request_rejects_extra_evidence():
    """evidence may only carry IDs listed in permitted_evidence_ids."""
    case = make_case_001()
    with pytest.raises(ContractError):
        DialogueRequest("gardener", "q", ["F001"], ["E001"],
                        evidence=[case.evidence["E009"]])


def test_TC_AUTH_003_request_rejects_unpermitted_presented_id():
    """presented_evidence_ids must be a subset of permitted_evidence_ids."""
    with pytest.raises(ContractError):
        DialogueRequest("gardener", "q", ["F001"], ["E001"],
                        presented_evidence_ids=["E009"])


@pytest.mark.parametrize("npc_id", ["gardener", "cook"])
def test_TC_AUTH_004_consistent_request_constructs(npc_id):
    """Positive control: a request built from the NPC context is accepted."""
    case = make_case_001()
    npc = make_npc_context(case, npc_id)
    assert _request(case, npc).npc_id == npc_id


@pytest.mark.parametrize("over", [
    dict(authorized_fact_ids=["F001", "F002", "F003"], facts={}),   # widened
    dict(authorized_fact_ids=["F001"], facts={}),                   # narrowed
    dict(permitted_evidence_ids=["E001"], evidence=[]),             # narrowed
], ids=["widened_facts", "narrowed_facts", "narrowed_evidence"])
def test_TC_AUTH_005_request_must_match_npc_context(over):
    """Request ID lists must equal the NPCContext lists exactly."""
    case = make_case_001()
    npc = make_npc_context(case, "gardener")
    result = validate_dialogue(_request(case, npc, **over), _draft(), case, npc)
    _assert_fallback(result, Reason.AUTH_MISMATCH)


def test_TC_AUTH_006_npc_context_cannot_exceed_grant():
    """An NPCContext claiming a fact outside the NPCGrant is rejected."""
    case = make_case_001()
    npc = NPCContext(npc_id="gardener", authorized_fact_ids=["F001", "F003"],
                     permitted_evidence_ids=["E001", "E003"])
    result = validate_dialogue(_request(case, npc), _draft(), case, npc)
    _assert_fallback(result, Reason.AUTH_MISMATCH)


def test_TC_AUTH_007_presented_evidence_must_be_discovered():
    """Presenting permitted-but-undiscovered evidence is AUTH_MISMATCH."""
    case = make_case_001()
    case.discovered_evidence_ids = ["E001"]       # E003 not in inventory
    npc = make_npc_context(case, "gardener")
    request = _request(case, npc, presented_evidence_ids=["E003"])
    result = validate_dialogue(request, _draft(), case, npc)
    _assert_fallback(result, Reason.AUTH_MISMATCH)


def test_TC_AUTH_008_authorized_reply_is_accepted():
    """Positive control: authorized + cited + uses own term -> valid."""
    case = make_case_001()
    npc = make_npc_context(case, "gardener")
    result = validate_dialogue(_request(case, npc), _draft(), case, npc)
    assert Reason.OK in result.reasons
    assert result.used_fallback is False and result.valid is True
    assert result.cited_fact_ids == ["F001"]
