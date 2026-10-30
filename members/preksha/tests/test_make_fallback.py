"""make_fallback tests (TC_FALLBACK_*): validator.make_fallback() directly.

Rules enforced:
 * make_fallback ALWAYS returns a DialogueResult with the constant
   SAFE_FALLBACK_TEXT, valid False, used_fallback True, no citations.
 * Reason codes are sanitised: unknown / non-string codes and Reason.OK
   become VALIDATOR_ERROR; duplicates collapse; an empty list gets
   VALIDATOR_ERROR.
 * Bad arguments (npc_id, reasons, metrics) never raise.
Uses no fixture or case data.
"""
import pytest

from shared.contracts import (
    DialogueResult, Reason, SAFE_FALLBACK_TEXT, TurnMetrics,
)
from validator import make_fallback

ALL_CODES = sorted(
    v for k, v in vars(Reason).items()
    if k.isupper() and type(v) is str and v != Reason.OK
)


def _assert_fallback(result):
    assert isinstance(result, DialogueResult)
    assert result.text == SAFE_FALLBACK_TEXT
    assert result.valid is False
    assert result.used_fallback is True
    assert result.cited_fact_ids == []
    assert result.cited_evidence_ids == []
    assert result.latency_ms >= 0, f"latency_ms={result.latency_ms}"


def test_TC_FALLBACK_001_basic_contract():
    """Baseline: constant text, no citations, valid False, fallback True."""
    result = make_fallback("gardener", [Reason.SCHEMA_INVALID])
    _assert_fallback(result)
    assert result.npc_id == "gardener"
    assert Reason.SCHEMA_INVALID in result.reasons, result.reasons


@pytest.mark.parametrize("code", ALL_CODES)
def test_TC_FALLBACK_002_every_real_reason_is_preserved(code):
    """Each real Reason code (except OK) survives sanitising unchanged."""
    result = make_fallback("cook", [code])
    _assert_fallback(result)
    assert result.reasons == [code], f"expected [{code}], got {result.reasons}"


def test_TC_FALLBACK_003_multiple_reasons_keep_order_and_dedupe():
    """Several codes are kept in order with duplicates removed."""
    result = make_fallback(
        "gardener",
        [Reason.UNAUTHORIZED_FACT, Reason.PROTECTED_TERM_LEAK,
         Reason.UNAUTHORIZED_FACT])
    _assert_fallback(result)
    assert result.reasons == [Reason.UNAUTHORIZED_FACT,
                              Reason.PROTECTED_TERM_LEAK]


@pytest.mark.parametrize("bad", ["NOT_A_REASON", "", None, 7, Reason.OK],
                         ids=["unknown", "empty", "none", "int", "ok_code"])
def test_TC_FALLBACK_004_bad_reason_becomes_validator_error(bad):
    """Unknown, non-string, or OK codes are replaced by VALIDATOR_ERROR."""
    result = make_fallback("gardener", [bad])
    _assert_fallback(result)
    assert Reason.VALIDATOR_ERROR in result.reasons, result.reasons
    assert Reason.OK not in result.reasons, "a fallback must never say OK"


@pytest.mark.parametrize("bad", [[], None, "GEN_TIMEOUT", ("GEN_TIMEOUT",)],
                         ids=["empty_list", "none", "str", "tuple"])
def test_TC_FALLBACK_005_bad_reasons_container(bad):
    """An empty or non-list reasons argument yields VALIDATOR_ERROR."""
    result = make_fallback("gardener", bad)
    _assert_fallback(result)
    assert Reason.VALIDATOR_ERROR in result.reasons, result.reasons


@pytest.mark.parametrize("bad_id", [None, 123, ["cook"], b"cook"],
                         ids=["none", "int", "list", "bytes"])
def test_TC_FALLBACK_006_non_string_npc_id_becomes_empty(bad_id):
    """A non-string npc_id is replaced by '' and does not raise."""
    result = make_fallback(bad_id, [Reason.NPC_MISMATCH])
    _assert_fallback(result)
    assert result.npc_id == ""


def test_TC_FALLBACK_007_without_metrics_latency_is_zero():
    """No metrics -> metrics None and latency_ms == 0.0."""
    result = make_fallback("gardener", [Reason.GEN_TIMEOUT])
    _assert_fallback(result)
    assert result.metrics is None
    assert result.latency_ms == 0.0


def test_TC_FALLBACK_008_valid_metrics_set_latency_and_are_copied():
    """Valid metrics set latency_ms = total_ms and are NOT aliased."""
    metrics = TurnMetrics(total_ms=12.5)
    result = make_fallback("gardener", [Reason.GEN_TIMEOUT], metrics)
    _assert_fallback(result)
    assert result.latency_ms == 12.5
    assert result.metrics is not metrics, "result must hold a copy"
    metrics.total_ms = 99.0
    assert result.metrics.total_ms == 12.5, "later edits must not leak in"


@pytest.mark.parametrize("bad", [
    TurnMetrics(total_ms=-1.0), TurnMetrics(generation_ms=float("nan")),
    TurnMetrics(mode="weird"), "not metrics", {"total_ms": 1.0},
], ids=["negative", "nan", "bad_mode", "string", "dict"])
def test_TC_FALLBACK_009_malformed_metrics_are_dropped(bad):
    """Malformed telemetry is discarded: metrics None, latency 0.0."""
    result = make_fallback("gardener", [Reason.GEN_ERROR], bad)
    _assert_fallback(result)
    assert result.metrics is None
    assert result.latency_ms == 0.0