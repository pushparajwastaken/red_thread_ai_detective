# Case Engine

Author: Richa Bharti (case_001 extended to the Sprint 1 case requirement by the integration lead)

## Overview

`load_case(case_id: str) -> CaseState` loads a deterministic, validated authored case. Known IDs (exact,
case-sensitive): `case_001` (canonical, equals `shared.fixture_case.make_case_001()`) and `case_002`
(Richa's original richer case, kept unchanged and separate).

## case_001 contents (canonical)

- One victim (`lord_ashby`), exactly three suspects (`gardener`, `cook`, `housekeeper`), exactly ten clues,
  and a nine-event ground-truth timeline with strictly increasing times.
- 11 canonical facts (`F001-F010` truth, `L001` the cook's authored lie), 11 evidence items, explicit fact and
  evidence grants per suspect, `reveal_at` progression gating.
- Ground truth: the cook poisoned the decanter. The authored lie is never referenced by a clue or the timeline.
- The original gardener/cook data is unchanged; everything added for the requirement is appended after it.

The `clues` and `timeline` fields are for the Case Engine only. Other modules must not read them.

## Deterministic knowledge queries

`fact_access`, `evidence_access` -> `ALLOWED | NOT_YET_REVEALED | NOT_GRANTED`; `can_suspect_know_fact`,
`can_suspect_use_evidence` -> bool. Pure functions of the authored grants and `reveal_at`.

## Running tests

```powershell
.\.venv\Scripts\python.exe -m pytest members/richa -q
.\.venv\Scripts\python.exe -m pytest tests/test_case_acceptance.py -q
```

See [SUBMISSION.md](./SUBMISSION.md) for the integrity report and results.
