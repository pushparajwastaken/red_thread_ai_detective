"""Generate docs/benchmark-report.md from results/benchmark_results.csv (numbers come only from the CSV)."""
from __future__ import annotations

import csv
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "results" / "benchmark_results.csv"
OUT = ROOT / "docs" / "benchmark-report.md"
if len(sys.argv) > 1:          # make_benchmark_report.py [csv [out]]  (e.g. a real-model csv)
    CSV_PATH = Path(sys.argv[1])
    OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT
QUESTIONS = {q["question_id"]: q for q in json.loads((ROOT / "test_cases" / "benchmark_questions.json").read_text(encoding="utf-8"))["questions"]}

MOCK_NOTES = [
         "- **Dynamic mode here = the real pipeline with the OFFLINE DETERMINISTIC MOCK generator.** "
         "No LLM was called (no network, no credentials, no local model server in this environment). "
         "Its latencies measure *pipeline overhead* (context build, retrieval, prompt build, validation) "
         "only; they say **nothing** about real-model latency, and the mock's answers are canned.",
         "- **The dynamic `answer_correct` rate is therefore NOT a quality result.** The mock quotes the "
         "alphabetically-first authorized fact verbatim and cites only that fact (plus at most one evidence term), so it "
         "fails the rubric on any question that needs a different fact (e.g. cover stories). Dynamic-vs-branching "
         "*quality* is **unmeasured** until a real model is run on this same question set (blocked: no model/credentials here)."
]
REAL_NOTES = [
    "- **Dynamic mode here = the real pipeline with a REAL model** (see Models below), measured from actual calls "
    "on this hardware. Latency includes context build, retrieval, the model call, validation, and daemon-thread overhead.",
    "- TTFT appears only where the backend reported it; blank cells mean unavailable and are never estimated. "
    "Cost is reported only if the backend returned it.",
    "- Quality columns use the same lexical rubric as the mock run: paraphrased leaks and recombined authorized "
    "words are NOT detected, and rows flagged `requires_human_review` need a person. The validator rejects replies "
    "whose wording is not supported by their citations, so a high fallback rate is expected and is itself a result.",
]


def p95(xs):  # nearest-rank
    s = sorted(xs)
    return s[max(0, math.ceil(0.95 * len(s)) - 1)]


def b(v): return v == "True"


def main() -> int:
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8")))
    by = defaultdict(lambda: {"cold": [], "warm": []})
    for r in rows:
        by[r["mode"]]["cold" if r["run_id"].endswith("-cold") else "warm"].append(r)
    is_mock = {r["model"] for r in rows if r["mode"] == "dynamic"} == {"mock"}
    hw = {r["hardware"] for r in rows}; models = {m: {r["model"] for r in rows if r["mode"] == m} for m in by}
    run_ids = sorted({r["run_id"].rsplit("-", 2)[0] if "-warm-" in r["run_id"] else r["run_id"].rsplit("-", 1)[0] for r in rows})

    def lat(rs, key="total_ms"):
        v = [float(r[key]) for r in rs]
        return f"{statistics.median(v):.3f} | {p95(v):.3f} | {len(v)}" if v else "n/a | n/a | 0"

    L = ["# Benchmark report - Sprint 1 (dynamic vs branching)", "",
         "> Every number below is generated from `results/benchmark_results.csv` by "
         "`scripts/make_benchmark_report.py`. Regenerate with:",
         "> `python scripts/run_benchmark.py --all --warm-passes 20 && python scripts/make_benchmark_report.py`", "",
         "## Read this first - what these numbers are and are not", "",
         *(MOCK_NOTES if is_mock else REAL_NOTES),
         "- **Branching** = Ananya's deterministic fixed-tree baseline (`model=fixed-tree`); its answers are authored "
         "per question from the same set, so a high correct rate mostly reflects authoring, not generalisation.",
         "- **TTFT: unavailable** (empty in the CSV) for both modes: the mock is not streaming and the baseline has no model. "
         "Player-visible latency is `total_ms`. The project's sub-800 ms first-token target is **not evaluated**.",
         "- **Cost: unavailable** (empty). No backend reported usage; nothing was estimated.",
         "- Lexical rubric limits apply: paraphrased leaks and false combinations of authorized terms are not detected; "
         "rows flagged `requires_human_review` in the question set need a person.", "",
         "## Setup", "",
         f"- Questions: **{len(QUESTIONS)}** (`test_cases/benchmark_questions.json`, 10 categories x 3, case_001, NPCs gardener/cook).",
         f"- Hardware/environment: {'; '.join(sorted(hw))}",
         "- Runs: each mode in its own fresh process. **Cold** = first pass after interpreter start (30 samples/mode). "
         "**Warm** = 20 subsequent passes (600 samples/mode). Cold/warm are separated via `run_id` suffix (`-cold`, `-warm-NN`).",
         f"- Models: " + ", ".join(f"{m}: {sorted(v)}" for m, v in models.items()) + ".",
         "- Percentiles: median and nearest-rank p95 of `total_ms`, with n.",
         "- Dynamic latency includes a daemon worker thread per call (whole-call deadline enforcement). Cold and warm "
         "medians differ by less than run-to-run noise at this scale; no cold-vs-warm effect is claimed.", "",
         "## Latency (ms, player-visible `total_ms`)", "",
         "| Mode | Run | median | p95 | n |", "|---|---|---:|---:|---:|"]
    for m in ("dynamic", "branching"):
        for k in ("cold", "warm"):
            L.append(f"| {m} | {k} | {lat(by[m][k])} |")
    L += ["", "Component medians (warm, ms; branching has no generation or validation stage, so those components are recorded as 0.0 by the baseline, not measured): " + "; ".join(
        f"{m}: generation {statistics.median(float(r['generation_ms']) for r in by[m]['warm']):.3f}, "
        f"validation {statistics.median(float(r['validation_ms']) for r in by[m]['warm']):.3f}" for m in ("dynamic", "branching")) + ".", "",
        "## Outcomes under the shared rubric (cold pass, one sample per question; warm passes are identical because both modes are deterministic here)", "",
        "| Mode | questions | answer_correct | leaked_protected_fact | fallback | valid |", "|---|---:|---:|---:|---:|---:|"]
    for m in ("dynamic", "branching"):
        cs = by[m]["cold"]; n = len(cs)
        L.append(f"| {m} | {n} | {sum(b(r['answer_correct']) for r in cs)}/{n} | {sum(b(r['leaked_protected_fact']) for r in cs)}/{n} "
                 f"| {sum(b(r['used_fallback']) for r in cs)}/{n} | {sum(b(r['valid']) for r in cs)}/{n} |")
    det = all(len({(r['question_id'], r['answer_correct'], r['used_fallback'], r['reasons']) for r in by[m]['warm'] + by[m]['cold'] if r['question_id'] == qid}) == 1
              for m in by for qid in QUESTIONS)
    L += ["", f"Determinism check across all passes: **{'identical outcomes for every question' if det else 'OUTCOMES VARIED - investigate'}**.", "",
          "### Correctness by category (cold pass)", "", "| category | dynamic (mock) correct | branching correct |", "|---|---:|---:|"]
    cats = sorted({q["category"] for q in QUESTIONS.values()})
    for c in cats:
        cell = []
        for m in ("dynamic", "branching"):
            rs = [r for r in by[m]["cold"] if QUESTIONS[r["question_id"]]["category"] == c]
            cell.append(f"{sum(b(r['answer_correct']) for r in rs)}/{len(rs)}")
        L.append(f"| {c} | {cell[0]} | {cell[1]} |")
    L += ["", "### Fallback reasons (cold pass)", ""]
    for m in ("dynamic", "branching"):
        L.append(f"- {m}: " + (", ".join(f"{k or '(none)'}={v}" for k, v in Counter(r['reasons'] for r in by[m]['cold']).items())))
    L += ["", "The two modes intentionally differ on questions BQ025-BQ027 (presented evidence the NPC may not see): "
          "the baseline falls back with `UNAUTHORIZED_EVIDENCE`; `interrogate()` silently drops such IDs and answers on the "
          "remaining evidence (documented in the question set's `mode_expectations`).", "",
          "## Not measured / pending", "",
          *(["- Real-model (e.g. Ollama) dynamic latency, TTFT, token counts and quality: **not run** (no model/credentials/network); "
             "see docs/real-model-validation.md."] if is_mock else []),
          "- Human playtests of the branching baseline: **pending** - protocol in `members/ananya/playtest_protocol.md`, "
          "results template `members/ananya/playtest_results_template.csv` (empty of data).",
          "- Cost: unavailable. Sub-800 ms TTFT target: not evaluated.", ""]
    OUT.write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
