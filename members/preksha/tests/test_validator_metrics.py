"""Metrics tests (TC_METRICS_*), fixture source: make_case_001().

Rules enforced (validator + DialogueResult contract):
 * validate_dialogue copies a well-formed draft.metrics into result.metrics
   (never aliasing the model-owned object) and measures validation_ms.
 * result.latency_ms == result.metrics.total_ms whenever metrics exist.
 * Malformed or absent telemetry is dropped: metrics None, latency_ms 0.0.
"""
import math

import pytest

from shared.contracts import (
    DialogueDraft, DialogueRequest, Reason, TurnMetrics,
)
from shared.fixture_case import make_case_001
from validator import validate_dialogue
from conftest import make_npc_context


def _validate(draft, npc_id="gardener"):
    case = make_case_001()
    npc = make_npc_context(case, npc_id)
    request = DialogueRequest(
        npc_id=npc_id, question="Where were you?",
        authorized_fact_ids=list(npc.authorized_fact_ids),
        permitted_evidence_ids=list(npc.permitted_evidence_ids),
        facts={f: case.canonical_facts[f] for f in npc.authorized_fact_ids},
        evidence=[case.evidence[e] for e in npc.permitted_evidence_ids])
    return validate_dialogue(request, draft, case, npc)


def _draft(**over):
    kw = dict(npc_id="gardener", text="I saw nothing.")
    kw.update(over)
    return DialogueDraft(**kw)


def test_TC_METRICS_001_accepted_result_carries_metrics():
    """A valid draft with default metrics -> result.metrics is a TurnMetrics."""
    result = _validate(_draft())
    assert Reason.OK in result.reasons, result.reasons
    assert result.used_fallback is False and result.valid is True
    assert isinstance(result.metrics, TurnMetrics), f"got {result.metrics!r}"


def test_TC_METRICS_002_latency_equals_total_ms():
    """latency_ms must equal metrics.total_ms when metrics exist."""
    draft = _draft(metrics=TurnMetrics(model="mock", total_ms=7.5))
    result = _validate(draft)
    assert result.metrics is not None
    assert result.latency_ms == result.metrics.total_ms == 7.5


def test_TC_METRICS_003_validation_ms_is_measured():
    """validation_ms is filled in by the validator and is > 0."""
    result = _validate(_draft())
    assert result.metrics.validation_ms > 0, result.metrics.validation_ms
    assert math.isfinite(result.metrics.validation_ms)


def test_TC_METRICS_004_metrics_are_copied_not_aliased():
    """result.metrics is a copy: the model-owned draft.metrics is untouched."""
    metrics = TurnMetrics(model="mock", generation_ms=5.0)
    result = _validate(_draft(metrics=metrics))
    assert result.metrics is not metrics, "result must not alias draft.metrics"
    assert metrics.validation_ms == 0.0, "validator must not mutate the draft"
    assert result.metrics.generation_ms == 5.0, "generation_ms must be kept"
    assert result.metrics.model == "mock"


def test_TC_METRICS_005_fallback_keeps_metrics_and_latency():
    """A spoiler fallback still reports metrics, latency and validation_ms."""
    draft = _draft(cited_fact_ids=["F004"],
                   metrics=TurnMetrics(total_ms=3.25))
    result = _validate(draft)
    assert Reason.UNAUTHORIZED_FACT in result.reasons, result.reasons
    assert result.used_fallback is True and result.valid is False
    assert result.cited_fact_ids == [] and result.cited_evidence_ids == []
    assert result.metrics is not None
    assert result.latency_ms == result.metrics.total_ms == 3.25
    assert result.metrics.validation_ms > 0


def test_TC_METRICS_006_non_ok_draft_still_reports_validation_ms():
    """A timeout draft's fallback also measures validation_ms."""
    result = _validate(_draft(status="timeout", text="", error="slow"))
    assert Reason.GEN_TIMEOUT in result.reasons, result.reasons
    assert result.used_fallback is True
    assert result.metrics is not None
    assert result.metrics.validation_ms > 0


@pytest.mark.parametrize("bad", [
    TurnMetrics(total_ms=-1.0), TurnMetrics(generation_ms=float("nan")),
    TurnMetrics(mode="weird"), "fast", None,
], ids=["negative", "nan", "bad_mode", "string", "none"])
def test_TC_METRICS_007_malformed_metrics_are_dropped(bad):
    """Bad telemetry -> SCHEMA_INVALID fallback with metrics None, latency 0."""
    result = _validate(_draft(metrics=bad))
    assert Reason.SCHEMA_INVALID in result.reasons, result.reasons
    assert result.used_fallback is True
    assert result.metrics is None, f"metrics leaked through: {result.metrics!r}"
    assert result.latency_ms == 0.0


def test_TC_METRICS_008_non_draft_has_explicit_none_metrics():
    """A draft that is not a DialogueDraft yields metrics None, latency 0.0."""
    result = _validate({"text": "I saw nothing."})
    assert Reason.SCHEMA_INVALID in result.reasons, result.reasons
    assert result.used_fallback is True
    assert result.metrics is None
    assert result.latency_ms == 0.0
