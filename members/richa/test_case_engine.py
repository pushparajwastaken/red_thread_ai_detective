import copy
from dataclasses import replace

import pytest

import members.richa.case_engine as engine
from members.richa.case_engine import (
    CASE_001_ID,
    CASE_001_SUSPECT_IDS,
    CASE_002_ID,
    CASE_002_SUSPECT_IDS,
    Access,
    _build_case_001,
    _validate_case_001,
    _validate_case_002,
    can_suspect_know_fact,
    can_suspect_use_evidence,
    evidence_access,
    fact_access,
    load_case,
)
from shared.contracts import CaseState, ContractError
from shared.fixture_case import make_case_001


def test_known_case_loads_with_required_canonical_facts():
    case = load_case(CASE_002_ID)

    assert case.case_id == CASE_002_ID
    assert case.canonical_facts["F005"] == "Aman had a financial dispute with the victim."
    assert case.canonical_facts["F006"] == "Neha was present in the office that night."
    assert case.canonical_facts["F007"] == "The victim received a threat message."
    assert case.canonical_facts["F008"] == "A security camera was disabled."
    assert case.canonical_facts["F009"] == "A witness heard shouting before the death."
    assert case.canonical_facts["F010"] == "Poison was purchased earlier that day."
    assert set(case.canonical_facts) == set(case.fact_meta)
    assert case.evidence
    assert set(case.npc_grants) == CASE_002_SUSPECT_IDS


@pytest.mark.parametrize("case_id", ["unknown", "CASE_001", "case_001 ", " case_002", "", None, 1])
def test_unknown_or_invalid_case_id_raises_contract_error(case_id):
    with pytest.raises(ContractError):
        load_case(case_id)


def test_fact_metadata_terms_and_cover_story_are_authored_separately():
    case = load_case(CASE_002_ID)

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
    case = load_case(CASE_002_ID)

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
    case = load_case(CASE_002_ID)
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
    case = load_case(CASE_002_ID)
    invalid_case = replace(case, clues=case.clues[:-1])

    with pytest.raises(ContractError, match="exactly ten clues"):
        _validate_case_002(invalid_case)


def test_duplicate_clue_id_in_fixture_raises_contract_error():
    case = load_case(CASE_002_ID)
    clues = [dict(clue) for clue in case.clues]
    clues[1]["clue_id"] = clues[0]["clue_id"]

    with pytest.raises(ContractError, match="Clue IDs must be unique"):
        _validate_case_002(replace(case, clues=clues))


def test_dangling_clue_reference_in_fixture_raises_contract_error():
    case = load_case(CASE_002_ID)
    clues = [dict(clue) for clue in case.clues]
    clues[0]["evidence_ids"] = ["E999"]

    with pytest.raises(ContractError, match="unknown evidence"):
        _validate_case_002(replace(case, clues=clues))


def test_repeated_loads_are_equivalent_and_independent():
    first = load_case(CASE_002_ID)
    second = load_case(CASE_002_ID)

    assert first == second
    first.fact_meta["F001"].terms.append("mutated")
    first.clues[0]["suspect_ids"].clear()
    assert "mutated" not in second.fact_meta["F001"].terms
    assert second.clues[0]["suspect_ids"]


# ---- canonical case_001 must equal the shared fixture --------------------

def test_case_001_equals_shared_fixture():
    assert load_case(CASE_001_ID) == make_case_001()


def test_case_001_has_canonical_npcs_and_private_internals():
    # Previously asserted npc_grants == {gardener, cook} and clues == [] / timeline == [], i.e. it
    # asserted that the Sprint 1 case requirement was NOT met. case_001 now meets it.
    case = load_case(CASE_001_ID)
    assert set(case.npc_grants) == {"gardener", "cook", "housekeeper"}
    assert len(case.clues) == 10 and len(case.timeline) == 9
    assert case.progression == 0
    assert case.fact_meta["F004"].reveal_at == 2
    assert case.fact_meta["L001"].kind == "cover_story"


def test_case_001_loads_are_independent():
    first, second = load_case(CASE_001_ID), load_case(CASE_001_ID)
    first.canonical_facts["F001"] = "mutated"
    first.npc_grants["cook"].fact_ids.clear()
    assert second == make_case_001()


def test_case_002_is_separate_from_case_001():
    assert load_case(CASE_002_ID).case_id == CASE_002_ID
    assert set(load_case(CASE_002_ID).npc_grants) == CASE_002_SUSPECT_IDS
    assert not set(load_case(CASE_002_ID).npc_grants) & set(load_case(CASE_001_ID).npc_grants)


# ======================================================================================
# Sprint 1 case requirement: one victim, exactly three suspects, ten clues, ordered timeline
# ======================================================================================

def test_case_001_meets_the_sprint1_case_requirement():
    case = load_case(CASE_001_ID)

    assert set(case.npc_grants) == CASE_001_SUSPECT_IDS == {"gardener", "cook", "housekeeper"}
    assert len(case.npc_grants) == 3
    assert len(case.clues) == 10
    assert {event["victim_id"] for event in case.timeline} == {"lord_ashby"}
    times = [event["time_minute"] for event in case.timeline]
    assert times == sorted(times) and len(times) == len(set(times))      # strictly increasing
    assert (len(case.canonical_facts), len(case.evidence), len(case.timeline)) == (11, 11, 9)


def test_case_001_original_entries_are_unchanged():
    """The benchmark set and security scenarios are keyed to these; extending the case must not move them."""
    case = load_case(CASE_001_ID)
    assert case.npc_grants["gardener"].fact_ids == ["F001", "F002"]
    assert case.npc_grants["gardener"].evidence_ids == ["E001", "E003"]
    assert case.npc_grants["cook"].fact_ids == ["F003", "L001"]
    assert case.npc_grants["cook"].evidence_ids == []
    assert case.canonical_facts["F001"] == "I saw a figure near the greenhouse at nine o'clock."
    assert case.canonical_facts["L001"] == "I never left the kitchen all evening."
    assert (case.fact_meta["F004"].reveal_at, case.evidence["E009"].reveal_at) == (2, 2)
    assert case.discovered_evidence_ids == ["E001", "E003"]
    # extension is appended after the original entries
    assert list(case.canonical_facts)[:5] == ["F001", "F002", "F003", "F004", "L001"]
    assert list(case.evidence)[:3] == ["E001", "E003", "E009"]
    assert list(case.npc_grants)[:2] == ["gardener", "cook"]


def test_case_001_references_are_all_valid():
    case = load_case(CASE_001_ID)
    facts, evidence, suspects = set(case.canonical_facts), set(case.evidence), set(case.npc_grants)
    clue_ids = [c["clue_id"] for c in case.clues]
    event_ids = [e["event_id"] for e in case.timeline]
    assert len(clue_ids) == len(set(clue_ids)) == 10 and len(event_ids) == len(set(event_ids))
    for clue in case.clues:
        assert clue["fact_ids"] and clue["evidence_ids"] and clue["suspect_ids"]
        assert set(clue["fact_ids"]) <= facts
        assert set(clue["evidence_ids"]) <= evidence
        assert set(clue["suspect_ids"]) <= suspects
        for fid in clue["fact_ids"]:       # every clued fact is supported by that clue's own evidence
            assert any(fid in case.evidence[e].fact_ids for e in clue["evidence_ids"]), clue["clue_id"]
    for event in case.timeline:
        assert set(event["suspect_ids"]) <= suspects and set(event.get("fact_ids", [])) <= facts
    for grant in case.npc_grants.values():
        assert set(grant.fact_ids) <= facts and set(grant.evidence_ids) <= evidence
    assert {s for c in case.clues for s in c["suspect_ids"]} == suspects      # every suspect is clued
    assert {s for e in case.timeline for s in e["suspect_ids"]} == suspects   # ...and on the timeline


def test_authored_lie_is_kept_separate_from_canonical_truth():
    case = load_case(CASE_001_ID)
    assert [f for f, m in case.fact_meta.items() if m.kind == "cover_story"] == ["L001"]
    referenced = {f for c in case.clues for f in c["fact_ids"]}
    referenced |= {f for e in case.timeline for f in e.get("fact_ids", [])}
    assert "L001" not in referenced
    # the truth that contradicts the lie exists as an ordinary fact, and is not granted to the liar
    assert case.fact_meta["F005"].kind == "fact" and "kitchen" in case.canonical_facts["F005"]
    assert "F005" not in case.npc_grants["cook"].fact_ids


def test_case_001_repeated_loads_are_equal_and_fully_independent():
    first, second = load_case(CASE_001_ID), load_case(CASE_001_ID)
    assert first == second and first is not second
    first.clues[0]["suspect_ids"].clear()
    first.timeline[0]["event"] = "mutated"
    first.timeline.pop()
    first.npc_grants["housekeeper"].fact_ids.clear()
    first.evidence["E007"].terms.append("mutated")
    first.fact_meta["F007"].terms.clear()
    first.discovered_evidence_ids.append("E007")
    assert load_case(CASE_001_ID) == second == make_case_001()


# ---- malformed data fails safely (ContractError, never a stray exception) -------------

def _bad(mutate):
    case = _build_case_001()
    mutate(case)
    return case


def _drop_clue(c): c.clues.pop()
def _extra_clue(c): c.clues.append({**copy.deepcopy(c.clues[0]), "clue_id": "C011"})
def _dup_clue_id(c): c.clues[1]["clue_id"] = c.clues[0]["clue_id"]
def _bad_clue_id(c): c.clues[0]["clue_id"] = "c001"
def _clue_not_dict(c): c.clues[0] = "C001"
def _clue_unknown_fact(c): c.clues[0]["fact_ids"] = ["F999"]
def _clue_unknown_evidence(c): c.clues[0]["evidence_ids"] = ["E999"]
def _clue_unknown_suspect(c): c.clues[0]["suspect_ids"] = ["ghost"]
def _clue_case_variant(c): c.clues[0]["suspect_ids"] = ["Cook"]
def _clue_lie(c): c.clues[0]["fact_ids"] = ["L001"]
def _clue_unsupported(c): c.clues[0]["evidence_ids"] = ["E002"]
def _clue_missing_key(c): del c.clues[0]["evidence_ids"]
def _clue_none_ids(c): c.clues[0]["fact_ids"] = None
def _clue_scalar_ids(c): c.clues[0]["suspect_ids"] = 5
def _clue_dup_refs(c): c.clues[0]["fact_ids"] = ["F001", "F001"]
def _clue_empty_refs(c): c.clues[0]["fact_ids"] = []
def _suspect_unclued(c):
    for clue in c.clues:
        clue["suspect_ids"] = [s for s in clue["suspect_ids"] if s != "housekeeper"] or ["cook"]
def _timeline_swapped(c): c.timeline[0], c.timeline[1] = c.timeline[1], c.timeline[0]
def _timeline_equal_times(c): c.timeline[1]["time_minute"] = c.timeline[0]["time_minute"]
def _timeline_str_time(c): c.timeline[2]["time_minute"] = "21:00"
def _timeline_float_time(c): c.timeline[2]["time_minute"] = 1200.5
def _timeline_bool_time(c): c.timeline[0]["time_minute"] = True
def _timeline_after_midnight(c): c.timeline[-1]["time_minute"] = 24 * 60
def _timeline_negative(c): c.timeline[0]["time_minute"] = -5
def _timeline_dup_id(c): c.timeline[1]["event_id"] = c.timeline[0]["event_id"]
def _timeline_bad_id(c): c.timeline[0]["event_id"] = "t001"
def _timeline_no_victim(c): del c.timeline[3]["victim_id"]
def _timeline_two_victims(c): c.timeline[3]["victim_id"] = "lady_ashby"
def _timeline_unknown_suspect(c): c.timeline[3]["suspect_ids"] = ["ghost"]
def _timeline_unknown_fact(c): c.timeline[3]["fact_ids"] = ["F999"]
def _timeline_lie(c): c.timeline[3]["fact_ids"] = ["L001"]
def _timeline_empty(c): c.timeline.clear()
def _timeline_no_text(c): c.timeline[0]["event"] = ""
def _suspect_off_timeline(c):
    for event in c.timeline:
        event["suspect_ids"] = [s for s in event["suspect_ids"] if s != "housekeeper"]
def _only_two_suspects(c): del c.npc_grants["housekeeper"]
def _four_suspects(c): c.npc_grants["maid"] = copy.deepcopy(c.npc_grants["cook"])
def _wrong_case_id(c): c.case_id = "case_999"
def _bad_fact_id(c):
    c.canonical_facts["f001"] = c.canonical_facts.pop("F001")
    c.fact_meta["f001"] = c.fact_meta.pop("F001")
def _non_str_fact_id(c):
    c.canonical_facts[1] = "x"; c.fact_meta[1] = copy.deepcopy(c.fact_meta["F001"])
def _lie_not_L(c): c.fact_meta["F005"].kind = "cover_story"
def _negative_reveal(c): c.fact_meta["F005"].reveal_at = -1
def _uppercase_term(c): c.fact_meta["F005"].terms = ["Corridor"]
def _lost_meta(c): del c.fact_meta["F005"]
def _grant_dup(c): c.npc_grants["cook"].fact_ids = ["F003", "F003"]
def _discovered_dup(c): c.discovered_evidence_ids = ["E001", "E001"]
def _bad_evidence_id(c): c.evidence["e002"] = c.evidence.pop("E002")
def _evidence_dup_facts(c): c.evidence["E002"].fact_ids = ["F002", "F002"]
def _started_midway(c): c.progression = 1
def _L001_demoted(c): c.fact_meta["L001"].kind = "fact"

MALFORMED = [
    (_drop_clue, "exactly ten clues"), (_extra_clue, "exactly ten clues"),
    (_dup_clue_id, "Clue IDs must be unique"), (_bad_clue_id, "Malformed clue ID"),
    (_clue_not_dict, "string clue_id"), (_clue_unknown_fact, "unknown fact"),
    (_clue_unknown_evidence, "unknown evidence"), (_clue_unknown_suspect, "unknown suspect"),
    (_clue_case_variant, "unknown suspect"), (_clue_lie, "authored lie"),
    (_clue_unsupported, "no listed evidence supports"), (_clue_missing_key, "list of ID strings"),
    (_clue_none_ids, "list of ID strings"), (_clue_scalar_ids, "list of ID strings"),
    (_clue_dup_refs, "duplicate IDs"), (_clue_empty_refs, "must reference a fact"),
    (_suspect_unclued, "at least one clue"),
    (_timeline_swapped, "ordered integer times"), (_timeline_equal_times, "ordered integer times"),
    (_timeline_str_time, "ordered integer times"), (_timeline_float_time, "ordered integer times"),
    (_timeline_bool_time, "ordered integer times"), (_timeline_after_midnight, "ordered integer times"),
    (_timeline_negative, "ordered integer times"),
    (_timeline_dup_id, "Timeline event IDs must be unique"),
    (_timeline_bad_id, "Malformed timeline event ID"), (_timeline_no_victim, "has no victim"),
    (_timeline_two_victims, "exactly one victim"), (_timeline_unknown_suspect, "unknown suspect"),
    (_timeline_unknown_fact, "unknown fact"), (_timeline_lie, "authored lie"),
    (_timeline_empty, "ground-truth timeline"), (_timeline_no_text, "no description"),
    (_suspect_off_timeline, "at least one timeline event"),
    (_only_two_suspects, "exactly the three suspects"), (_four_suspects, "exactly the three suspects"),
    (_wrong_case_id, "Invalid case fixture id"), (_bad_fact_id, "Malformed fact ID"),
    (_non_str_fact_id, "Malformed fact ID"), (_lie_not_L, "only L### IDs"),
    (_negative_reveal, "Invalid reveal_at"), (_uppercase_term, "Invalid terms"),
    (_lost_meta, "exactly one fact_meta"), (_grant_dup, "duplicate IDs"),
    (_discovered_dup, "duplicate IDs"), (_bad_evidence_id, "Malformed evidence ID"),
    (_evidence_dup_facts, "duplicate IDs"), (_started_midway, "progression 0"),
    (_L001_demoted, "L001: only L### IDs"),
]


@pytest.mark.parametrize("mutate,message", MALFORMED, ids=[m.__name__.strip("_") for m, _ in MALFORMED])
def test_malformed_case_001_data_is_rejected_with_contract_error(mutate, message):
    with pytest.raises(ContractError, match=message):
        _validate_case_001(_bad(mutate))


@pytest.mark.parametrize("mutate,message", MALFORMED, ids=[m.__name__.strip("_") for m, _ in MALFORMED])
def test_load_case_fails_safely_when_authored_data_is_malformed(monkeypatch, mutate, message):
    """Through the public entry point: only ContractError ever escapes, and a good load still works."""
    monkeypatch.setitem(engine._CASES, CASE_001_ID, (lambda: _bad(mutate), _validate_case_001))
    with pytest.raises(ContractError):
        load_case(CASE_001_ID)
    monkeypatch.undo()
    assert load_case(CASE_001_ID) == make_case_001()


def _meta_wrong_type(c): c.fact_meta["F005"] = "not a FactMeta"
def _grant_wrong_type(c): c.npc_grants["cook"] = None
def _evidence_wrong_type(c): c.evidence["E002"] = {"evidence_id": "E002"}
def _facts_wrong_type(c): c.canonical_facts = ["F001"]
def _clues_wrong_type(c): c.clues = {"C001": {}}
def _timeline_wrong_type(c): c.timeline = "T001"
def _timeline_event_none(c): c.timeline[0] = None

STRUCTURALLY_WRONG = [_meta_wrong_type, _grant_wrong_type, _evidence_wrong_type, _facts_wrong_type,
                      _clues_wrong_type, _timeline_wrong_type, _timeline_event_none]


@pytest.mark.parametrize("mutate", STRUCTURALLY_WRONG, ids=[m.__name__.strip("_") for m in STRUCTURALLY_WRONG])
def test_structurally_wrong_objects_are_converted_to_contract_error(monkeypatch, mutate):
    """Wrong *types* (not just wrong values) raise stray AttributeError/TypeError inside the validator;
    load_case must still surface them as ContractError so no caller has to catch anything else."""
    monkeypatch.setitem(engine._CASES, CASE_001_ID, (lambda: _bad(mutate), _validate_case_001))
    with pytest.raises(ContractError):
        load_case(CASE_001_ID)


def test_validator_is_shared_so_case_002_gets_the_same_protection():
    case = load_case(CASE_002_ID)
    swapped = copy.deepcopy(case)
    swapped.timeline[0], swapped.timeline[1] = swapped.timeline[1], swapped.timeline[0]
    with pytest.raises(ContractError, match="ordered integer times"):
        _validate_case_002(swapped)
    lied = copy.deepcopy(case)
    lied.clues[0]["fact_ids"] = ["L001"]
    with pytest.raises(ContractError, match="authored lie"):
        _validate_case_002(lied)


@pytest.mark.parametrize("case_id", ["case_003", "Case_001", "CASE_001", "case_001 ", " case_001", "case_001\n",
                                     "case-001", "case_01", "", None, 1, 1.0, b"case_001", ["case_001"], {}])
def test_unknown_or_invalid_ids_never_load_anything(case_id):
    with pytest.raises(ContractError):
        load_case(case_id)


# ---- deterministic "can suspect S know fact F?" queries -------------------------------

def test_fact_access_golden_table():
    case = load_case(CASE_001_ID)
    A, N, G = Access.ALLOWED, Access.NOT_YET_REVEALED, Access.NOT_GRANTED
    golden = {
        # (suspect, fact): verdicts at progression 0, 1, 2, 3
        ("gardener", "F001"): (A, A, A, A), ("gardener", "F002"): (A, A, A, A),
        ("gardener", "F003"): (G, G, G, G), ("gardener", "F004"): (G, G, G, G),   # spoiler never granted
        ("gardener", "L001"): (G, G, G, G),
        ("cook", "F003"): (A, A, A, A), ("cook", "L001"): (A, A, A, A),
        ("cook", "F001"): (G, G, G, G), ("cook", "F004"): (G, G, G, G),
        ("cook", "F005"): (G, G, G, G), ("cook", "F010"): (G, G, G, G),          # the guilty cook is not granted her own crime
        ("housekeeper", "F007"): (A, A, A, A),
        ("housekeeper", "F008"): (N, A, A, A),
        ("housekeeper", "F004"): (N, N, A, A),
        ("housekeeper", "F001"): (G, G, G, G), ("housekeeper", "F010"): (G, G, G, G),
        ("housekeeper", "L001"): (G, G, G, G),
    }
    for (suspect, fact), verdicts in golden.items():
        assert tuple(fact_access(case, suspect, fact, progression=p) for p in range(4)) == verdicts, (suspect, fact)
        assert tuple(can_suspect_know_fact(case, suspect, fact, progression=p) for p in range(4)) \
            == tuple(v == A for v in verdicts)


def test_evidence_access_golden_table():
    case = load_case(CASE_001_ID)
    A, N, G = Access.ALLOWED, Access.NOT_YET_REVEALED, Access.NOT_GRANTED
    golden = {
        ("gardener", "E001"): (A, A, A, A), ("gardener", "E003"): (A, A, A, A),
        ("gardener", "E009"): (G, G, G, G), ("gardener", "E007"): (G, G, G, G),
        ("cook", "E001"): (G, G, G, G), ("cook", "E009"): (G, G, G, G),
        ("housekeeper", "E007"): (A, A, A, A),
        ("housekeeper", "E008"): (N, A, A, A),
        ("housekeeper", "E009"): (N, N, A, A),
        ("housekeeper", "E011"): (G, G, G, G),
    }
    for (suspect, evidence), verdicts in golden.items():
        assert tuple(evidence_access(case, suspect, evidence, progression=p) for p in range(4)) == verdicts
        assert tuple(can_suspect_use_evidence(case, suspect, evidence, progression=p) for p in range(4)) \
            == tuple(v == A for v in verdicts)


def test_queries_default_to_the_cases_progression_and_never_mutate_it():
    case = load_case(CASE_001_ID)
    before = copy.deepcopy(case)
    assert fact_access(case, "housekeeper", "F008") == Access.NOT_YET_REVEALED
    case.progression = 1
    assert fact_access(case, "housekeeper", "F008") == Access.ALLOWED
    assert fact_access(case, "housekeeper", "F008", progression=0) == Access.NOT_YET_REVEALED   # explicit wins
    assert case.progression == 1
    case.progression = 0
    assert case == before


def test_queries_are_deterministic_and_return_plain_values():
    case = load_case(CASE_001_ID)
    runs = [[(s, f, fact_access(case, s, f, progression=p))
             for s in case.npc_grants for f in case.canonical_facts for p in range(4)] for _ in range(3)]
    assert runs[0] == runs[1] == runs[2]
    assert all(type(v) is str for _, _, v in runs[0])
    assert type(can_suspect_know_fact(case, "cook", "F003")) is bool


@pytest.mark.parametrize("suspect", ["Gardener", "GARDENER", " gardener", "gardener ", "", "butler", "aman",
                                     None, 1, ["gardener"], {"gardener"}])
def test_queries_reject_unknown_or_inexact_suspects(suspect):
    case = load_case(CASE_001_ID)
    with pytest.raises(ContractError):
        fact_access(case, suspect, "F001")
    with pytest.raises(ContractError):
        evidence_access(case, suspect, "E001")


@pytest.mark.parametrize("fact", ["f001", "F001 ", " F001", "F999", "", None, 1, ["F001"]])
def test_fact_query_rejects_unknown_or_inexact_facts(fact):
    with pytest.raises(ContractError):
        fact_access(load_case(CASE_001_ID), "gardener", fact)


@pytest.mark.parametrize("evidence", ["e001", "E001 ", "E999", "F001", "", None, 1, ["E001"]])
def test_evidence_query_rejects_unknown_or_inexact_evidence(evidence):
    with pytest.raises(ContractError):
        evidence_access(load_case(CASE_001_ID), "gardener", evidence)


@pytest.mark.parametrize("level", [-1, "1", 1.0, 1.5, True, False, [], object()])
def test_queries_reject_invalid_progression(level):
    with pytest.raises(ContractError):
        fact_access(load_case(CASE_001_ID), "gardener", "F001", progression=level)


@pytest.mark.parametrize("bad_case", [None, "case_001", {}, [], 1])
def test_queries_reject_non_case_objects(bad_case):
    with pytest.raises(ContractError):
        fact_access(bad_case, "gardener", "F001")
