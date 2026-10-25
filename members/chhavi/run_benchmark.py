"""
Module 8: Benchmark runner
Developer: Chhavi Sharma

Mock mode tests the measurement and CSV workflow only.
Real mode calls an explicitly supplied integration function.
"""

import argparse
import importlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from shared.contracts import (
    DialogueResult,
    SAFE_FALLBACK_TEXT,
    TurnMetrics,
)
from shared.fixture_case import make_case_001
from members.chhavi.benchmark import (
    create_benchmark_record,
    save_results,
    summarize_results,
)


BASE_DIR = Path(__file__).resolve().parent


def mock_interrogate(
    case,
    npc_id,
    question,
    *,
    presented_evidence_ids=(),
):
    """Return a synthetic fallback to exercise the benchmark workflow."""
    start = perf_counter()

    metrics = TurnMetrics(
        mode="dynamic",
        model="MOCK-HARNESS-NO-LLM",
        ttft_ms=None,
        cost_usd=None,
    )

    result = DialogueResult(
        npc_id=npc_id,
        text=SAFE_FALLBACK_TEXT,
        cited_fact_ids=[],
        valid=False,
        used_fallback=True,
        latency_ms=0.0,
        reasons=["GEN_ERROR"],
        metrics=metrics,
    )

    elapsed = (perf_counter() - start) * 1000
    metrics.total_ms = elapsed
    result.latency_ms = elapsed
    return result


def load_target(target):
    """Load a callable specified as package.module:function."""
    module_name, separator, function_name = target.partition(":")

    if not separator:
        raise ValueError(
            "Target must use package.module:function format"
        )

    module = importlib.import_module(module_name)
    function = getattr(module, function_name)

    if not callable(function):
        raise ValueError("Target must be callable")

    return function


def main():
    parser = argparse.ArgumentParser(
        description="Run interrogation latency benchmarks."
    )
    backend = parser.add_mutually_exclusive_group(required=True)
    backend.add_argument("--mock", action="store_true")
    backend.add_argument("--target")
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument(
        "--hardware",
        required=True,
        help="Actual hardware description, for example Apple M2, 8 GB RAM",
    )
    args = parser.parse_args()

    if args.repeats < 1:
        parser.error("--repeats must be at least 1")

    questions_path = BASE_DIR / "benchmark_questions.json"
    questions = json.loads(
        questions_path.read_text(encoding="utf-8-sig")
    )

    if not isinstance(questions, list) or not questions:
        raise ValueError("Question file must contain a non-empty list")

    question_ids = set()

    for item in questions:
        for key in ("question_id", "npc_id", "question"):
            if not isinstance(item.get(key), str) or not item[key]:
                raise ValueError(f"Invalid question field: {key}")

        if item["question_id"] in question_ids:
            raise ValueError("Duplicate question_id")

        question_ids.add(item["question_id"])

        evidence_ids = item.get("presented_evidence_ids", [])
        if not isinstance(evidence_ids, list) or not all(
            isinstance(value, str) for value in evidence_ids
        ):
            raise ValueError("Invalid presented_evidence_ids")

    target = mock_interrogate if args.mock else load_target(args.target)
    label = "mock" if args.mock else "integration"
    run_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid4().hex[:8]
    )

    output_dir = BASE_DIR / "results" / f"{label}-{run_id}"
    output_dir.mkdir(parents=True, exist_ok=False)

    records = []
    external_timings = []

    for repeat in range(args.repeats):
        for item in questions:
            # Reset case state for every independent question/trial.
            case = make_case_001(progression=0)

            start = perf_counter()
            result = target(
                case,
                item["npc_id"],
                item["question"],
                presented_evidence_ids=item.get(
                    "presented_evidence_ids", []
                ),
            )
            external_ms = (perf_counter() - start) * 1000

            if not isinstance(result, DialogueResult):
                raise TypeError("Target must return DialogueResult")

            if result.metrics is None:
                raise ValueError("Target returned no TurnMetrics")

            if result.latency_ms != result.metrics.total_ms:
                raise ValueError(
                    "latency_ms must equal metrics.total_ms"
                )

            records.append(
                create_benchmark_record(
                    result,
                    run_id,
                    item["question_id"],
                    args.hardware,
                )
            )

            external_timings.append({
                "trial": repeat + 1,
                "question_id": item["question_id"],
                "external_call_ms": external_ms,
            })

            # Preserve completed rows after each successful call.
            save_results(
                records,
                output_dir / "benchmark_results.csv",
            )

    metadata = {
        "run_id": run_id,
        "backend": label,
        "target": args.target,
        "hardware": args.hardware,
        "os": platform.platform(),
        "python": platform.python_version(),
        "case_id": "case_001",
        "progression": 0,
        "repeats_per_question": args.repeats,
        "question_count": len(questions),
        "concurrency": 1,
        "conditions": "Uncontrolled startup; cold/warm not classified",
        "limitations": [
            "Mock mode uses synthetic fallbacks and no LLM.",
            "Mock generation/validation defaults are not measurements.",
            "Correctness and protected-fact leakage are not scored.",
            "Cold/warm protocol remains to be implemented.",
            "Question set is provisional.",
        ],
        "questions": questions,
        "external_timings": external_timings,
        "summaries": summarize_results(records),
    }

    (output_dir / "summary.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    print(f"Backend: {label}")
    print(f"Records saved: {len(records)}")
    print(f"Output: {output_dir}")

    if args.mock:
        print("MOCK ONLY: these are not real model benchmarks.")

    print(json.dumps(metadata["summaries"], indent=2))


if __name__ == "__main__":
    main()
