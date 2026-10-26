# Ananya — Submission

## Assigned module

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

No new third-party dependencies. Uses Python standard library plus the repository's existing `shared` contracts/fixture and pytest for tests.

## Exact test command

From repository root:

```bash
python -m pytest members/ananya/test_branching_baseline.py -q
```

## Test status

Development test suite: 10 tests passing in 0.13s against the current shared/fixture_case.py fixture.

## Known limitations

- The shared `test_cases/` directory is currently empty, so the local question set is a development fixture only.
- No participant/playtest results are fabricated; `playtest_results_template.csv` must be populated from actual runs.
- Engagement/replayability claims must remain limited to collected evidence.
- The branching baseline is intentionally deterministic and fixed-dialogue; it is a comparison baseline, not the dynamic dialogue implementation.

## Branch / commit

Fill these in after creating the personal feature branch and committing:

- Branch: feature/ananya-branching-baseline
- Commit: pending documentation update