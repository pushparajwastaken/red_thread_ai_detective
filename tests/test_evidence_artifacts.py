"""Independent verification that the committed evidence artifacts are well-formed, consistent with each other,
and NOT stale relative to the current source tree (outcomes are recomputed from scratch)."""
import csv
import dataclasses
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import pytest

from members.ananya.branching_baseline import answer_branching
from shared.contracts import BenchmarkRecord, TestRecord
from shared.fixture_case import make_case_001
from src.pipeline import interrogate, load_case
from tests.security_scenarios import SCENARIOS, expected, outcome, run_scenario
from tests.test_benchmark_questions import score_result

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = json.loads((ROOT / "test_cases" / "benchmark_questions.json").read_text(encoding="utf-8"))["questions"]
SEC = list(csv.DictReader((ROOT / "results" / "security_test_log.csv").open(encoding="utf-8")))
BEN = list(csv.DictReader((ROOT / "results" / "benchmark_results.csv").open(encoding="utf-8")))
REQUIRED = {"authorization", "spoiler", "unsupported_claim", "direct_injection", "indirect_injection",
            "malformed_output", "validator_failure", "timeout", "fallback", "e2e"}
WARM = 20


def header(path):
    return next(csv.reader(path.open(encoding="utf-8")))


# ------------------------------------------------------------------ security log
def test_security_log_header_is_testrecord_field_order():
    assert header(ROOT / "results" / "security_test_log.csv") == [f.name for f in dataclasses.fields(TestRecord)]


def test_security_log_covers_required_categories_and_all_rows_pass():
    assert REQUIRED <= {r["category"] for r in SEC}
    assert [r["test_id"] for r in SEC if r["passed"] != "True"] == []
    assert len({r["test_id"] for r in SEC}) == len(SEC)


def test_security_log_is_not_stale_and_matches_actual_execution():
    assert [r["test_id"] for r in SEC] == [s.test_id for s in SCENARIOS]
    for row, s in zip(SEC, SCENARIOS):
        res, _ = run_scenario(s)
        assert row["expected"] == expected(s), s.test_id
        assert row["actual"] == outcome(res), f"{s.test_id}: log is stale ({row['actual']} vs {outcome(res)})"
        assert row["model"] == "mock"


def test_security_log_records_known_residuals_explicitly():
    residual = [r for r in SEC if "KNOWN RESIDUAL" in r["details"] or "KNOWN FALSE POSITIVE" in r["details"]]
    assert {r["test_id"] for r in residual} >= {"UNSUP-10", "UNSUP-11", "IINJ-03"}


# ------------------------------------------------------------------ benchmark csv
def test_benchmark_header_is_benchmarkrecord_field_order():
    assert header(ROOT / "results" / "benchmark_results.csv") == [f.name for f in dataclasses.fields(BenchmarkRecord)]


def test_benchmark_row_counts_and_cold_warm_separation():
    per_mode = len(QUESTIONS) * (1 + WARM)
    for mode in ("dynamic", "branching"):
        rows = [r for r in BEN if r["mode"] == mode]
        assert len(rows) == per_mode
        runs = Counter(r["run_id"] for r in rows)
        cold = [k for k in runs if k.endswith(f"-{mode}-cold")]
        warm = [k for k in runs if re.search(rf"-{mode}-warm-\d\d$", k)]
        assert len(cold) == 1 and len(warm) == WARM
        assert runs[cold[0]] == len(QUESTIONS) and all(runs[w] == len(QUESTIONS) for w in warm)
        assert {r["question_id"] for r in rows} == {q["question_id"] for q in QUESTIONS}


def test_benchmark_unavailable_metrics_are_empty_never_fabricated():
    for r in BEN:
        assert r["ttft_ms"] == "" and r["cost_usd"] == "" and r["prompt_tokens"] == "" and r["completion_tokens"] == ""
        assert float(r["total_ms"]) > 0 and r["hardware"] and r["model"] in {"mock", "fixed-tree"}
    assert {r["model"] for r in BEN if r["mode"] == "dynamic"} == {"mock"}


def test_benchmark_outcomes_are_not_stale_and_match_a_fresh_recomputation():
    fresh = {}
    for q in QUESTIONS:
        case = load_case("case_001"); case.progression = q["progression"]
        d = interrogate(case, q["npc_id"], q["question"], presented_evidence_ids=q["presented_evidence_ids"])
        b = answer_branching(make_case_001(q["progression"]), q["npc_id"], q["question_id"],
                             presented_evidence_ids=q["presented_evidence_ids"])
        for mode, res in (("dynamic", d), ("branching", b)):
            sc = score_result(q, res)
            fresh[(mode, q["question_id"])] = (str(res.valid), str(res.used_fallback), ";".join(res.reasons),
                                               str(sc["answer_correct"]), str(sc["leaked_protected_fact"]))
    for r in BEN:
        got = (r["valid"], r["used_fallback"], r["reasons"], r["answer_correct"], r["leaked_protected_fact"])
        assert got == fresh[(r["mode"], r["question_id"])], (r["run_id"], r["question_id"])


# ------------------------------------------------------------------ report <-> csv consistency
def _p95(xs):
    s = sorted(xs)
    return s[max(0, math.ceil(0.95 * len(s)) - 1)]


def test_report_latency_table_matches_csv_recomputation():
    text = (ROOT / "docs" / "benchmark-report.md").read_text(encoding="utf-8")
    groups = defaultdict(list)
    for r in BEN:
        groups[(r["mode"], "cold" if r["run_id"].endswith("-cold") else "warm")].append(float(r["total_ms"]))
    for (mode, kind), xs in groups.items():
        row = re.search(rf"\| {mode} \| {kind} \| ([\d.]+) \| ([\d.]+) \| (\d+) \|", text)
        assert row, (mode, kind)
        assert float(row[1]) == pytest.approx(statistics.median(xs), abs=0.0006)
        assert float(row[2]) == pytest.approx(_p95(xs), abs=0.0006)
        assert int(row[3]) == len(xs)


def test_report_outcome_table_matches_csv_and_labels_mock_honestly():
    text = (ROOT / "docs" / "benchmark-report.md").read_text(encoding="utf-8")
    for mode in ("dynamic", "branching"):
        cold = [r for r in BEN if r["mode"] == mode and r["run_id"].endswith("-cold")]
        n = len(cold)
        row = re.search(rf"\| {mode} \| {n} \| (\d+)/{n} \| (\d+)/{n} \| (\d+)/{n} \| (\d+)/{n} \|", text)
        assert row, mode
        assert [int(x) for x in row.groups()] == [sum(r["answer_correct"] == "True" for r in cold),
                                                  sum(r["leaked_protected_fact"] == "True" for r in cold),
                                                  sum(r["used_fallback"] == "True" for r in cold),
                                                  sum(r["valid"] == "True" for r in cold)]
    assert "OFFLINE DETERMINISTIC MOCK" in text and "NOT a quality result" in text
    assert "not evaluated" in text.lower() and "unavailable" in text.lower()
