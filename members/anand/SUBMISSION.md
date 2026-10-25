# NPC Knowledge Module

This project implements the NPC knowledge retrieval flow for the repository's case model. The goal is to produce a safe, filtered context for a specific NPC without exposing unrelated or unauthorized information.

## What I implemented

- Added `members/anand/npc_knowledge.py` with `build_npc_context(case, npc_id)`.
- Added `UnknownNPCError` and `NPCContext` to enforce the repository contract.
- Resolved NPCs by exact canonical ID and raised `UnknownNPCError` for invalid IDs.
- Applied authorization and progression-based filtering before returning any knowledge.
- Kept epistemic categories separated so the result distinguishes:
  - `known_facts`
  - `suspected_facts`
  - `cover_story`
- Ensured the input `case` is not mutated and that mutable collections are returned as independent copies.

## Behavior and safety checks

The implementation enforces the following rules:

- Fact authorization is checked against the fact's `authorized_for` / `authorized_npcs`-style metadata and any case-level access map.
- Progression gating is honored for facts tied to discovery or threshold requirements.
- Facts remain hidden until required discoveries or progression thresholds are available.
- The function never leaks the full case into an NPC context.
- False or deceptive explanations are preserved separately from actual case knowledge.

## Validation

I validated the change with the following test commands:

1. `python -m pytest tests/test_npc_knowledge.py -v`
2. `python -m pytest -v`

Result: both commands passed successfully, with the focused NPC knowledge test file passing and the full repository test suite passing.

## Notes and limitations

- The repository's shared interface is intentionally permissive, so the implementation follows flexible case-state parsing rather than a rigid schema.
- No unresolved contract discrepancies were present in the working repository, and the shared contract was treated as authoritative.

## Files involved

- `members/anand/npc_knowledge.py`
- `tests/test_npc_knowledge.py`

This work completes the NPC knowledge module behavior requested by the task and keeps the implementation aligned with the repository contract.
