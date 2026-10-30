"""Fail-closed tests (TC_FAILCLOSED_*), fixture source: make_case_001().

Rules enforced:
 * validate_dialogue NEVER raises, whatever garbage it receives for the
   draft, request, case or NPC context.
 * Every garbage call returns a DialogueResult with used_fallback True,
   valid False, SAFE_FALLBACK_TEXT and no citations, plus a reason code.
 * Garbage in trusted objects -> SETUP_ERROR; garbage in request or draft
   -> SCHEMA_INVALID; an internal crash -> VALIDATOR_ERROR.
"""
import pytest

import validator
from shared.contracts import (
    DialogueDraft, DialogueRequest, DialogueResult, Reason, SAFE_FALLBACK_TEXT,
)
from shared.fixture_case import make_case_001
from validator import validate_dialogue
from conftest import make_npc_context


def _build():
    case = make_case_001()
    npc = make_npc_context(case, "gardener")
    request = DialogueRequest(
        npc_id="gardener", question="Where were you?",
        authorized_fact_ids=list(npc.authorized_fact_ids),
        permitted_evidence_ids=list(npc.permitted_evidence_ids),
        facts={f: case.canonical_facts[f] for f in npc.authorized_fact_ids},
        evidence=[case.evidence[e] for e in npc.permitted_evidence_ids])
    draft = DialogueDraft(npc_id="gardener", text="I saw nothing.")
    return case, npc, request, draft


def _assert_failclosed(result, reason):
    assert isinstance(result, DialogueResult), f"got {type(result)}"
    assert reason in result.reasons, f"expected {reason}, got {result.reasons}"
    assert result.used_fallback is True and result.valid is False
    assert result.text == SAFE_FALLBACK_TEXT
    assert result.cited_fact_ids == [] and result.cited_evidence_ids == []
    assert result.latency_ms >= 0


@pytest.mark.parametrize("garbage", [
    None, {"text": "hi"}, "I saw nothing.", 42, [], object(),
], ids=["none", "dict", "str", "int", "list", "object"])
def test_TC_FAILCLOSED_001_garbage_draft_object(garbage):
    """A draft that is not a DialogueDraft -> SCHEMA_INVALID, no raise."""
    case, npc, request, _ = _build()
    _assert_failclosed(validate_dialogue(request, garbage, case, npc),
                       Reason.SCHEMA_INVALID)


@pytest.mark.parametrize("field,value", [
    ("text", ""), ("text", "   "), ("text", None), ("text", 123),
    ("text", ["I saw nothing."]), ("text", b"I saw nothing."),
    ("cited_fact_ids", None), ("cited_fact_ids", "F001"),
    ("cited_fact_ids", ("F001",)), ("cited_fact_ids", {"F001": 1}),
    ("cited_fact_ids", [None]), ("cited_fact_ids", ["F001", "F001"]),
    ("cited_evidence_ids", None), ("cited_evidence_ids", "E001"),
    ("cited_evidence_ids", [["E001"]]), ("cited_evidence_ids", [""]),
    ("npc_id", None), ("npc_id", ""), ("npc_id", 5),
    ("status", None), ("status", 0), ("status", "weird"),
    ("error", None), ("metrics", None), ("metrics", "fast"),
])
def test_TC_FAILCLOSED_002_malformed_draft_fields(field, value):
    """Wrong types / empty text / non-list citations -> SCHEMA_INVALID."""
    case, npc, request, draft = _build()
    setattr(draft, field, value)
    _assert_failclosed(validate_dialogue(request, draft, case, npc),
                       Reason.SCHEMA_INVALID)


@pytest.mark.parametrize("garbage", [None, {}, "req", 7, object()],
                         ids=["none", "dict", "str", "int", "object"])
def test_TC_FAILCLOSED_003_garbage_request(garbage):
    """A request that is not a DialogueRequest -> SCHEMA_INVALID."""
    case, npc, _, draft = _build()
    _assert_failclosed(validate_dialogue(garbage, draft, case, npc),
                       Reason.SCHEMA_INVALID)


@pytest.mark.parametrize("garbage", [None, {}, "case", object()],
                         ids=["none", "dict", "str", "object"])
def test_TC_FAILCLOSED_004_garbage_case_or_npc(garbage):
    """Untrusted-shape case or NPC context -> SETUP_ERROR."""
    case, npc, request, draft = _build()
    _assert_failclosed(validate_dialogue(request, draft, garbage, npc),
                       Reason.SETUP_ERROR)
    _assert_failclosed(validate_dialogue(request, draft, case, garbage),
                       Reason.SETUP_ERROR)


@pytest.mark.parametrize("field,value", [
    ("progression", "0"), ("progression", -1), ("canonical_facts", None),
    ("evidence", None), ("npc_grants", []),
])
def test_TC_FAILCLOSED_005_corrupt_case_field(field, value):
    """A CaseState mutated into a bad shape -> SETUP_ERROR."""
    case, npc, request, draft = _build()
    setattr(case, field, value)
    _assert_failclosed(validate_dialogue(request, draft, case, npc),
                       Reason.SETUP_ERROR)


@pytest.mark.parametrize("value", [None, "F001", ["F001", "F001"], [1]])
def test_TC_FAILCLOSED_006_corrupt_npc_fact_list(value):
    """An NPCContext with a malformed fact list -> SETUP_ERROR."""
    case, npc, request, draft = _build()
    npc.authorized_fact_ids = value
    _assert_failclosed(validate_dialogue(request, draft, case, npc),
                       Reason.SETUP_ERROR)


def test_TC_FAILCLOSED_007_everything_garbage_still_returns():
    """All four arguments None: still a fallback, never an exception."""
    result = validate_dialogue(None, None, None, None)
    _assert_failclosed(result, Reason.SETUP_ERROR)
    assert result.npc_id == ""


def test_TC_FAILCLOSED_008_internal_crash_gives_validator_error(monkeypatch):
    """If the checker itself raises, the result is VALIDATOR_ERROR."""
    case, npc, request, draft = _build()

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated validator crash")

    monkeypatch.setattr(validator, "_check", _boom)
    _assert_failclosed(validate_dialogue(request, draft, case, npc),
                       Reason.VALIDATOR_ERROR)


def test_TC_FAILCLOSED_009_valid_inputs_still_pass():
    """Positive control: clean inputs are accepted, not failed closed."""
    case, npc, request, draft = _build()
    result = validate_dialogue(request, draft, case, npc)
    assert Reason.OK in result.reasons, result.reasons
    assert result.used_fallback is False and result.valid is True