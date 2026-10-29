"""Timeout / failure-path robustness for the REAL pipeline, driven by controlled blocking stages.

A Python thread cannot be force-killed, so these tests assert what CAN be guaranteed: the caller gets the
contract fallback within the deadline, stuck workers are bounded and never block process exit, late results are
discarded, and trusted state is untouched. Cooperative cancellation (a generator honouring request.timeout_s)
remains the generator's job.
"""
from __future__ import annotations

import copy
import subprocess
import sys
import textwrap
import threading
import time
from dataclasses import replace
from pathlib import Path

import pytest

from members.anshul import dialogue_generator as dg
from shared.contracts import SAFE_FALLBACK_TEXT, DialogueDraft, DialogueResult, Reason
from src.pipeline import interrogate_with_trace, load_case, real_deps

ROOT = Path(__file__).resolve().parents[1]
TIMEOUT = 0.3
SLACK = 0.35          # scheduling slack allowed on top of the deadline (seconds)


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setenv(dg.ENV_PROVIDER, "mock")
    dg.clear_mock_scripts()


def blocked(release: threading.Event, hold_s: float = 30.0):
    def fn(*a, **k):
        release.wait(hold_s)
        raise RuntimeError("released late")
    return fn


def worker_threads():
    return [t for t in threading.enumerate() if t.name.startswith("redthread-")]


def call(deps, timeout=TIMEOUT, case=None):
    case = case or load_case("case_001")
    t = time.perf_counter()
    res, trace = interrogate_with_trace(case, "gardener", "What did you see?", timeout_s=timeout, deps=deps)
    return res, trace, time.perf_counter() - t, case


def assert_fallback(res, reason, elapsed, timeout=TIMEOUT):
    assert isinstance(res, DialogueResult)
    assert res.used_fallback and res.text == SAFE_FALLBACK_TEXT and res.reasons == [reason]
    assert elapsed < timeout + SLACK, f"caller blocked {elapsed:.2f}s for a {timeout}s deadline"
    assert res.latency_ms == res.metrics.total_ms < (timeout + SLACK) * 1000


def test_blocking_generator_returns_gen_timeout_within_deadline():
    rel = threading.Event()
    try:
        res, trace, elapsed, _ = call(replace(real_deps(), generate_dialogue=blocked(rel)))
        assert_fallback(res, Reason.GEN_TIMEOUT, elapsed)
        assert trace.timed_out
        assert res.metrics.total_ms >= TIMEOUT * 1000 * 0.9           # whole-call duration, not a stub 0
    finally:
        rel.set()


@pytest.mark.parametrize("stage,reason", [
    ("validate_dialogue", Reason.VALIDATOR_ERROR),
    ("retrieve_evidence", Reason.SETUP_ERROR),
    ("build_npc_context", Reason.SETUP_ERROR),
])
def test_hung_non_generation_stage_is_bounded_by_the_whole_call_deadline(stage, reason):
    rel = threading.Event()
    try:
        res, _, elapsed, _ = call(replace(real_deps(), **{stage: blocked(rel)}))
        assert_fallback(res, reason, elapsed)
    finally:
        rel.set()


def test_repeated_timeouts_do_not_accumulate_unbounded_threads():
    rel = threading.Event()
    deps = replace(real_deps(), generate_dialogue=blocked(rel))
    end = time.time() + 5                       # let threads abandoned by earlier tests finish first
    while time.time() < end and worker_threads():
        time.sleep(0.05)
    base = len(worker_threads())
    assert base == 0, "another test left stuck workers behind"
    try:
        started = time.perf_counter()
        results = [call(deps, timeout=0.05)[0] for _ in range(40)]
        assert all(r.used_fallback and r.reasons == [Reason.GEN_TIMEOUT] for r in results)
        assert len(worker_threads()) - base <= 12, "stuck workers must be capped"
        assert time.perf_counter() - started < 6        # refusals are immediate once the cap is hit
    finally:
        rel.set()
    deadline = time.time() + 3
    while time.time() < deadline and len(worker_threads()) > base:
        time.sleep(0.05)
    assert len(worker_threads()) == base, "workers must drain once the stuck stage returns"
    ok, *_ = call(real_deps(), timeout=5)               # pipeline recovers after the stuck work ends
    assert ok.valid and not ok.used_fallback


def test_late_completion_is_discarded_and_cannot_mutate_state_or_trace():
    case = load_case("case_001")
    before = copy.deepcopy(case)

    def slow_ok(req):
        time.sleep(0.6)
        return DialogueDraft(npc_id=req.npc_id, text="I saw a figure near the greenhouse at nine o'clock.",
                             cited_fact_ids=["F001"], cited_evidence_ids=[], status="ok")
    res, trace, elapsed, _ = call(replace(real_deps(), generate_dialogue=slow_ok), case=case)
    assert_fallback(res, Reason.GEN_TIMEOUT, elapsed)
    snap_trace, snap_res = copy.deepcopy(trace), copy.deepcopy(res)
    time.sleep(0.9)                                     # the abandoned worker finishes now
    assert case == before
    assert trace == snap_trace and res == snap_res


def test_stuck_worker_does_not_block_interpreter_exit():
    script = textwrap.dedent(f"""
        import os, sys, threading
        os.environ["LLM_PROVIDER"] = "mock"
        sys.path.insert(0, {str(ROOT)!r})
        from dataclasses import replace
        from src.pipeline import interrogate_with_trace, load_case, real_deps
        never = threading.Event()
        deps = replace(real_deps(), generate_dialogue=lambda r: never.wait(60))
        res, _ = interrogate_with_trace(load_case("case_001"), "gardener", "hi", timeout_s=0.2, deps=deps)
        print(res.reasons)
    """)
    t = time.perf_counter()
    out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=40)
    elapsed = time.perf_counter() - t
    assert out.returncode == 0 and "GEN_TIMEOUT" in out.stdout, out.stderr
    assert elapsed < 10, f"interpreter exit blocked by a stuck worker for {elapsed:.0f}s"


# ---- every failure path independently, via controlled faults -----------------------------------------
def _boom(*a, **k):
    raise RuntimeError("boom")


@pytest.mark.parametrize("name,deps_kwargs,reason", [
    ("setup-npc-builder-raises", {"build_npc_context": _boom}, Reason.SETUP_ERROR),
    ("setup-retrieval-raises", {"retrieve_evidence": _boom}, Reason.SETUP_ERROR),
    ("generator-raises", {"generate_dialogue": _boom}, Reason.GEN_ERROR),
    ("validator-raises", {"validate_dialogue": _boom}, Reason.VALIDATOR_ERROR),
    ("validator-returns-garbage", {"validate_dialogue": lambda *a: "not a result"}, Reason.VALIDATOR_ERROR),
    ("npc-builder-returns-garbage", {"build_npc_context": lambda *a: None}, Reason.SETUP_ERROR),
])
def test_each_failure_path_yields_its_own_contract_reason(name, deps_kwargs, reason):
    res, _, elapsed, case = call(replace(real_deps(), **deps_kwargs), timeout=5)
    assert res.used_fallback and res.text == SAFE_FALLBACK_TEXT and res.reasons == [reason], name
    assert case == load_case("case_001")


def test_malformed_generator_output_is_rejected_by_the_validator():
    res, *_ = call(replace(real_deps(), generate_dialogue=lambda r: {"text": "dict, not a draft"}), timeout=5)
    assert res.used_fallback and res.reasons == [Reason.SCHEMA_INVALID]


def test_fallback_maker_failure_still_returns_a_safe_result():
    deps = replace(real_deps(), generate_dialogue=_boom, make_fallback=_boom)
    res, *_ = call(deps, timeout=5)
    assert isinstance(res, DialogueResult) and res.used_fallback and res.text == SAFE_FALLBACK_TEXT
