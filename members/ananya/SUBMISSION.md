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

## Lead integration update (applied on top of merged PR #7, commit 44126a9)

- PR #7 already fixed the hard-coded `0.0` latency on successful branches (`elapsed` measured from `start`). That change is kept
  exactly as merged; the integration patch does not touch it.
- `SHARED_QUESTION_SET` still pointed at a non-existent `test_cases/branching_questions.json`, so the shared set was never loaded and
  the module silently used its local dev fixture. It now points at the canonical `test_cases/benchmark_questions.json`; the local
  Q001..Q006 fixture remains the fallback and the unit tests pin to it explicitly (autouse fixture).
- All 30 shared questions run through `answer_branching`: 30/30 correct under the shared rubric, 0 leaks, 3 evidence-rejection
  questions return the safe fallback by design (`UNAUTHORIZED_EVIDENCE`).
- Unit tests in this folder: 11 passed (10 original + 1 latency regression test added by the lead).
- Human playtest results: **still pending** (protocol and template are in this folder).
- Note for the owner: the "Dependencies" section above says the benchmark schema validation uses `jsonschema`, but `requirements.txt`
  does not list it, so on a clean install that one test is skipped (it passes once `jsonschema` is installed).
