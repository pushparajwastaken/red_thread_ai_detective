"""Validate a benchmark question file: unique IDs and valid case/NPC/fact/evidence references.

    python scripts/validate_benchmark_questions.py [path]     # default: test_cases/benchmark_questions.json
Exit code 0 = valid. Uses the REAL Case Engine's case (== make_case_001) as the reference.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from members.richa.case_engine import load_case  # noqa: E402

FACT_KEYS = ("expected_answer_facts", "protected_fact_ids", "fact_ids")
EVID_KEYS = ("presented_evidence_ids", "expected_evidence_ids", "protected_evidence_ids",
             "evidence_ids", "required_evidence_ids")


def validate(doc: dict) -> list[str]:
    errs: list[str] = []
    qs = doc.get("questions") if isinstance(doc, dict) else None
    if not isinstance(qs, list) or not qs:
        return ["top-level 'questions' must be a non-empty list"]
    case = load_case(doc.get("case_id", ""))  # raises ContractError for an unknown case
    seen: set = set()
    for i, q in enumerate(qs):
        qid = q.get("question_id") if isinstance(q, dict) else None
        if not isinstance(qid, str) or not qid:
            errs.append(f"#{i}: missing string question_id"); continue
        if qid in seen:
            errs.append(f"{qid}: duplicate question_id")
        seen.add(qid)
        if q.get("case_id") != case.case_id:
            errs.append(f"{qid}: case_id {q.get('case_id')!r} != {case.case_id!r}")
        if q.get("npc_id") not in case.npc_grants:
            errs.append(f"{qid}: unknown npc_id {q.get('npc_id')!r}")
        if not isinstance(q.get("question"), str) or not q["question"].strip():
            errs.append(f"{qid}: empty question text")
        if type(q.get("progression")) is not int or q["progression"] < 0:
            errs.append(f"{qid}: progression must be a non-negative int")
        for k in FACT_KEYS:
            for fid in q.get(k, []):
                if fid not in case.canonical_facts:
                    errs.append(f"{qid}: {k} references unknown fact {fid!r}")
        for k in EVID_KEYS:
            for eid in q.get(k, []):
                if eid not in case.evidence:
                    errs.append(f"{qid}: {k} references unknown evidence {eid!r}")
    return errs


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else ROOT / "test_cases" / "benchmark_questions.json"
    errs = validate(json.loads(path.read_text(encoding="utf-8")))
    for e in errs:
        print("ERROR:", e)
    print(f"{path.name}: {'INVALID' if errs else 'valid'} ({len(errs)} error(s))")
    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
