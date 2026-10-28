from dataclasses import replace

import pytest

from members.richa.case_engine import CASE_ID, SUSPECT_IDS, _validate_case, load_case
from shared.contracts import ContractError


def test_known_case_loads_with_required_canonical_facts():
    case = load_case(CASE_ID)

    assert case.case_id == CASE_ID
    assert case.canonical_facts["F005"] == "Aman had a financial dispute with the victim."
    assert case.canonical_facts["F006"] == "Neha was present in the office that night."
    assert case.canonical_facts["F007"] == "The victim received a threat message."
    assert case.canonical_facts["F008"] == "A security camera was disabled."
    assert case.canonical_facts["F009"] == "A witness heard shouting before the death."
    assert case.canonical_facts["F010"] == "Poison was purchased earlier that day."
    assert set(case.canonical_facts) == set(case.fact_meta)
    assert case.evidence
    assert set(case.npc_grants) == SUSPECT_IDS


@pytest.mark.parametrize("case_id", ["unknown", "CASE_001", "", None, 1])
def test_unknown_or_invalid_case_id_raises_contract_error(case_id):
    with pytest.raises(ContractError):
        load_case(case_id)


def test_fact_metadata_terms_and_cover_story_are_authored_separately():
    case = load_case(CASE_ID)

    assert all(meta.reveal_at >= 0 for meta in case.fact_meta.values())
    assert all(
        meta.terms
        and all(term == term.lower() for term in meta.terms)
        for meta in case.fact_meta.values()
    )
    assert {"poison", "poisoned"}.issubset(case.fact_meta["F004"].terms)
    assert case.fact_meta["L001"].kind == "cover_story"
    assert "claims" in case.canonical_facts["L001"]
    assert "never poisoned" in case.canonical_facts["L001"]
    assert "Rohan added arsenic" in case.canonical_facts["F011"]
    assert case.fact_meta["L001"].kind != "fact"
    assert {"break", "broke", "broken"}.issubset(case.fact_meta["F002"].terms)
    assert {"hear", "heard", "hearing"}.issubset(case.fact_meta["F009"].terms)


def test_case_has_one_victim_three_suspects_ten_clues_and_timeline():
    case = load_case(CASE_ID)

    assert len(case.npc_grants) == 3
    assert len(case.clues) == 10
    assert len(case.timeline) == 11
    assert {event["victim_id"] for event in case.timeline} == {"lord_ashby"}
    assert [event["time_minute"] for event in case.timeline] == sorted(
        event["time_minute"] for event in case.timeline
    )
    assert any("Rohan adds arsenic" in event["event"] for event in case.timeline)
    assert any("Lord Ashby dies" in event["event"] for event in case.timeline)
    assert any("figure is seen near the greenhouse" in event["event"] for event in case.timeline)
    assert any("Neha argues with Lord Ashby" in event["event"] for event in case.timeline)


def test_fact_evidence_suspect_and_clue_references_are_integral():
    case = load_case(CASE_ID)
    fact_ids = set(case.canonical_facts)
    evidence_ids = set(case.evidence)
    suspect_ids = set(case.npc_grants)
    clue_ids = [clue["clue_id"] for clue in case.clues]
    event_ids = [event["event_id"] for event in case.timeline]

    assert len(fact_ids) == len(case.canonical_facts)
    assert len(evidence_ids) == len(case.evidence)
    assert len(evidence_ids) == 12
    assert len(clue_ids) == len(set(clue_ids))
    assert len(event_ids) == len(set(event_ids))
    assert all(
        item.evidence_id == evidence_id and set(item.fact_ids) <= fact_ids
        for evidence_id, item in case.evidence.items()
    )
    assert all(
        set(grant.fact_ids) <= fact_ids and set(grant.evidence_ids) <= evidence_ids
        for grant in case.npc_grants.values()
    )
    assert set(case.discovered_evidence_ids) <= evidence_ids
    for clue in case.clues:
        assert set(clue["fact_ids"]) <= fact_ids
        assert set(clue["evidence_ids"]) <= evidence_ids
        assert set(clue["suspect_ids"]) <= suspect_ids
    for event in case.timeline:
        assert set(event["suspect_ids"]) <= suspect_ids


def test_invalid_case_fixture_raises_contract_error():
    case = load_case(CASE_ID)
    invalid_case = replace(case, clues=case.clues[:-1])

    with pytest.raises(ContractError, match="exactly ten clues"):
        _validate_case(invalid_case)


def test_duplicate_clue_id_in_fixture_raises_contract_error():
    case = load_case(CASE_ID)
    clues = [dict(clue) for clue in case.clues]
    clues[1]["clue_id"] = clues[0]["clue_id"]

    with pytest.raises(ContractError, match="Clue IDs must be unique"):
        _validate_case(replace(case, clues=clues))


def test_dangling_clue_reference_in_fixture_raises_contract_error():
    case = load_case(CASE_ID)
    clues = [dict(clue) for clue in case.clues]
    clues[0]["evidence_ids"] = ["E999"]

    with pytest.raises(ContractError, match="unknown evidence"):
        _validate_case(replace(case, clues=clues))


def test_repeated_loads_are_equivalent_and_independent():
    first = load_case(CASE_ID)
    second = load_case(CASE_ID)

    assert first == second
    first.fact_meta["F001"].terms.append("mutated")
    first.clues[0]["suspect_ids"].clear()
    assert "mutated" not in second.fact_meta["F001"].terms
    assert second.clues[0]["suspect_ids"]
