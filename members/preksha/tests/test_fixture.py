"""Fixture tests (TC_FIXTURE_*): shared.fixture_case.make_case_001() ONLY.

Rule enforced: the golden fixture is internally consistent (no dangling IDs)
and its authored gating data is exactly what other tests rely on.
NOTE: this file never touches case_engine.load_case("CASE_001"); the two
sources differ (case_id, NPC ids, evidence ids) and must not be mixed.
"""
import pytest

from shared.contracts import CaseState
from shared.fixture_case import make_case_001

REVEAL_AT = {"F001": 0, "F002": 0, "F003": 0, "F004": 2, "L001": 0}


def test_TC_FIXTURE_001_identity_and_inventory():
    """Fixture identity: lowercase case_id and the exact ID inventories."""
    case = make_case_001()
    assert isinstance(case, CaseState)
    assert case.case_id == "case_001"
    assert case.progression == 0
    assert set(case.canonical_facts) == set(REVEAL_AT)
    assert set(case.evidence) == {"E001", "E003", "E009"}
    assert set(case.npc_grants) == {"gardener", "cook"}


@pytest.mark.parametrize("progression", [0, 1, 2, 5])
def test_TC_FIXTURE_002_progression_passthrough(progression):
    """make_case_001(n) sets case.progression == n."""
    assert make_case_001(progression).progression == progression


@pytest.mark.parametrize("fact_id,expected", sorted(REVEAL_AT.items()))
def test_TC_FIXTURE_003_fact_reveal_at(fact_id, expected):
    """Only F004 is a future spoiler (reveal_at == 2)."""
    assert make_case_001().reveal_at(fact_id) == expected


def test_TC_FIXTURE_004_evidence_reveal_and_inventory():
    """E009 is future evidence and is not in the player's inventory."""
    case = make_case_001()
    assert case.evidence["E009"].reveal_at == 2
    assert case.evidence["E001"].reveal_at == 0
    assert case.discovered_evidence_ids == ["E001", "E003"]


def test_TC_FIXTURE_005_cover_story_kind():
    """L001 is the only authored cover story."""
    meta = make_case_001().fact_meta
    assert meta["L001"].kind == "cover_story"
    assert [f for f, m in meta.items() if m.kind == "cover_story"] == ["L001"]


def test_TC_FIXTURE_006_no_dangling_ids():
    """Every cross-reference resolves inside the fixture."""
    case = make_case_001()
    facts, evidence = set(case.canonical_facts), set(case.evidence)
    assert set(case.fact_meta) <= facts, "fact_meta references unknown fact"
    for eid, item in case.evidence.items():
        assert item.evidence_id == eid, f"evidence key {eid} != id"
        assert set(item.fact_ids) <= facts, f"{eid} supports unknown fact"
    for npc, grant in case.npc_grants.items():
        assert set(grant.fact_ids) <= facts, f"{npc} granted unknown fact"
        assert set(grant.evidence_ids) <= evidence, f"{npc} granted unknown evidence"
    assert set(case.discovered_evidence_ids) <= evidence


def test_TC_FIXTURE_007_spoilers_are_never_granted():
    """F004 and E009 (future plot) are granted to no NPC."""
    case = make_case_001()
    granted_facts = {f for g in case.npc_grants.values() for f in g.fact_ids}
    granted_evid = {e for g in case.npc_grants.values() for e in g.evidence_ids}
    assert "F004" not in granted_facts
    assert "E009" not in granted_evid


def test_TC_FIXTURE_008_hostile_evidence_is_inert_data():
    """E003 carries injection text but supports no fact and has no terms."""
    item = make_case_001().evidence["E003"]
    assert item.fact_ids == [] and item.terms == []
    assert "IGNORE ALL PREVIOUS INSTRUCTIONS" in item.content


def test_TC_FIXTURE_009_calls_return_independent_objects():
    """Mutating one fixture instance must not leak into another."""
    first, second = make_case_001(), make_case_001()
    first.canonical_facts["F001"] = "tampered"
    first.discovered_evidence_ids.append("E009")
    assert second.canonical_facts["F001"] != "tampered"
    assert "E009" not in second.discovered_evidence_ids
