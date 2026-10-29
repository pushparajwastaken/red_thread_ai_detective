"""Module 2 (NPC Knowledge) against the REAL shared types, the canonical
fixture, and the REAL Case Engine. Replaces an earlier dict-shaped test that
exercised a data shape the contract never defined."""
import copy
from dataclasses import asdict

import pytest

import shared.contracts as C
from members.anand.npc_knowledge import build_npc_context
from members.richa.case_engine import load_case
from shared.fixture_case import make_case_001


def test_uses_shared_contract_types_not_private_copies():
    import members.anand.npc_knowledge as nk
    assert nk.NPCContext is C.NPCContext
    assert nk.UnknownNPCError is C.UnknownNPCError
    assert isinstance(build_npc_context(make_case_001(), "gardener"), C.NPCContext)


@pytest.mark.parametrize("source", ["fixture", "real_engine"])
def test_gardener_context_at_progression_0(source):
    case = make_case_001() if source == "fixture" else load_case("case_001")
    ctx = build_npc_context(case, "gardener")
    assert ctx.npc_id == "gardener"
    assert ctx.authorized_fact_ids == ["F001", "F002"]
    assert ctx.permitted_evidence_ids == ["E001", "E003"]
    assert ctx.persona == "A blunt old gardener."
    assert ctx.beliefs == [] and ctx.suspicions == []


def test_cook_gets_cover_story_but_not_gardener_facts_or_spoilers():
    ctx = build_npc_context(load_case("case_001"), "cook")
    assert ctx.authorized_fact_ids == ["F003", "L001"]   # cover story is granted
    assert ctx.permitted_evidence_ids == []
    assert not {"F001", "F002", "F004"} & set(ctx.authorized_fact_ids)


def test_future_fact_is_never_granted_before_reveal_even_if_granted():
    case = make_case_001()
    case.npc_grants["gardener"].fact_ids.append("F004")     # reveal_at == 2
    case.npc_grants["gardener"].evidence_ids.append("E009")  # reveal_at == 2
    for prog in (0, 1):
        case.progression = prog
        ctx = build_npc_context(case, "gardener")
        assert "F004" not in ctx.authorized_fact_ids
        assert "E009" not in ctx.permitted_evidence_ids
    case.progression = 2
    ctx = build_npc_context(case, "gardener")
    assert "F004" in ctx.authorized_fact_ids and "E009" in ctx.permitted_evidence_ids


def test_ungranted_future_fact_not_leaked_at_any_progression():
    for prog in range(0, 4):
        ctx = build_npc_context(make_case_001(progression=prog), "cook")
        assert "F004" not in ctx.authorized_fact_ids
        assert "E009" not in ctx.permitted_evidence_ids


@pytest.mark.parametrize("bad", ["Gardener", "GARDENER", " gardener", "gardener ", "", "aman", None, 1, ["gardener"]])
def test_unknown_or_inexact_npc_raises_shared_error(bad):
    with pytest.raises(C.UnknownNPCError):
        build_npc_context(make_case_001(), bad)


def test_case_not_mutated():
    case = make_case_001(progression=2)
    before = copy.deepcopy(case)
    build_npc_context(case, "gardener")
    assert case == before


def test_returned_lists_are_fresh_copies():
    case = make_case_001()
    ctx = build_npc_context(case, "gardener")
    ctx.authorized_fact_ids.append("F004")
    ctx.permitted_evidence_ids.clear()
    assert case.npc_grants["gardener"].fact_ids == ["F001", "F002"]
    again = build_npc_context(case, "gardener")
    assert again.authorized_fact_ids == ["F001", "F002"]
    assert again.permitted_evidence_ids == ["E001", "E003"]


def test_deterministic_repeatability():
    case = load_case("case_001")
    assert asdict(build_npc_context(case, "cook")) == asdict(build_npc_context(case, "cook"))


def test_progression_advances_real_case_002_reveals_gradually():
    case = load_case("case_002")
    case = load_case("case_002")
    case.progression = 0
    assert "F007" not in build_npc_context(case, "rohan").authorized_fact_ids  # reveal_at 1
    case.progression = 1
    assert "F007" in build_npc_context(case, "rohan").authorized_fact_ids
