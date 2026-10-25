import copy

import pytest

from members.anand.npc_knowledge import NPCContext, UnknownNPCError, build_npc_context


@pytest.fixture
def sample_case():
    return {
        "npcs": [
            {
                "id": "Alice",
                "name": "Alice",
                "known_facts": ["fact_1"],
                "suspicions": ["fact_2"],
            },
            {
                "id": "Bob",
                "name": "Bob",
                "cover_story": ["fact_3"],
            },
        ],
        "facts": [
            {
                "fact_id": "fact_1",
                "summary": "Alice's secret identity was exposed.",
                "authorized_for": ["Alice"],
            },
            {
                "fact_id": "fact_2",
                "summary": "The butler is the hidden suspect.",
                "authorized_for": ["Alice"],
                "category": "suspected",
                "required_discovery": ["fact_1"],
            },
            {
                "fact_id": "fact_3",
                "summary": "Bob invented a cover story about the ledger.",
                "authorized_for": ["Bob"],
                "category": "lie",
            },
            {
                "fact_id": "fact_4",
                "summary": "This clue requires a discovery gate.",
                "authorized_for": ["Alice"],
                "required_discovery": ["missing_fact"],
            },
        ],
        "progress": {"discovered_facts": ["fact_1"]},
    }


def test_authorized_and_filtered_context(sample_case):
    context = build_npc_context(sample_case, "Alice")

    assert isinstance(context, NPCContext)
    assert set(context.keys()) == {"npc_id", "known_facts", "suspected_facts", "cover_story"}
    assert context["npc_id"] == "Alice"
    assert [fact["fact_id"] for fact in context["known_facts"]] == ["fact_1"]
    assert [fact["fact_id"] for fact in context["suspected_facts"]] == ["fact_2"]
    assert context["cover_story"] == []


def test_unauthorized_fact_excluded(sample_case):
    context = build_npc_context(sample_case, "Alice")
    fact_ids = {fact["fact_id"] for fact in context["known_facts"] + context["suspected_facts"] + context["cover_story"]}
    assert "fact_3" not in fact_ids


def test_progression_gate_filters_fact_until_available(sample_case):
    gated = copy.deepcopy(sample_case)
    gated["facts"].append(
        {
            "fact_id": "fact_5",
            "summary": "Unlocked after discovery.",
            "authorized_for": ["Alice"],
            "required_discovery": ["fact_9"],
        }
    )
    context = build_npc_context(gated, "Alice")
    fact_ids = {fact["fact_id"] for fact in context["known_facts"] + context["suspected_facts"] + context["cover_story"]}
    assert "fact_5" not in fact_ids


def test_unknown_npc_raises_error(sample_case):
    with pytest.raises(UnknownNPCError):
        build_npc_context(sample_case, "Mallory")


def test_identifier_capitalization_is_exact(sample_case):
    with pytest.raises(UnknownNPCError):
        build_npc_context(sample_case, "alice")


def test_no_input_mutation(sample_case):
    original = copy.deepcopy(sample_case)
    build_npc_context(sample_case, "Alice")
    assert sample_case == original


def test_mutable_output_is_independent(sample_case):
    context = build_npc_context(sample_case, "Alice")
    context["known_facts"].append({"fact_id": "rogue", "summary": "mutated"})
    original_ids = [fact["fact_id"] for fact in sample_case["facts"] if fact["fact_id"] == "fact_1"]
    assert original_ids == ["fact_1"]
    assert "rogue" not in {fact["fact_id"] for fact in sample_case["facts"]}


def test_multiple_npc_isolation(sample_case):
    alice = build_npc_context(sample_case, "Alice")
    bob = build_npc_context(sample_case, "Bob")
    assert [fact["fact_id"] for fact in alice["known_facts"]] == ["fact_1"]
    assert [fact["fact_id"] for fact in bob["cover_story"]] == ["fact_3"]
    assert "fact_1" not in {fact["fact_id"] for fact in bob["known_facts"] + bob["suspected_facts"] + bob["cover_story"]}
