# Sprint 1 Submission — Module 1: Case Engine

**Owner:** Richa Bharti
**Contract:** `load_case(case_id: str) -> CaseState`
**Known case ID:** `case_001`

## Implementation

- Loads fresh, deterministic case data containing canonical facts, complete
  `fact_meta`, evidence, and NPC grants for three suspects.
- Includes the six requested facts F005-F010 verbatim.
- Marks Rohan's authored in-world lie as `kind="cover_story"` so it is not
  represented as canonical truth.
- Keeps exactly ten clues and the ordered ground-truth timeline in Case Engine
  data; other modules should not depend on either field.
- Rejects unknown or invalid case IDs with `ContractError`.
- Validates fact metadata, the one-victim/three-suspect/ten-clue requirements,
  unique clue and timeline IDs, ordered timeline events, and clue/timeline
  references.

## Integrity report

| Check | Result |
|---|---:|
| Canonical facts with matching metadata | 12 / 12 |
| Evidence records | 12 |
| Suspects / NPC grants | 3 |
| Victims in ground-truth timeline | 1 |
| Clues | 10 |
| Timeline events, ordered | 11 |
| Dangling fact/evidence/suspect references | 0 |
| Duplicate clue or timeline IDs | 0 |
| Fact metadata terms lowercase | Pass |
| Repeated loads equivalent and independent | Pass |

## Focused test result

Command:

```powershell
python -m pytest members/richa/test_case_engine.py
```

Result: **13 passed**.

Focused tests cover successful loading, unknown and invalid IDs, fixture
validation, reference integrity, duplicate IDs, the required case counts,
lowercase inflection terms, cover-story distinction, and repeated-load
equivalence.
