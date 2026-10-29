"""Tests for Ananya Narula's deterministic branching baseline."""

from shared.fixture_case import make_case_001
from shared.contracts import SAFE_FALLBACK_TEXT
from members.ananya.branching_baseline import answer_branching

import pytest


@pytest.fixture(autouse=True)
def _use_local_dev_fixture(monkeypatch, tmp_path):
    """These unit tests target the member-local Q001..Q006 development fixture.
    The canonical shared set (test_cases/benchmark_questions.json) is covered by
    tests/test_branching_shared_set.py."""
    import members.ananya.branching_baseline as module
    monkeypatch.setattr(module, "SHARED_QUESTION_SET", tmp_path / "absent.json")


def test_branching_returns_comparable_dialogue_result():
    result = answer_branching(make_case_001(), "gardener", "Q001")
    assert result.valid is True
    assert result.used_fallback is False
    assert result.metrics is not None
    assert result.metrics.mode == "branching"
    assert result.metrics.model == "fixed-tree"
    assert result.latency_ms == result.metrics.total_ms
    assert result.cited_fact_ids == ["F001"]


def test_branching_answers_same_case_fact():
    result = answer_branching(make_case_001(), "gardener", "Q002")
    assert result.valid is True
    assert "glass" in result.text.lower()
    assert result.cited_fact_ids == ["F002"]


def test_branching_supports_authored_cover_story():
    result = answer_branching(make_case_001(), "cook", "Q004")
    assert result.valid is True
    assert result.cited_fact_ids == ["L001"]


def test_branching_does_not_reveal_future_fact():
    result = answer_branching(make_case_001(progression=0), "gardener", "Q005")
    assert result.valid is True
    assert result.used_fallback is False
    assert "poisoned" not in result.text.lower()
    assert "F004" not in result.cited_fact_ids


def test_hostile_evidence_is_not_executed_as_instruction():
    result = answer_branching(
        make_case_001(), "gardener", "Q006", presented_evidence_ids=["E003"]
    )
    assert result.valid is True
    assert "poisoned" not in result.text.lower()
    assert result.cited_fact_ids == []


def test_unauthorized_evidence_is_rejected():
    result = answer_branching(
        make_case_001(), "gardener", "Q001", presented_evidence_ids=["E009"]
    )
    assert result.valid is False
    assert result.used_fallback is True
    assert result.text == SAFE_FALLBACK_TEXT


def test_unknown_question_is_safe_failure():
    result = answer_branching(make_case_001(), "gardener", "Q999")
    assert result.valid is False
    assert result.used_fallback is True
    assert result.reasons == ["SETUP_ERROR"]


def test_unknown_npc_is_safe_failure():
    result = answer_branching(make_case_001(), "detective", "Q001")
    assert result.valid is False
    assert result.used_fallback is True
    assert result.reasons == ["NPC_MISMATCH"]


def test_branching_does_not_mutate_case_state():
    case = make_case_001()
    before_progression = case.progression
    before_discovered = list(case.discovered_evidence_ids)

    answer_branching(case, "gardener", "Q001")

    assert case.progression == before_progression
    assert case.discovered_evidence_ids == before_discovered


def test_branching_rejects_authored_branch_that_contains_future_term(monkeypatch):
    # This protects against an accidental spoiler in a fixed dialogue node.
    import members.ananya.branching_baseline as module

    monkeypatch.setattr(
        module,
        "_load_question_set",
        lambda: {
            "BAD": {
                "question_id": "BAD",
                "npc_id": "gardener",
                "answer": "The brandy was poisoned.",
                "fact_ids": [],
                "evidence_ids": [],
            }
        },
    )

    result = module.answer_branching(make_case_001(), "gardener", "BAD")

    assert result.valid is False
    assert result.used_fallback is True


def test_success_path_reports_measured_nonzero_latency_consistently():
    result = answer_branching(make_case_001(), "gardener", "Q001")
    assert result.used_fallback is False
    assert result.metrics.total_ms > 0.0
    assert result.latency_ms == result.metrics.total_ms
