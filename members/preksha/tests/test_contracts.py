"""Contract tests (TC_CONTRACT_*): trusted dataclasses fail AT CONSTRUCTION.

Rule enforced: CaseState and DialogueResult raise ContractError when their
cross-reference / invariant rules in shared/contracts.py are violated.
Uses small hand-built objects, so no fixture or case_engine data is involved.
"""
import pytest

from shared.contracts import (
    CaseState, ContractError, DialogueResult, EvidenceItem, FactMeta, NPCGrant,
)


def _case(**over):
    base = dict(case_id="c1", canonical_facts={"F1": "a", "F2": "b"},
                clues=[], timeline=[])
    base.update(over)
    return CaseState(**base)


def _result(**over):
    base = dict(npc_id="n", text="t", cited_fact_ids=[], valid=True,
                used_fallback=False, latency_ms=0.0)
    base.update(over)
    return DialogueResult(**base)


def test_TC_CONTRACT_001_baseline_case_constructs():
    """A consistent CaseState constructs; reveal_at defaults to 0."""
    case = _case(fact_meta={"F1": FactMeta(reveal_at=3)},
                 evidence={"E1": EvidenceItem("E1", "x", ["F1"])},
                 npc_grants={"n": NPCGrant(["F1"], ["E1"])},
                 discovered_evidence_ids=["E1"])
    assert case.reveal_at("F1") == 3, "meta reveal_at must be honoured"
    assert case.reveal_at("F2") == 0, "fact without meta defaults to 0"


def test_TC_CONTRACT_002_negative_progression():
    """progression must be >= 0."""
    with pytest.raises(ContractError):
        _case(progression=-1)


def test_TC_CONTRACT_003_fact_meta_unknown_fact():
    """fact_meta may only describe facts in canonical_facts."""
    with pytest.raises(ContractError):
        _case(fact_meta={"F404": FactMeta()})


def test_TC_CONTRACT_004_evidence_key_mismatch():
    """evidence dict key must equal the item's evidence_id."""
    with pytest.raises(ContractError):
        _case(evidence={"E1": EvidenceItem("E2", "x")})


def test_TC_CONTRACT_005_evidence_supports_unknown_fact():
    """EvidenceItem.fact_ids must all exist in canonical_facts."""
    with pytest.raises(ContractError):
        _case(evidence={"E1": EvidenceItem("E1", "x", ["F404"])})


def test_TC_CONTRACT_006_grant_unknown_fact():
    """NPCGrant.fact_ids must all exist in canonical_facts."""
    with pytest.raises(ContractError):
        _case(npc_grants={"n": NPCGrant(["F404"], [])})


def test_TC_CONTRACT_007_grant_unknown_evidence():
    """NPCGrant.evidence_ids must all exist in evidence."""
    with pytest.raises(ContractError):
        _case(npc_grants={"n": NPCGrant([], ["E404"])})


def test_TC_CONTRACT_008_discovered_unknown_evidence():
    """discovered_evidence_ids must all exist in evidence."""
    with pytest.raises(ContractError):
        _case(discovered_evidence_ids=["E404"])


def test_TC_CONTRACT_009_negative_latency():
    """DialogueResult.latency_ms must be >= 0."""
    with pytest.raises(ContractError):
        _result(latency_ms=-0.1)


@pytest.mark.parametrize("valid,used_fallback", [(True, True), (False, False)])
def test_TC_CONTRACT_010_valid_xor_used_fallback(valid, used_fallback):
    """valid and used_fallback must differ (exactly one is True)."""
    with pytest.raises(ContractError):
        _result(valid=valid, used_fallback=used_fallback)


@pytest.mark.parametrize("citations", [
    dict(cited_fact_ids=["F1"]),
    dict(cited_evidence_ids=["E1"]),
])
def test_TC_CONTRACT_011_fallback_carries_no_citations(citations):
    """A fallback result must not carry fact or evidence citations."""
    with pytest.raises(ContractError):
        _result(valid=False, used_fallback=True, **citations)


def test_TC_CONTRACT_012_valid_result_may_cite():
    """Positive control: a valid (non-fallback) result may carry citations."""
    res = _result(cited_fact_ids=["F1"], cited_evidence_ids=["E1"])
    assert res.valid is True and res.used_fallback is False
    assert res.cited_fact_ids == ["F1"] and res.cited_evidence_ids == ["E1"]
