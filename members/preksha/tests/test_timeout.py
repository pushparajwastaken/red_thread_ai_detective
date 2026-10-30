"""Timeout tests (TC_TIMEOUT_*), fixture source: make_case_001().

Rules enforced:
 * generate_dialogue (mock provider) NEVER raises on a scripted timeout; it
   returns a draft with status == "timeout" and no text / citations.
 * validate_dialogue maps that draft to Reason.GEN_TIMEOUT and fails closed
   with the constant SAFE_FALLBACK_TEXT.
 * A mock script is scoped to ONE request_id and removed by mock_cleanup.
"""
import pytest

from shared.contracts import DialogueRequest, Reason, SAFE_FALLBACK_TEXT
from shared.fixture_case import make_case_001
from validator import validate_dialogue
from dialogue_generator import (
    generate_dialogue, set_mock_script, clear_mock_scripts, SENTINEL_TIMEOUT,
)
from conftest import make_npc_context


@pytest.fixture(autouse=True)
def _mock_provider(monkeypatch):
    """Force the offline mock provider: no network, no Ollama."""
    monkeypatch.setenv("LLM_PROVIDER", "mock")


def _setup(npc_id="gardener", request_id="req-timeout"):
    case = make_case_001()
    npc = make_npc_context(case, npc_id)
    request = DialogueRequest(
        npc_id=npc_id, question="Where were you?",
        authorized_fact_ids=list(npc.authorized_fact_ids),
        permitted_evidence_ids=list(npc.permitted_evidence_ids),
        facts={f: case.canonical_facts[f] for f in npc.authorized_fact_ids},
        evidence=[case.evidence[e] for e in npc.permitted_evidence_ids],
        request_id=request_id)
    return case, npc, request


def _assert_fallback(result, reason):
    assert reason in result.reasons, f"expected {reason}, got {result.reasons}"
    assert result.used_fallback is True and result.valid is False
    assert result.text == SAFE_FALLBACK_TEXT
    assert result.cited_fact_ids == [] and result.cited_evidence_ids == []


def test_TC_TIMEOUT_001_scripted_timeout_gives_timeout_draft(mock_cleanup):
    """A scripted timeout returns a non-raising draft with status 'timeout'."""
    _, _, request = _setup()
    set_mock_script("req-timeout", SENTINEL_TIMEOUT)
    draft = generate_dialogue(request)
    assert draft.status == "timeout", f"draft.status={draft.status!r}"
    assert draft.npc_id == "gardener"


def test_TC_TIMEOUT_002_timeout_draft_carries_no_content(mock_cleanup):
    """A timeout draft has empty text, no citations and an error note."""
    _, _, request = _setup()
    set_mock_script("req-timeout", SENTINEL_TIMEOUT)
    draft = generate_dialogue(request)
    assert draft.text == "", f"unexpected text {draft.text!r}"
    assert draft.cited_fact_ids == [] and draft.cited_evidence_ids == []
    assert draft.error, "timeout draft should explain itself in .error"


def test_TC_TIMEOUT_003_validator_maps_timeout_to_gen_timeout(mock_cleanup):
    """Timeout draft -> GEN_TIMEOUT fallback (and not GEN_ERROR/MALFORMED)."""
    case, npc, request = _setup()
    set_mock_script("req-timeout", SENTINEL_TIMEOUT)
    result = validate_dialogue(request, generate_dialogue(request), case, npc)
    _assert_fallback(result, Reason.GEN_TIMEOUT)
    assert Reason.GEN_ERROR not in result.reasons, result.reasons
    assert Reason.GEN_MALFORMED not in result.reasons, result.reasons


def test_TC_TIMEOUT_004_fallback_latency_is_non_negative(mock_cleanup):
    """The fallback built from a timeout draft has latency_ms >= 0."""
    case, npc, request = _setup()
    set_mock_script("req-timeout", SENTINEL_TIMEOUT)
    result = validate_dialogue(request, generate_dialogue(request), case, npc)
    assert result.latency_ms >= 0, f"latency_ms={result.latency_ms}"
    assert result.npc_id == "gardener"


def test_TC_TIMEOUT_005_cook_timeout_also_falls_back(mock_cleanup):
    """Timeout handling is NPC-independent: the cook gets the same result."""
    case, npc, request = _setup("cook", "req-cook-timeout")
    set_mock_script("req-cook-timeout", SENTINEL_TIMEOUT)
    draft = generate_dialogue(request)
    assert draft.status == "timeout", f"draft.status={draft.status!r}"
    result = validate_dialogue(request, draft, case, npc)
    _assert_fallback(result, Reason.GEN_TIMEOUT)
    assert result.npc_id == "cook"


def test_TC_TIMEOUT_006_script_is_scoped_to_request_id(mock_cleanup):
    """Positive control: another request_id is unaffected and validates."""
    case, npc, request = _setup(request_id="req-unscripted")
    set_mock_script("req-timeout", SENTINEL_TIMEOUT)
    draft = generate_dialogue(request)
    assert draft.status == "ok", f"draft.status={draft.status!r}"
    result = validate_dialogue(request, draft, case, npc)
    assert Reason.OK in result.reasons, result.reasons
    assert result.used_fallback is False and result.valid is True


def test_TC_TIMEOUT_007_cleared_script_no_longer_times_out(mock_cleanup):
    """After clear_mock_scripts() the same request_id behaves normally."""
    case, npc, request = _setup()
    set_mock_script("req-timeout", SENTINEL_TIMEOUT)
    clear_mock_scripts()
    draft = generate_dialogue(request)
    assert draft.status == "ok", f"draft.status={draft.status!r}"
    result = validate_dialogue(request, draft, case, npc)
    assert Reason.OK in result.reasons, result.reasons
    assert result.used_fallback is False