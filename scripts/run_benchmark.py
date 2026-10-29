"""Run the shared benchmark question set in BOTH modes and append real measurements.

    python scripts/run_benchmark.py --all --warm-passes 20      # rewrites results/benchmark_results.csv

Each mode runs in its OWN fresh subprocess so the cold pass is genuinely cold
(first calls after interpreter start). One BenchmarkRecord per question per pass.
Cold and warm are separated through ``run_id``: ``<base>-<mode>-cold`` and
``<base>-<mode>-warm-<NN>`` (the contract has no cold/warm column; none was added).

* dynamic  = the REAL pipeline. Default provider is the offline deterministic MOCK generator
             (model="mock"): that measures pipeline overhead only, NOT a quality signal and NOT an
             LLM latency. A REAL-MODEL run needs `--provider ollama [--model NAME]` and a running
             Ollama server (see docs/real-model-validation.md); it writes to a SEPARATE csv.
* branching = Ananya's fixed-tree baseline (model="fixed-tree").
Empty cell = metric unavailable (never estimated). cost_usd is empty unless a backend
reported it (the mock and local backends do not).
"""
from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "results" / "benchmark_results.csv"   # replaced by --out / provider default in main()
QPATH = ROOT / "test_cases" / "benchmark_questions.json"


def hardware() -> str:
    cpu = "unknown CPU"
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.lower().startswith("model name"):
                cpu = line.split(":", 1)[1].strip(); break
    except OSError:
        cpu = platform.processor() or cpu
    mem = ""
    try:
        kb = int(next(l for l in Path("/proc/meminfo").read_text().splitlines() if l.startswith("MemTotal")).split()[1])
        mem = f", {kb / 1048576:.1f} GiB RAM"
    except Exception:
        pass
    return f"{cpu}, {os.cpu_count()} vCPU{mem}, {platform.system()} {platform.release()}, Python {platform.python_version()}"


def _cell(v):
    return "" if v is None else v


def run_mode(mode: str, base: str, warm_passes: int, provider: str = "mock", model: str = "",
             timeout_s: float | None = None) -> list[dict]:
    os.environ["LLM_PROVIDER"] = provider
    if model:
        os.environ["LLM_MODEL"] = model
    from shared.contracts import BenchmarkRecord
    from tests.test_benchmark_questions import score_result
    questions = json.loads(QPATH.read_text(encoding="utf-8"))["questions"]
    hw = hardware()
    if mode == "dynamic":
        from src.pipeline import interrogate, load_case
        def call(q):
            case = load_case("case_001"); case.progression = q["progression"]
            kw = {} if timeout_s is None else {"timeout_s": timeout_s}
            return interrogate(case, q["npc_id"], q["question"], presented_evidence_ids=q["presented_evidence_ids"], **kw)
    else:
        from members.ananya.branching_baseline import answer_branching
        from shared.fixture_case import make_case_001
        def call(q):
            return answer_branching(make_case_001(q["progression"]), q["npc_id"], q["question_id"],
                                    presented_evidence_ids=q["presented_evidence_ids"])
    rows = []
    for pass_name in ["cold"] + [f"warm-{i:02d}" for i in range(1, warm_passes + 1)]:
        for q in questions:
            res = call(q)
            sc = score_result(q, res)
            m = res.metrics
            rec = BenchmarkRecord(
                run_id=f"{base}-{mode}-{pass_name}", mode=mode, model=m.model, hardware=hw,
                question_id=q["question_id"], npc_id=q["npc_id"], ttft_ms=m.ttft_ms,
                generation_ms=m.generation_ms, validation_ms=m.validation_ms, total_ms=m.total_ms,
                prompt_tokens=m.prompt_tokens, completion_tokens=m.completion_tokens, cost_usd=m.cost_usd,
                valid=res.valid, used_fallback=res.used_fallback, reasons=";".join(res.reasons),
                answer_correct=sc["answer_correct"], leaked_protected_fact=sc["leaked_protected_fact"])
            rows.append(dataclasses.asdict(rec))
    return rows


def write(rows: list[dict], append: bool) -> None:
    from shared.contracts import BenchmarkRecord
    fields = [f.name for f in dataclasses.fields(BenchmarkRecord)]
    new = not (append and OUT.exists() and OUT.stat().st_size)
    with OUT.open("a" if append else "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        if new:
            w.writerow(fields)
        for r in rows:
            w.writerow([_cell(r[f]) for f in fields])


def main() -> int:
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dynamic", "branching"])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--warm-passes", type=int, default=20)
    ap.add_argument("--base", default=None)
    ap.add_argument("--append", action="store_true")
    ap.add_argument("--provider", choices=["mock", "ollama"], default="mock")
    ap.add_argument("--model", default="", help="LLM_MODEL for the ollama provider")
    ap.add_argument("--timeout-s", type=float, default=None, help="whole-call deadline per question (dynamic)")
    ap.add_argument("--out", default=None, help="csv path (default: results/benchmark_results.csv for mock, "
                                                "results/benchmark_results_<provider>.csv otherwise)")
    a = ap.parse_args()
    OUT = Path(a.out) if a.out else ROOT / "results" / ("benchmark_results.csv" if a.provider == "mock"
                                                       else f"benchmark_results_{a.provider}.csv")
    base = a.base or "sprint1-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if a.all:
        OUT.write_text("", encoding="utf-8")
        for mode in ("dynamic", "branching"):
            cmd = [sys.executable, __file__, "--mode", mode, "--base", base, "--append", "--out", str(OUT),
                   "--warm-passes", str(a.warm_passes), "--provider", a.provider]
            if a.model:
                cmd += ["--model", a.model]
            if a.timeout_s is not None:
                cmd += ["--timeout-s", str(a.timeout_s)]
            subprocess.run(cmd, check=True, cwd=ROOT)
        return 0
    if not a.mode:
        ap.error("--mode or --all required")
    rows = run_mode(a.mode, base, a.warm_passes, a.provider, a.model, a.timeout_s)
    write(rows, a.append)
    print(f"{a.mode}: wrote {len(rows)} rows ({OUT})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
