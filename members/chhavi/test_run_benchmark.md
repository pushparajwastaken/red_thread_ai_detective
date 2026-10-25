"""Tests for benchmark trial order, output and failure logging."""

import csv
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from members.chhavi.run_benchmark import (
    mock_interrogate,
    run_group,
)


class TestBenchmarkRunner(unittest.TestCase):

    def setUp(self):
        self.args = SimpleNamespace(
            mock=True,
            target=None,
            reset_hook=None,
            reset_description=None,
            configuration=None,
            hardware="test-hardware",
            repeats=2,
            warmup=1,
        )
        self.questions = [{
            "question_id": "Q001",
            "npc_id": "gardener",
            "question": "What did you see?",
            "presented_evidence_ids": [],
        }]

    def test_cold_resets_before_every_measurement(self):
        events = []

        def reset():
            events.append("reset")

        def target(case, npc_id, question, **kwargs):
            self.assertEqual(case.progression, 0)
            events.append("call")
            case.progression = 1
            return mock_interrogate(
                case, npc_id, question, **kwargs
            )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_group(
                "cold", target, reset,
                self.questions, self.args, root,
            )

            self.assertEqual(
                events,
                ["reset", "call", "reset", "call"],
            )

            with (root / "cold/benchmark_results.csv").open(
                newline="", encoding="utf-8"
            ) as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(len(rows), 2)
            self.assertTrue(
                all(row["run_id"].endswith("-cold") for row in rows)
            )

    def test_warmup_excluded_and_outputs_separate(self):
        events = []

        def reset():
            events.append("reset")

        def target(case, npc_id, question, **kwargs):
            events.append("call")
            return mock_interrogate(
                case, npc_id, question, **kwargs
            )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            run_group(
                "cold", target, reset,
                self.questions, self.args, root,
            )
            cold_path = root / "cold/benchmark_results.csv"
            original_cold = cold_path.read_bytes()

            events.clear()
            run_group(
                "warm", target, reset,
                self.questions, self.args, root,
            )

            self.assertEqual(
                events,
                [
                    "reset", "call", "call",
                    "reset", "call", "call",
                ],
            )

            with (root / "warm/benchmark_results.csv").open(
                newline="", encoding="utf-8"
            ) as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(len(rows), 2)
            self.assertEqual(cold_path.read_bytes(), original_cold)

            summary = json.loads(
                (root / "warm/summary.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(summary["condition"], "warm")
            self.assertEqual(summary["completed_records"], 2)
            self.assertEqual(len(summary["external_timings"]), 2)

    def test_failure_preserves_completed_records(self):
        calls = 0

        def target(case, npc_id, question, **kwargs):
            nonlocal calls
            calls += 1

            if calls == 2:
                raise RuntimeError("Simulated backend failure")

            return mock_interrogate(
                case, npc_id, question, **kwargs
            )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            with self.assertRaises(RuntimeError):
                run_group(
                    "cold", target, None,
                    self.questions, self.args, root,
                )

            summary = json.loads(
                (root / "cold/summary.json").read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(summary["completed_records"], 1)
            self.assertEqual(
                summary["failures"],
                [{
                    "trial": 2,
                    "question_id": "Q001",
                    "stage": "measurement",
                    "error_type": "RuntimeError",
                }],
            )

            with (root / "cold/benchmark_results.csv").open(
                newline="", encoding="utf-8"
            ) as file:
                self.assertEqual(len(list(csv.DictReader(file))), 1)


if __name__ == "__main__":
    unittest.main()
