# Ananya — Submission

## Assigned Module

Module 9 — Branching Baseline, plus the matched playtest/replayability protocol.

## Files

- `branching_baseline.py`
- `branching_questions.json`
- `test_branching_baseline.py`
- `playtest_protocol.md`
- `playtest_results_template.csv`
- `README.md`

## Contract

Implements:

```python
answer_branching(case, npc_id, question_id, *, presented_evidence_ids=()) -> DialogueResult
```

The returned metrics use `mode="branching"` so branching and dynamic records remain comparable.

## Dependencies

Uses Python standard library, repository shared contracts/fixtures, and pytest for testing.

The benchmark schema validation uses the `jsonschema` dependency.

## Exact Test Commands

From repository root:

```bash
python -m pytest members/ananya/test_branching_baseline.py -q
python -m pytest tests/test_benchmark_questions.py -q
python -m pytest tests/test_npc_knowledge.py -q
python -m pytest -q -rs
```

## Test Status

The complete repository test suite was executed successfully.

```text
32 passed in 0.45s
```

All tests passed with no skipped or failed tests after installing the required `jsonschema` dependency.

## Known Limitations

- The branching baseline is intentionally deterministic and fixed-dialogue; it serves as a comparison baseline, not the dynamic dialogue implementation.
- No participant/playtest results are fabricated; `playtest_results_template.csv` must be populated from actual runs.
- Engagement and replayability claims must remain limited to collected evidence.
- Benchmark question and NPC knowledge tests validate the baseline against the repository's current test cases. Passing automated tests does not establish real-world engagement or replayability.

## Branch / Commit

- Branch: `feature/ananya-branching-baseline`
- Integration commit: `50ce755` — Merge `origin/main` into `feature/ananya-branching-baseline`
