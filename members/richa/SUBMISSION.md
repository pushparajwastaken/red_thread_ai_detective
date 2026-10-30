# Sprint 1 Submission - Module 1: Case Engine

**Owner:** Richa Bharti (case_001 extended by the integration lead)
**Contract:** `load_case(case_id: str) -> CaseState`
**Known case IDs:** `case_001` (canonical), `case_002` (Richa's original case, unchanged)

## History (why there are two cases)

Richa's original `case_001` (aman/neha/rohan, 12 facts) did not match the shared fixture `make_case_001()`
(gardener/cook), which the benchmark set, branching baseline and integration use. The lead realigned `case_001`
to the fixture and preserved her case as `case_002`. That left the canonical case with **two** NPCs and **empty**
`clues`/`timeline`, i.e. it did **not** meet the Sprint 1 requirement (one victim, exactly three suspects, ten
clues, a ground-truth timeline). The earlier version of this file reported the three-suspect/ten-clue integrity
numbers of `case_002` as if they described `case_001`. That was wrong and is corrected here.

## Implementation (verified)

- `case_001` now satisfies the requirement and still equals `make_case_001()` (asserted by tests).
  The original gardener/cook entries and every ID they can see are unchanged; the third suspect
  (`housekeeper`), facts `F005-F010`, evidence `E002 E004-E008 E010 E011`, ten clues and the timeline are appended.
  The third suspect is not named `butler` because existing tests use `butler` as the nonexistent NPC.
- Note: `F005-F010` in `case_001` are **different facts** from `F005-F010` in `case_002`; IDs are scoped per case.
- One shared, type-defensive validator covers both cases: ID formats, duplicate IDs, dangling references,
  clue evidence actually supports each clued fact, authored lies never referenced as truth, strictly ordered
  in-range integer timeline, exactly one victim, every suspect clued and on the timeline. Any malformed data
  surfaces as `ContractError` (a safety net converts stray `TypeError`/`AttributeError`).
- Deterministic queries `fact_access` / `evidence_access` / `can_suspect_know_fact` / `can_suspect_use_evidence`.
- `load_case` builds and validates a fresh object on every call; unknown or inexact IDs raise `ContractError`.

## Integrity report: case_001 (canonical)

| Check | Result |
|---|---:|
| Victims / suspects / clues | 1 / 3 / 10 |
| Canonical facts with matching metadata (incl. 1 authored lie) | 11 / 11 |
| Evidence records | 11 |
| Ground-truth timeline events, strictly ordered | 9 |
| Dangling fact/evidence/suspect references | 0 |
| Duplicate clue, event or reference IDs | 0 |
| Equals `make_case_001()` at every progression | Pass |
| Repeated loads equal and independent | Pass |

`case_002` (unchanged): 12 facts, 12 evidence, 3 suspects, 10 clues, 11 timeline events.

## Test results (Linux sandbox, Python 3.12.3, pytest 9.2.0)

| Command | Result |
|---|---|
| `python -m pytest members/richa -q` | 189 passed (was 19) |
| `python -m pytest tests/test_case_acceptance.py -q` | 46 passed |

Mutation check: 19 deliberate defects in the engine and 9 in pipeline gates were each caught by these tests.
`test_case_001_has_canonical_npcs_and_no_private_internals` was rewritten because it asserted the requirement was
NOT met (`{gardener, cook}`, `clues == []`, `timeline == []`); it is now `..._and_private_internals`.

## Known limits

"Can know" means *authorized* (granted and revealed), not omniscience: the guilty cook is not granted her own
crime. Whether the requirement means authorization or ground-truth presence is a decision for the lead.
