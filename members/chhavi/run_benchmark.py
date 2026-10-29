"""
Module 8: Benchmark runner
Developer: Chhavi Sharma

Separate cold and warm trial groups.
Mock results test the workflow only, not model performance.
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
    case, npc_id, question, *, presented_evidence_ids=()
):
    """Synthetic fallback; no model or validator is exercised."""
    start = perf_counter()

    result = DialogueResult(
        npc_id=npc_id,
        text=SAFE_FALLBACK_TEXT,
        cited_fact_ids=[],
        valid=False,
        used_fallback=True,
        latency_ms=0.0,
        reasons=["GEN_ERROR"],
        metrics=TurnMetrics(
            mode="dynamic",
            model="MOCK-HARNESS-NO-LLM",
        ),
    )

    elapsed = (perf_counter() - start) * 1000
    result.metrics.total_ms = elapsed
    result.latency_ms = elapsed
    return result


def load_target(spec):
    """Load package.module:function."""
    module_name, separator, function_name = spec.partition(":")

    if not separator or not module_name or not function_name:
        raise ValueError("Use package.module:function format")

    function = getattr(
        importlib.import_module(module_name), function_name
    )

    if not callable(function):
        raise TypeError("Target must be callable")

    return function

def load_questions():
    path = (
        BASE_DIR.parents[1]
        / "test_cases"
        / "benchmark_questions.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8-sig"))

    questions = (
        payload.get("questions")
        if isinstance(payload, dict)
        else payload
    )

    if not isinstance(questions, list) or not questions:
        raise ValueError("Questions must be a non-empty list")

    seen = set()

    for item in questions:
        if not isinstance(item, dict):
            raise ValueError("Each question must be an object")

        for key in ("question_id", "npc_id", "question"):
            if not isinstance(item.get(key), str) or not item[key]:
                raise ValueError(f"Invalid field: {key}")

        if item["question_id"] in seen:
            raise ValueError("Duplicate question_id")

        seen.add(item["question_id"])

        progression = item.get("progression", 0)
        if type(progression) is not int or progression < 0:
            raise ValueError("Invalid progression")

        evidence = item.get("presented_evidence_ids", [])
        if not isinstance(evidence, list) or not all(
            isinstance(value, str) for value in evidence
        ):
            raise ValueError("Invalid presented_evidence_ids")

    return questions




def call_target(target, item):
    # Fresh case prevents one trial from advancing another's state.
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
        raise ValueError("latency_ms must equal metrics.total_ms")

    return result, external_ms


def run_group(condition, target, reset, questions, args, root):
    folder = root / condition
    folder.mkdir()
    records = []
    timings = []
    failures = []

    metadata = {
        "run_id": root.name,
        "condition": condition,
        "backend": "mock" if args.mock else "integration",
        "target": args.target,
        "reset_hook": args.reset_hook,
        "reset_description": args.reset_description,
        "configuration": args.configuration,
        "hardware": args.hardware,
        "os": platform.platform(),
        "python": platform.python_version(),
        "case_id": "case_001",
        "progression": 0,
        "repeats_per_question": args.repeats,
        "concurrency": 1,
        "questions": questions,
        "external_timings": timings,
        "failures": failures,
        "limitations": [
            "Mock cold/warm labels are workflow groups only.",
            "Mock stage defaults are not measured durations.",
            "Correctness and leakage remain unscored.",
            "Reset-hook behavior requires integration-lead review.",
            "Reset duration is excluded from request latency.",
            "Cold inference includes model loading only if target loads lazily.",
            "Warmups may incur backend usage; cost totals exclude warmups.",
            "Question set is provisional.",
        ],
    }

    def checkpoint():
        metadata["completed_records"] = len(records)
        metadata["summaries"] = summarize_results(records)
        save_results(records, folder / "benchmark_results.csv")
        (folder / "summary.json").write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8",
        )

    checkpoint()

    for repeat in range(args.repeats):
        for item in questions:
            stage = "reset"

            try:
                if reset is not None:
                    # Hook takes no arguments and must finish synchronously.
                    reset()

                if condition == "warm":
                    stage = "warmup"
                    # Each warm sample follows its own warmup sequence.
                    for _ in range(args.warmup):
                        call_target(target, item)

                stage = "measurement"
                result, external_ms = call_target(target, item)

                records.append(
                    create_benchmark_record(
                        result,
                        root.name + "-" + condition,
                        item["question_id"],
                        args.hardware,
                    )
                )
                timings.append({
                    "trial": repeat + 1,
                    "question_id": item["question_id"],
                    "external_call_ms": external_ms,
                })

            except Exception as error:
                failures.append({
                    "trial": repeat + 1,
                    "question_id": item["question_id"],
                    "stage": stage,
                    "error_type": type(error).__name__,
                })
                checkpoint()
                raise

            checkpoint()

    print(f"{condition}: {len(records)} records")
    print(json.dumps(metadata["summaries"], indent=2))


def main():
    parser = argparse.ArgumentParser()
    backend = parser.add_mutually_exclusive_group(required=True)
    backend.add_argument("--mock", action="store_true")
    backend.add_argument("--target")
    parser.add_argument("--hardware", required=True)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--reset-hook")
    parser.add_argument("--reset-description")
    parser.add_argument("--configuration")
    args = parser.parse_args()

    if args.repeats < 1 or args.warmup < 1:
        parser.error("--repeats and --warmup must be positive")

    if args.mock and args.reset_hook:
        parser.error("--reset-hook is for real integration only")

    if not args.mock and not all([
        args.reset_hook,
        args.reset_description,
        args.configuration,
    ]):
        parser.error(
            "Real mode requires --reset-hook, "
            "--reset-description and --configuration"
        )

    questions = load_questions()
    target = mock_interrogate if args.mock else load_target(args.target)
    reset = None if args.mock else load_target(args.reset_hook)

    run_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-" + uuid4().hex[:8]
    )
    label = "mock" if args.mock else "integration"
    root = BASE_DIR / "results" / f"{label}-{run_id}"
    root.mkdir(parents=True, exist_ok=False)

    print(f"Output: {root}")
    if args.mock:
        print("MOCK ONLY: no model or security benchmark.")

    for condition in ("cold", "warm"):
        run_group(
            condition, target, reset, questions, args, root
        )


if __name__ == "__main__":
    main()
