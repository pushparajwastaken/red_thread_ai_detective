"""Case-engine load tests (TC_CASEENG_*), source: case_engine.load_case().

Rule enforced: load_case(CASE_ID) returns a contract CaseState. Richa's
engine accepts ONLY its own CASE_ID constant ("case_001", lowercase) and
defines the NPCs aman / neha / rohan and evidence E001..E012.

This file NEVER touches shared.fixture_case.make_case_001(): the fixture
(gardener, cook, E001/E003/E009) is a different data source.
Drift / negative cases live in test_bug_case_engine_vs_fixture.py.
"""
import pytest

from shared.contracts import CaseState, EvidenceItem, NPCGrant
from case_engine import load_case, CASE_ID

EXPECTED_NPCS = ["aman", "neha", "rohan"]
EXPECTED_EVIDENCE = [f"E{n:03d}" for n in range(1, 13)]


@pytest.fixture
def case():
    """Fresh case from the real case engine."""
    return load_case(CASE_ID)


def test_TC_CASEENG_001_returns_case_state(case):
    """load_case(CASE_ID) returns the contract CaseState dataclass."""
    assert isinstance(case, CaseState), f"got {type(case)}"


def test_TC_CASEENG_002_case_id_is_case_001(case):
    """The loaded case_id is exactly 'case_001' and equals CASE_ID."""
    assert case.case_id == "case_001", f"case_id={case.case_id!r}"
    assert case.case_id == CASE_ID


def test_TC_CASEENG_003_rohan_has_a_grant(case):
    """'rohan' is a key of npc_grants and maps to an NPCGrant."""
    assert "rohan" in case.npc_grants, sorted(case.npc_grants)
    assert isinstance(case.npc_grants["rohan"], NPCGrant)


@pytest.mark.parametrize("npc_id", EXPECTED_NPCS)
def test_TC_CASEENG_004_all_npcs_are_granted(case, npc_id):
    """Each authored NPC id is present in npc_grants (exact, lowercase)."""
    assert npc_id in case.npc_grants, sorted(case.npc_grants)


def test_TC_CASEENG_005_evidence_e001_and_e002_exist(case):
    """Both 'E001' and 'E002' are keys of case.evidence."""
    assert "E001" in case.evidence, sorted(case.evidence)
    assert "E002" in case.evidence, sorted(case.evidence)


def test_TC_CASEENG_006_full_evidence_inventory(case):
    """The case defines exactly E001..E012."""
    assert sorted(case.evidence) == EXPECTED_EVIDENCE, sorted(case.evidence)


@pytest.mark.parametrize("evidence_id", ["E001", "E002"])
def test_TC_CASEENG_007_evidence_items_are_keyed_correctly(case, evidence_id):
    """Each evidence entry is an EvidenceItem whose id equals its key."""
    item = case.evidence[evidence_id]
    assert isinstance(item, EvidenceItem), f"got {type(item)}"
    assert item.evidence_id == evidence_id
