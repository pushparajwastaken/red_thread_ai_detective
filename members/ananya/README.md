# Ananya — Branching Baseline

This folder contains Ananya Narula's Module 9 deliverable: a deterministic fixed-dialogue branching baseline and the replayability/playtest protocol.

## Files

- `branching_baseline.py` — implements `answer_branching(...)`.
- `branching_questions.json` — local development question set because the shared `test_cases/` directory is currently empty.
- `test_branching_baseline.py` — component tests.
- `playtest_protocol.md` — matched dynamic-vs-branching evaluation protocol and metrics.
- `playtest_results_template.csv` — empty template for real participant results.

## Run

From the repository root:

```bash
python -m pytest members/ananya/test_branching_baseline.py -q
```

The implementation is deterministic and does not require an API key or model.

## Integration note

When the team adds the real shared branching question set under `test_cases/`, the implementation will prefer that shared file when it is named `branching_questions.json`; otherwise it uses the local development fixture.

The component does not modify `CaseState`, `shared/`, `src/`, or the shared `test_cases/` directory.
