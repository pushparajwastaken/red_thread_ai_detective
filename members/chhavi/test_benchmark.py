
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
)


class TestBenchmark(unittest.TestCase):

    def test_median(self):
        values = [100, 200, 300, 400, 500]
        self.assertEqual(calculate_median(values), 300)

    def test_p95(self):
        values = [100, 200, 300, 400, 500]
        self.assertAlmostEqual(
            calculate_p95(values), 480
        )

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
