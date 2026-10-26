"""Case-engine load tests (TC_CASEENG_*), source: case_engine.load_case().

Rule enforced: load_case("CASE_001") returns a contract CaseState using
Richa's uppercase convention. Her case defines NPC_ROHAN / NPC_WITNESS /
NPC_FORENSIC and evidence E001 / E002.

This file NEVER touches shared.fixture_case.make_case_001(): the fixture
("case_001", gardener, cook, E001/E003/E009) is a different data source.
Negative / drift cases live in test_bug_richa_fixture_drift.py.
"""
import pytest

from shared.contracts import CaseState, EvidenceItem, NPCGrant
from case_engine import load_case


@pytest.fixture
def case():
    """Fresh CASE_001 from the real case engine."""
    return load_case("CASE_001")


def test_TC_CASEENG_001_returns_case_state(case):
    """load_case('CASE_001') returns the contract CaseState dataclass."""
    assert isinstance(case, CaseState), f"got {type(case)}"


def test_TC_CASEENG_002_case_id_is_uppercase(case):
    """Richa's convention: case_id is exactly 'CASE_001'."""
    assert case.case_id == "CASE_001", f"case_id={case.case_id!r}"


def test_TC_CASEENG_003_rohan_has_a_grant(case):
    """'NPC_ROHAN' is a key of npc_grants and maps to an NPCGrant."""
    assert "NPC_ROHAN" in case.npc_grants, sorted(case.npc_grants)
    assert isinstance(case.npc_grants["NPC_ROHAN"], NPCGrant)


@pytest.mark.parametrize("npc_id", ["NPC_ROHAN", "NPC_WITNESS", "NPC_FORENSIC"])
def test_TC_CASEENG_004_all_three_npcs_are_granted(case, npc_id):
    """Each authored NPC id is present in npc_grants (exact, uppercase)."""
    assert npc_id in case.npc_grants, sorted(case.npc_grants)


def test_TC_CASEENG_005_evidence_e001_and_e002_exist(case):
    """Both 'E001' and 'E002' are keys of case.evidence."""
    assert "E001" in case.evidence, sorted(case.evidence)
    assert "E002" in case.evidence, sorted(case.evidence)


@pytest.mark.parametrize("evidence_id", ["E001", "E002"])
def test_TC_CASEENG_006_evidence_items_are_keyed_correctly(case, evidence_id):
    """Each evidence entry is an EvidenceItem whose id equals its key."""
    item = case.evidence[evidence_id]
    assert isinstance(item, EvidenceItem), f"got {type(item)}"
    assert item.evidence_id == evidence_id
