
"""
Red Thread AI Detective
Module 8: Performance Benchmarking
Developer: Chhavi Sharma

Benchmark result storage and latency statistics.
"""

import csv
import statistics
from dataclasses import asdict, fields
from pathlib import Path

from shared.contracts import BenchmarkRecord, DialogueResult


def save_results(records, filename):
    """Save benchmark records in CSV format."""

    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    columns = [
        field.name for field in fields(BenchmarkRecord)
    ]

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file, fieldnames=columns
        )
        writer.writeheader()

        for record in records:
            writer.writerow(asdict(record))


def calculate_median(values):
    """Return the median of recorded latencies."""

    if not values:
        return None

    return statistics.median(values)
  
def calculate_p95(values):
    """Calculate the 95th percentile latency."""

    if not values:
        return None

    sorted_values = sorted(values)

    if len(sorted_values) == 1:
        return sorted_values[0]

    position = (len(sorted_values) - 1) * 0.95
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)

    fraction = position - lower

    return (
        sorted_values[lower] * (1 - fraction)
        + sorted_values[upper] * fraction
    )
    
def create_benchmark_record(
    result: DialogueResult,
    run_id: str,
    question_id: str,
    hardware: str,
):
    """Convert an interrogation result into a benchmark record."""

    metrics = result.metrics

    if metrics is None:
        raise ValueError(
            "Cannot benchmark a result without TurnMetrics"
        )

    return BenchmarkRecord(
        run_id=run_id,
        mode=metrics.mode,
        model=metrics.model,
        hardware=hardware,
        question_id=question_id,
        npc_id=result.npc_id,
        ttft_ms=metrics.ttft_ms,
        generation_ms=metrics.generation_ms,
        validation_ms=metrics.validation_ms,
        total_ms=metrics.total_ms,
        prompt_tokens=metrics.prompt_tokens,
        completion_tokens=metrics.completion_tokens,
        cost_usd=metrics.cost_usd,
        valid=result.valid,
        used_fallback=result.used_fallback,
        reasons=";".join(result.reasons),
        answer_correct=None,
        leaked_protected_fact=None,
    )


