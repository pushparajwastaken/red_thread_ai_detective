"""
Tests for Module 8: Performance Benchmarking
Developer: Chhavi Sharma
"""

import unittest

from shared.contracts import DialogueResult, TurnMetrics
from members.chhavi.benchmark import (
    create_benchmark_record,
    calculate_median,
    calculate_p95,
    summarize_results,
)


class TestBenchmark(unittest.TestCase):

    def test_median(self):
        values = [100, 200, 300, 400, 500]
        self.assertEqual(calculate_median(values), 300)

    def test_p95(self):
        values = [100, 200, 300, 400, 500]
        self.assertAlmostEqual(calculate_p95(values), 480)

    def test_empty_values(self):
        self.assertIsNone(calculate_median([]))
        self.assertIsNone(calculate_p95([]))

    def test_create_benchmark_record(self):
        metrics = TurnMetrics(
            mode="dynamic",
            model="test-model",
            ttft_ms=120.0,
            generation_ms=300.0,
            validation_ms=20.0,
            total_ms=450.0,
            prompt_tokens=100,
            completion_tokens=50,
            cost_usd=None,
        )

        result = DialogueResult(
            npc_id="npc_test",
            text="I was at home.",
            cited_fact_ids=[],
            valid=True,
            used_fallback=False,
            latency_ms=450.0,
            reasons=["OK"],
            metrics=metrics,
        )

        record = create_benchmark_record(
            result=result,
            run_id="test_run_001",
            question_id="Q001",
            hardware="test-hardware",
        )

        self.assertEqual(record.total_ms, 450.0)
        self.assertEqual(record.ttft_ms, 120.0)
        self.assertEqual(record.model, "test-model")
        self.assertEqual(record.mode, "dynamic")
        self.assertTrue(record.valid)
        self.assertIsNone(record.cost_usd)

    def test_summary_groups_and_missing_ttft(self):
        records = []

        samples = [
            ("dynamic", "mock-a", 100.0, None),
            ("dynamic", "mock-a", 300.0, 50.0),
            ("branching", "fixed", 10.0, None),
            ("dynamic", "mock-b", 500.0, None),
        ]

        for index, (mode, model, total, ttft) in enumerate(samples):
            result = DialogueResult(
                npc_id="gardener",
                text="Test response.",
                cited_fact_ids=[],
                valid=True,
                used_fallback=False,
                latency_ms=total,
                reasons=["OK"],
                metrics=TurnMetrics(
                    mode=mode,
                    model=model,
                    total_ms=total,
                    ttft_ms=ttft,
                ),
            )

            records.append(
                create_benchmark_record(
                    result,
                    f"test_{index}",
                    "Q001",
                    "test-hardware",
                )
            )

        summaries = {
            (item["mode"], item["model"]): item
            for item in summarize_results(records)
        }

        self.assertEqual(len(summaries), 3)

        dynamic = summaries[("dynamic", "mock-a")]
        self.assertEqual(dynamic["n"], 2)
        self.assertEqual(dynamic["total_median_ms"], 200.0)
        self.assertAlmostEqual(dynamic["total_p95_ms"], 290.0)
        self.assertEqual(dynamic["ttft_n"], 1)
        self.assertEqual(dynamic["ttft_median_ms"], 50.0)
        self.assertEqual(dynamic["fallback_count"], 0)

        branching = summaries[("branching", "fixed")]
        self.assertEqual(branching["ttft_n"], 0)
        self.assertIsNone(branching["ttft_median_ms"])
        self.assertIsNone(branching["ttft_p95_ms"])

        self.assertEqual(summarize_results([]), [])

    def test_missing_metrics(self):
        result = DialogueResult(
            npc_id="npc_test",
            text="I cannot answer that reliably.",
            cited_fact_ids=[],
            valid=False,
            used_fallback=True,
            latency_ms=0.0,
            metrics=None,
        )

        with self.assertRaises(ValueError):
            create_benchmark_record(
                result,
                "test_run_002",
                "Q002",
                "test-hardware",
            )


if __name__ == "__main__":
    unittest.main()
       
      
