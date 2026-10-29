# Sprint 1 Submission - Module 2: NPC Knowledge

**Owner:** Anand Kumar Sahni
**Contract:** `build_npc_context(case: CaseState, npc_id: str) -> NPCContext`
**Branch / commit SHA:** not recorded in the reviewed snapshot (unverified).

> **Lead integration update.** The original submission implemented its own `NPCContext` /
> `UnknownNPCError` and parsed a dict-shaped case (`npcs`, `known_facts`, `authorized_for`) that the
> shared contract never defined. Against the real `CaseState` it raised `UnknownNPCError` for every NPC.
> The module was refactored by the integration lead onto the shared types; the original dict-shaped
> test (which passed only because it tested that invented shape) was replaced.

## Implementation (current)

- Uses `shared.contracts.NPCContext` and `shared.contracts.UnknownNPCError`; no private duplicates.
- Raises `UnknownNPCError` for any `npc_id` not exactly in `case.npc_grants` (case-sensitive; non-strings too).
- Returns only granted facts/evidence with `reveal_at <= case.progression`; cover stories are ordinary grants.
- Returns fresh lists; never mutates `case`; never reads `clues` / `timeline`; `beliefs`/`suspicions` left empty (deprecated in v2).

## Tests

`python -m pytest tests/test_npc_knowledge.py -q` - 19 passed (fixture AND the real Case Engine; progression gating,
future-fact protection, exact IDs, non-mutation, independence, determinism).
Dependencies: none.
