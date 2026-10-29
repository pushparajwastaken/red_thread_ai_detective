"""Module 2 - NPC Knowledge (shared/interfaces.md, v2).

    build_npc_context(case: CaseState, npc_id: str) -> NPCContext

Uses the shared contract types only (``shared.contracts.NPCContext`` and
``shared.contracts.UnknownNPCError``); no private types or data shapes.

Rules enforced here:
* NPC IDs are exact and case-sensitive; an unknown ID raises UnknownNPCError.
* Only items GRANTED to the NPC (``case.npc_grants``) are returned, and only
  when ``reveal_at <= case.progression``. Cover stories (kind="cover_story")
  are ordinary grants: an NPC may assert them once granted and revealed.
* Returned lists are fresh copies; ``case`` is never mutated.
* ``beliefs`` / ``suspicions`` are deprecated in v2 and are left empty. This
  module never reads ``case.clues`` or ``case.timeline``.
"""
from __future__ import annotations

from shared.contracts import CaseState, NPCContext, UnknownNPCError

__all__ = ["build_npc_context", "NPCContext", "UnknownNPCError"]


def build_npc_context(case: CaseState, npc_id: str) -> NPCContext:
    # A non-str ID can never match (and may be unhashable); treat as unknown.
    if not isinstance(npc_id, str) or npc_id not in case.npc_grants:
        raise UnknownNPCError(f"Unknown NPC: {npc_id!r}")

    grant = case.npc_grants[npc_id]
    progression = case.progression

    fact_ids = [fid for fid in grant.fact_ids if case.reveal_at(fid) <= progression]
    evidence_ids = [
        eid for eid in grant.evidence_ids
        if eid in case.evidence and case.evidence[eid].reveal_at <= progression
    ]
    return NPCContext(
        npc_id=npc_id,
        authorized_fact_ids=fact_ids,
        permitted_evidence_ids=evidence_ids,
        persona=grant.persona,
    )
