"""Benchmark-set validator (incl. negative cases) and dynamic-vs-branching comparability."""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_benchmark_questions import validate  # noqa: E402

from members.ananya import branching_baseline as bb
from shared.contracts import DialogueResult
from src.pipeline import interrogate, load_case

DOC = json.loads((ROOT / "test_cases" / "benchmark_questions.json").read_text(encoding="utf-8"))


def test_shipped_question_set_is_valid():
    assert validate(DOC) == []


@pytest.mark.parametrize("mutate,needle", [
    (lambda d: d["questions"][1].update(question_id=d["questions"][0]["question_id"]), "duplicate question_id"),
    (lambda d: d["questions"][0].update(npc_id="detective"), "unknown npc_id"),
    (lambda d: d["questions"][0].update(npc_id="Gardener"), "unknown npc_id"),
    (lambda d: d["questions"][0]["protected_fact_ids"].append("F999"), "unknown fact"),
    (lambda d: d["questions"][0]["presented_evidence_ids"].append("E404"), "unknown evidence"),
    (lambda d: d["questions"][0].update(case_id="case_002"), "case_id"),
    (lambda d: d["questions"][0].update(progression=-1), "progression"),
    (lambda d: d["questions"][0].update(question="  "), "empty question"),
])
def test_validator_rejects_corrupted_sets(mutate, needle):
    bad = copy.deepcopy(DOC)
    mutate(bad)
    assert any(needle in e for e in validate(bad))


def test_baseline_default_path_loads_the_canonical_shared_set():
    """Regression: the baseline used to look for a non-existent file and silently use its dev fixture."""
    assert bb.SHARED_QUESTION_SET == ROOT / "test_cases" / "benchmark_questions.json" and bb.SHARED_QUESTION_SET.exists()
    assert set(bb._load_question_set()) == {q["question_id"] for q in DOC["questions"]}


def test_both_modes_consume_identical_questions_cases_npcs_and_evidence():
    for q in DOC["questions"]:
        case_d = load_case("case_001"); case_d.progression = q["progression"]
        case_b = load_case("case_001"); case_b.progression = q["progression"]
        d = interrogate(case_d, q["npc_id"], q["question"], presented_evidence_ids=q["presented_evidence_ids"])
        b = bb.answer_branching(case_b, q["npc_id"], q["question_id"], presented_evidence_ids=q["presented_evidence_ids"])
        assert isinstance(d, DialogueResult) and isinstance(b, DialogueResult)
        assert d.npc_id == b.npc_id == q["npc_id"]
        assert d.metrics.mode == "dynamic" and b.metrics.mode == "branching"
        assert d.metrics.total_ms > 0 and b.metrics.total_ms > 0      # both measured, comparable
        assert case_d == case_b                                       # neither mode mutated state
