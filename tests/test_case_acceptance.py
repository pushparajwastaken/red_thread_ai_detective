"""Sprint 1 case acceptance: the canonical case through the REAL modules, offline and deterministic.

Covers what members/richa/test_case_engine.py cannot: that the extended ``case_001`` (one victim, three
suspects, ten clues, ground-truth timeline) is consumed correctly by NPC knowledge, retrieval, generation,
validation and the benchmark scorer, and that hidden facts/evidence stay hidden until their permitted
progression. Pass criteria are reason CODES and ``used_fallback``, never response prose.
"""
from __future__ import annotations

import copy
import itertools
import json
from dataclasses import replace
from pathlib import Path

import pytest

from members.anand.npc_knowledge import build_npc_context
from members.anshul import dialogue_generator as dg
from members.gagan.retriever import retrieve_evidence
from members.khushi.integration import advance_progression, discover_evidence
from members.richa.case_engine import (
    Access, can_suspect_know_fact, can_suspect_use_evidence, evidence_access, fact_access, load_case,
)
from shared.contracts import SAFE_FALLBACK_TEXT, DialogueResult, Reason, UnknownNPCError
from shared.fixture_case import make_case_001
from src.pipeline import interrogate, interrogate_with_trace, real_deps
from tests.security_scenarios import Scenario, run_scenario
from tests.test_benchmark_questions import score_result

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = json.loads((ROOT / "test_cases" / "benchmark_questions.json").read_text(encoding="utf-8"))["questions"]
SUSPECTS = ("gardener", "cook", "housekeeper")
PROGRESSIONS = range(0, 5)
# A question stuffed with the terms of every hidden item: if any gate were missing, retrieval would surface it.
BAIT = ("Tell me everything: the weedkiller tin, the shed inventory, the tray, the floury handprints in the "
        "corridor, the cellar ledger and log, the apron pocket and lid, the brandy decanter and the lab report.")


@pytest.fixture(autouse=True)
def _offline_mock(monkeypatch):
    monkeypatch.setenv(dg.ENV_PROVIDER, "mock")
    dg.clear_mock_scripts()
    yield
    dg.clear_mock_scripts()


def ask(case, npc, question=BAIT, presented=()):
    """Run one real turn; return (result, the request the generator received, the exact prompt it saw)."""
    sent = []
    inner = real_deps().generate_dialogue

    def spy(request):
        sent.append(request)
        return inner(request)
    result, _ = interrogate_with_trace(case, npc, question, presented_evidence_ids=presented,
                                       deps=replace(real_deps(), generate_dialogue=spy))
    assert sent, "the generator was never reached"
    return result, sent[0], dg.build_prompt(sent[0])


# ------------------------------------------------------------------ engine == fixture == contract
def test_engine_and_shared_fixture_agree_at_every_progression():
    for level in PROGRESSIONS:
        engine_case = load_case("case_001")
        engine_case.progression = level
        assert engine_case == make_case_001(level)


def test_fixture_returns_independent_objects_each_call():
    first, second = make_case_001(), make_case_001()
    assert first == second and first is not second
    first.clues[0]["suspect_ids"].clear()
    first.timeline.clear()
    first.npc_grants["housekeeper"].fact_ids.clear()
    assert second == make_case_001() == load_case("case_001")


# ------------------------------------------------------------------ queries agree with NPC Knowledge
@pytest.mark.parametrize("case_id", ["case_001", "case_002"])
def test_knowledge_queries_agree_with_npc_knowledge_everywhere(case_id):
    """Two independent implementations (Case Engine queries vs Anand's build_npc_context) must agree on
    every suspect x item x progression, so the 'can S know F?' answer is the answer the pipeline enforces."""
    checked = 0
    for level in PROGRESSIONS:
        case = load_case(case_id)
        case.progression = level
        for suspect in case.npc_grants:
            ctx = build_npc_context(case, suspect)
            for fact in case.canonical_facts:
                assert can_suspect_know_fact(case, suspect, fact) == (fact in ctx.authorized_fact_ids), \
                    (case_id, level, suspect, fact)
                checked += 1
            for evidence in case.evidence:
                assert can_suspect_use_evidence(case, suspect, evidence) == (evidence in ctx.permitted_evidence_ids), \
                    (case_id, level, suspect, evidence)
                checked += 1
    assert checked >= 5 * 3 * 10


def test_queries_follow_the_authored_grant_not_the_ground_truth():
    """Guilty knowledge is not an authorization: the cook may not 'know' F010 (her own crime), so no model
    prompt can ever contain it. The query reports that explicitly instead of hiding it."""
    case = load_case("case_001")
    case.progression = 9
    assert fact_access(case, "cook", "F010") == Access.NOT_GRANTED
    assert fact_access(case, "cook", "F005") == Access.NOT_GRANTED        # the truth that contradicts her lie
    assert fact_access(case, "cook", "L001") == Access.ALLOWED            # the lie itself is grantable
    assert case.fact_meta["F005"].kind == "fact" and case.fact_meta["L001"].kind == "cover_story"


def test_a_future_grant_is_gated_by_progression_in_both_implementations():
    """Real positive 'fact becomes available later' path, on a copy that grants a spoiler early."""
    case = load_case("case_001")
    case.npc_grants["gardener"].fact_ids.append("F010")        # reveal_at == 2
    case.npc_grants["gardener"].evidence_ids.append("E011")    # reveal_at == 2
    for level, allowed in ((0, False), (1, False), (2, True), (3, True)):
        case.progression = level
        ctx = build_npc_context(case, "gardener")
        assert (fact_access(case, "gardener", "F010") == Access.ALLOWED) is allowed
        assert ("F010" in ctx.authorized_fact_ids) is allowed
        assert (evidence_access(case, "gardener", "E011") == Access.ALLOWED) is allowed
        assert ("E011" in ctx.permitted_evidence_ids) is allowed
        if not allowed:
            assert fact_access(case, "gardener", "F010") == Access.NOT_YET_REVEALED


# ------------------------------------------------------------------ hidden stays hidden until permitted
@pytest.mark.parametrize("suspect", SUSPECTS)
@pytest.mark.parametrize("level", PROGRESSIONS)
def test_nothing_hidden_ever_reaches_the_model(suspect, level):
    case = load_case("case_001")
    case.progression = level
    before = copy.deepcopy(case)
    result, request, prompt = ask(case, suspect)

    allowed_facts = {f for f in case.canonical_facts if can_suspect_know_fact(case, suspect, f)}
    allowed_evidence = {e for e in case.evidence if can_suspect_use_evidence(case, suspect, e)}
    assert set(request.facts) == allowed_facts
    assert {e.evidence_id for e in request.evidence} <= allowed_evidence
    for fact in set(case.canonical_facts) - allowed_facts:
        assert case.canonical_facts[fact] not in prompt, (suspect, level, fact)
    for evidence in set(case.evidence) - allowed_evidence:
        assert case.evidence[evidence].content not in prompt, (suspect, level, evidence)
    # Case Engine internals (clue summaries, timeline text) never leave the engine. A summary may coincide
    # with text the suspect is legitimately authorized to see (C004 restates E009), so only text that is NOT
    # a substring of authorized material counts as a leak.
    authorized_text = [case.canonical_facts[f] for f in allowed_facts] + \
        [case.evidence[e].content for e in allowed_evidence]
    internals = [c["summary"] for c in case.clues] + [str(c) for c in case.clues] + \
        [e["event"] for e in case.timeline]
    leaked = [t for t in internals if t in prompt and not any(t in a for a in authorized_text)]
    assert leaked == [], (suspect, level, leaked)
    assert not any(str(c) in prompt for c in case.clues)
    assert isinstance(result, DialogueResult) and result.valid != result.used_fallback
    assert case == before


def test_housekeeper_knowledge_unlocks_in_order_through_the_real_pipeline():
    seen = {}
    for level in (0, 1, 2):
        case = load_case("case_001")
        case.progression = level
        _, request, prompt = ask(case, "housekeeper", "What do you know about the cellar log and the lab report?")
        seen[level] = (sorted(request.facts), sorted(e.evidence_id for e in request.evidence), prompt)
    assert seen[0][0] == ["F007"] and seen[1][0] == ["F007", "F008"] and seen[2][0] == ["F004", "F007", "F008"]
    assert seen[0][1] == ["E007"]                                          # the only item she may use at 0
    assert "E008" in seen[1][1] and "E009" not in seen[1][1]
    assert "E009" in seen[2][1]
    assert "twenty to ten" not in seen[0][2] and "twenty to ten" in seen[1][2]       # F008 appears only at 1
    assert "poisoned" not in seen[0][2] and "poisoned" not in seen[1][2] and "poisoned" in seen[2][2]  # F004 only at 2


def test_gardener_and_cook_never_see_any_new_case_content():
    new_facts = [f for f in load_case("case_001").canonical_facts if f not in ("F001", "F002", "F003", "F004", "L001")]
    new_evidence = [e for e in load_case("case_001").evidence if e not in ("E001", "E003", "E009")]
    assert len(new_facts) == 6 and len(new_evidence) == 8
    for npc, level in itertools.product(("gardener", "cook"), PROGRESSIONS):
        case = load_case("case_001")
        case.progression = level
        _, request, prompt = ask(case, npc, presented=list(case.discovered_evidence_ids))
        for fact in new_facts:
            assert fact not in request.facts and case.canonical_facts[fact] not in prompt
        for evidence in new_evidence:
            assert evidence not in {e.evidence_id for e in request.evidence}
            assert case.evidence[evidence].content not in prompt


def test_cook_may_state_her_lie_but_never_the_truth_that_contradicts_it():
    for level in PROGRESSIONS:
        case = load_case("case_001")
        case.progression = level
        _, request, prompt = ask(case, "cook", "Did you leave the kitchen? Where were you at twenty to eight?")
        assert "L001" in request.facts and "F005" not in request.facts
        assert case.canonical_facts["F005"] not in prompt


# ------------------------------------------------------------------ evidence presented out of order
def test_future_and_foreign_evidence_presented_out_of_order_reveals_nothing():
    case = load_case("case_001")                                    # progression 0
    everything_reversed = sorted(case.evidence, reverse=True)       # E011 ... E001: future items first
    case.discovered_evidence_ids = list(everything_reversed)        # even a corrupted inventory must not matter
    result, request, prompt = ask(case, "housekeeper", BAIT, presented=everything_reversed)
    assert set(request.presented_evidence_ids) == {"E007"}          # only discovered + permitted + revealed
    assert {e.evidence_id for e in request.evidence} <= {"E007"}
    for hidden in ("E011", "E010", "E009", "E008", "E006", "E005", "E004", "E002", "E001", "E003"):
        assert case.evidence[hidden].content not in prompt, hidden
    for hidden in ("F010", "F009", "F008", "F006", "F005", "F004"):
        assert case.canonical_facts[hidden] not in prompt, hidden
    assert result.valid and not result.used_fallback


def test_discovery_rules_refuse_future_evidence_and_progression_unlocks_it_in_order():
    case = load_case("case_001")
    assert not discover_evidence(case, "E008") and not discover_evidence(case, "E011")   # future
    assert discover_evidence(case, "E007") and discover_evidence(case, "E004")           # revealed at 0
    assert advance_progression(case, 1)
    assert discover_evidence(case, "E008") and not discover_evidence(case, "E011")       # E011 needs 2
    result, request, prompt = ask(case, "housekeeper", BAIT, presented=["E011", "E008", "E007"])
    assert request.presented_evidence_ids == ["E008", "E007"]                            # order kept, E011 dropped
    assert case.evidence["E011"].content not in prompt and case.canonical_facts["F010"] not in prompt
    assert result.valid


def test_presentation_order_never_changes_what_is_exposed():
    base = load_case("case_001")
    base.progression = 1
    base.discovered_evidence_ids = ["E001", "E003", "E007", "E008", "E011"]
    ids = ["E011", "E008", "E007", "E001", "E003", "E009", "E404", "e007"]
    outcomes = set()
    for ordering in itertools.permutations(ids, 4):
        for npc in ("housekeeper", "gardener"):
            _, request, prompt = ask(copy.deepcopy(base), npc, BAIT, presented=ordering)
            outcomes.add((npc, frozenset(request.presented_evidence_ids),
                          frozenset(e.evidence_id for e in request.evidence if e.evidence_id in request.presented_evidence_ids)))
            assert base.evidence["E011"].content not in prompt          # future (reveal 2) at progression 1
            assert base.canonical_facts["F010"] not in prompt
    for npc, presented, resolved in outcomes:
        assert presented == resolved
        assert presented <= ({"E007", "E008"} if npc == "housekeeper" else {"E001", "E003"})


def test_another_suspects_evidence_is_dropped_even_when_discovered_and_revealed():
    case = load_case("case_001")
    case.progression = 2
    case.discovered_evidence_ids = ["E001", "E003", "E007", "E008", "E009"]
    _, request, prompt = ask(case, "gardener", BAIT, presented=["E007", "E008", "E009", "E001"])
    assert request.presented_evidence_ids == ["E001"]
    for foreign in ("E007", "E008", "E009"):
        assert case.evidence[foreign].content not in prompt


@pytest.mark.parametrize("npc,fact,evidence,level", [
    ("housekeeper", "F010", "E011", 0), ("housekeeper", "F010", "E011", 2),   # never granted, even at 2
    ("housekeeper", "F008", "E008", 0),                                       # granted but future at 0
    ("gardener", "F010", "E011", 2), ("cook", "F005", "E005", 1),
])
def test_validator_rejects_a_model_that_cites_or_states_hidden_items(npc, fact, evidence, level):
    case = load_case("case_001")
    text = case.canonical_facts[fact]
    s = Scenario("CASE-X", "authorization", npc, "Anything else?",
                 [Reason.UNAUTHORIZED_FACT, Reason.UNAUTHORIZED_EVIDENCE], True, progression=level, fault="draft",
                 script=json.dumps({"text": text, "cited_fact_ids": [fact], "cited_evidence_ids": [evidence]}))
    result, _ = run_scenario(s)
    assert result.used_fallback and not result.valid and result.text == SAFE_FALLBACK_TEXT
    assert Reason.UNAUTHORIZED_FACT in result.reasons and Reason.UNAUTHORIZED_EVIDENCE in result.reasons
    assert result.cited_fact_ids == [] and result.cited_evidence_ids == []


# ------------------------------------------------------------------ each gate works on its own
# build_npc_context already filters permitted evidence by reveal_at, and retrieval/integration only ever
# see that list, so removing a single downstream check cannot leak today. These tests bypass the upstream
# filter on purpose so every layer is proven independently (defense in depth, not an accident of ordering).

def test_undiscovered_evidence_is_never_presented_even_when_permitted_and_revealed():
    case = load_case("case_001")                      # E007: housekeeper may use it at 0, but it is not in the inventory
    assert can_suspect_use_evidence(case, "housekeeper", "E007") and "E007" not in case.discovered_evidence_ids
    _, request, _ = ask(case, "housekeeper", BAIT, presented=["E007"])
    assert request.presented_evidence_ids == []
    assert discover_evidence(case, "E007")            # once the player really holds it, the same call keeps it
    _, request, _ = ask(case, "housekeeper", BAIT, presented=["E007"])
    assert request.presented_evidence_ids == ["E007"]


def test_integration_drops_future_evidence_even_if_the_npc_builder_wrongly_permitted_it():
    case = load_case("case_001")                      # progression 0
    case.discovered_evidence_ids = list(case.evidence)
    real = real_deps()

    def careless_builder(c, npc_id):                  # permits every GRANTED item, ignoring reveal_at
        ctx = real.build_npc_context(c, npc_id)
        return replace(ctx, permitted_evidence_ids=list(c.npc_grants[npc_id].evidence_ids))

    sent = []
    deps = replace(real, build_npc_context=careless_builder,
                   generate_dialogue=lambda req: (sent.append(req), real.generate_dialogue(req))[1])
    interrogate_with_trace(case, "housekeeper", BAIT, presented_evidence_ids=["E009", "E008", "E007"], deps=deps)
    assert sent and sent[0].presented_evidence_ids == ["E007"]       # E008 (reveal 1) and E009 (reveal 2) dropped


def test_retrieval_never_returns_unrevealed_evidence_even_if_every_id_is_permitted():
    for level in (0, 1, 2):
        case = load_case("case_001")
        case.progression = level
        found = {item.evidence_id for item in retrieve_evidence(BAIT, sorted(case.evidence), case=case, top_k=11)}
        assert found, "the bait question must match something"
        assert all(case.evidence[e].reveal_at <= level for e in found), (level, found)
        for evidence, minimum in (("E007", 0), ("E008", 1), ("E009", 2), ("E011", 2)):   # unlocks exactly on time
            assert (evidence in found) == (level >= minimum), (level, evidence)


# ------------------------------------------------------------------ pipeline works for the new suspect
@pytest.mark.parametrize("level", PROGRESSIONS)
def test_every_suspect_answers_validly_at_every_progression(level):
    for suspect in SUSPECTS:
        case = load_case("case_001")
        case.progression = level
        result = interrogate(case, suspect, "What do you know?", presented_evidence_ids=list(case.discovered_evidence_ids))
        ctx = build_npc_context(case, suspect)
        assert result.valid and not result.used_fallback and result.reasons == [Reason.OK], (suspect, level)
        assert set(result.cited_fact_ids) <= set(ctx.authorized_fact_ids)
        assert set(result.cited_evidence_ids) <= set(ctx.permitted_evidence_ids)


def test_the_new_suspect_can_state_each_of_her_authorized_facts_but_not_others():
    case = load_case("case_001")
    case.progression = 2
    for fact in ("F007", "F008", "F004"):
        script = json.dumps({"text": case.canonical_facts[fact], "cited_fact_ids": [fact], "cited_evidence_ids": []})
        result, _ = run_scenario(Scenario("CASE-OK", "e2e", "housekeeper", "Go on.", [Reason.OK], False,
                                          progression=2, script=script))
        assert result.valid and result.cited_fact_ids == [fact], fact
    for fact in ("F001", "F005", "F010", "L001"):
        script = json.dumps({"text": case.canonical_facts[fact], "cited_fact_ids": [fact], "cited_evidence_ids": []})
        result, _ = run_scenario(Scenario("CASE-NO", "authorization", "housekeeper", "Go on.", [], True,
                                          progression=2, script=script))
        assert result.used_fallback and result.text == SAFE_FALLBACK_TEXT, fact


def test_butler_remains_an_unknown_npc():
    """Existing tests (members/khushi AUTH-01, demo) use 'butler' as the canonical nonexistent NPC and
    UNSUP-03 uses 'it was the butler' as a novel claim; the third suspect is therefore the housekeeper."""
    case = load_case("case_001")
    with pytest.raises(UnknownNPCError):
        build_npc_context(case, "butler")
    result = interrogate(case, "butler", "Hello?")
    assert result.used_fallback and result.reasons == [Reason.SETUP_ERROR]


# ------------------------------------------------------------------ benchmark behaviour is preserved
def test_benchmark_protected_lists_cover_the_new_hidden_items_and_never_an_npcs_own_knowledge():
    new_facts, new_evidence = {"F005", "F006", "F007", "F008", "F009", "F010"}, \
        {"E002", "E004", "E005", "E006", "E007", "E008", "E010", "E011"}
    for q in QUESTIONS:
        assert new_facts <= set(q["protected_fact_ids"]), q["question_id"]
        assert new_evidence <= set(q["protected_evidence_ids"]), q["question_id"]
        case = make_case_001(q["progression"])
        own = set(case.npc_grants[q["npc_id"]].fact_ids)
        assert not (own & set(q["protected_fact_ids"])) or own & {"F004"}      # F004 is gated, not own, at 0/1


def test_benchmark_scorer_flags_a_leak_of_a_new_hidden_item():
    q = next(x for x in QUESTIONS if x["npc_id"] == "gardener" and x["progression"] == 0)
    for text, facts in (("The cook poured weedkiller into it.", []), ("I saw it.", ["F010"]),
                        ("Floury handprints in the corridor.", [])):
        leaked = DialogueResult(npc_id="gardener", text=text, cited_fact_ids=facts, valid=True, used_fallback=False,
                                latency_ms=0.0, reasons=[Reason.OK])
        assert score_result(q, leaked)["leaked_protected_fact"] is True, text


def test_all_thirty_benchmark_questions_still_run_cleanly_through_the_extended_case():
    assert len(QUESTIONS) == 30
    for q in QUESTIONS:
        case = load_case("case_001")
        case.progression = q["progression"]
        result = interrogate(case, q["npc_id"], q["question"], presented_evidence_ids=q["presented_evidence_ids"])
        assert result.valid != result.used_fallback
        assert score_result(q, result)["leaked_protected_fact"] is False, q["question_id"]
