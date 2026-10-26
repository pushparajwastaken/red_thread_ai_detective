"""Malformed-output tests (TC_MALFORMED_*), fixture source: make_case_001().

Rules enforced:
 * Draft status != "ok" maps to GEN_TIMEOUT / GEN_ERROR / GEN_MALFORMED.
 * An unknown status or a draft with a bad shape -> Reason.SCHEMA_INVALID.
 * generate_dialogue (mock provider) never raises: scripted bad completions
   come back as non-ok drafts which the validator turns into fallbacks.
"""
import json

import pytest

from shared.contracts import (
    MAX_DIALOGUE_CHARS, DialogueDraft, DialogueRequest, Reason,
    SAFE_FALLBACK_TEXT, TurnMetrics,
)
from shared.fixture_case import make_case_001
from validator import validate_dialogue
from dialogue_generator import (
    generate_dialogue, set_mock_script, SENTINEL_TIMEOUT, SENTINEL_ERROR,
)
from conftest import make_npc_context


def _setup(**req_over):
    case = make_case_001()
    npc = make_npc_context(case, "gardener")
    kw = dict(
        npc_id="gardener", question="Where were you?",
        authorized_fact_ids=list(npc.authorized_fact_ids),
        permitted_evidence_ids=list(npc.permitted_evidence_ids),
        facts={f: case.canonical_facts[f] for f in npc.authorized_fact_ids},
        evidence=[case.evidence[e] for e in npc.permitted_evidence_ids])
    kw.update(req_over)
    return case, npc, DialogueRequest(**kw)


def _assert_fallback(result, reason):
    assert reason in result.reasons, f"expected {reason}, got {result.reasons}"
    assert result.used_fallback is True and result.valid is False
    assert result.text == SAFE_FALLBACK_TEXT
    assert result.cited_fact_ids == [] and result.cited_evidence_ids == []


@pytest.mark.parametrize("status,reason", [
    ("malformed", Reason.GEN_MALFORMED),
    ("timeout", Reason.GEN_TIMEOUT),
    ("error", Reason.GEN_ERROR),
])
def test_TC_MALFORMED_001_non_ok_status_maps_to_reason(status, reason):
    """Each non-ok generator status has its own reason code."""
    case, npc, request = _setup()
    draft = DialogueDraft(npc_id="gardener", status=status, error="boom")
    _assert_fallback(validate_dialogue(request, draft, case, npc), reason)


@pytest.mark.parametrize("over", [
    dict(status="weird"), dict(status=None), dict(text=123), dict(text=""),
    dict(text="   "), dict(text="x" * (MAX_DIALOGUE_CHARS + 1)),
    dict(cited_fact_ids=("F001",)), dict(cited_fact_ids=["F001", "F001"]),
    dict(cited_fact_ids=[1]), dict(cited_evidence_ids="E001"),
    dict(npc_id=""), dict(error=None), dict(metrics=None),
    dict(metrics=TurnMetrics(total_ms=-1.0)),
    dict(metrics=TurnMetrics(generation_ms=float("nan"))),
], ids=lambda o: "-".join(o))
def test_TC_MALFORMED_002_bad_draft_shape(over):
    """Any structurally invalid draft field -> SCHEMA_INVALID."""
    case, npc, request = _setup()
    draft = DialogueDraft(npc_id="gardener", text="I saw nothing.")
    for name, value in over.items():
        setattr(draft, name, value)
    _assert_fallback(validate_dialogue(request, draft, case, npc),
                     Reason.SCHEMA_INVALID)


def test_TC_MALFORMED_003_draft_not_a_dataclass():
    """A plain dict is not a DialogueDraft."""
    case, npc, request = _setup()
    result = validate_dialogue(request, {"text": "hi"}, case, npc)
    _assert_fallback(result, Reason.SCHEMA_INVALID)


def test_TC_MALFORMED_004_length_boundary():
    """Exactly MAX_DIALOGUE_CHARS is accepted (positive control)."""
    case, npc, request = _setup()
    draft = DialogueDraft(npc_id="gardener", text="x" * MAX_DIALOGUE_CHARS)
    result = validate_dialogue(request, draft, case, npc)
    assert Reason.OK in result.reasons and result.used_fallback is False


@pytest.mark.parametrize("script,status,reason", [
    ("this is not json", "malformed", Reason.GEN_MALFORMED),
    (json.dumps({"text": "hi"}), "malformed", Reason.GEN_MALFORMED),
    (json.dumps({"text": "hi", "cited_fact_ids": ["F004"],
                 "cited_evidence_ids": []}), "malformed", Reason.GEN_MALFORMED),
    (SENTINEL_TIMEOUT, "timeout", Reason.GEN_TIMEOUT),
    (SENTINEL_ERROR, "error", Reason.GEN_ERROR),
], ids=["not_json", "missing_field", "cites_absent_id", "timeout", "error"])
def test_TC_MALFORMED_005_generator_failures_become_fallback(
        mock_cleanup, monkeypatch, script, status, reason):
    """Mock generator failures never raise and validate to a fallback."""
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    case, npc, request = _setup(request_id="req-malformed")
    set_mock_script("req-malformed", script)
    draft = generate_dialogue(request)
    assert draft.status == status, f"draft.status={draft.status!r}"
    _assert_fallback(validate_dialogue(request, draft, case, npc), reason)


def test_TC_MALFORMED_006_default_mock_reply_is_valid(mock_cleanup, monkeypatch):
    """Positive control: unscripted mock output passes the validator."""
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    case, npc, request = _setup(request_id="req-default")
    result = validate_dialogue(request, generate_dialogue(request), case, npc)
    assert Reason.OK in result.reasons, result.reasons
    assert result.used_fallback is False and result.valid is True
