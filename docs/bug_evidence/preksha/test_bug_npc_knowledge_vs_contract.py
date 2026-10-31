"""BUG EVIDENCE : npc_knowledge.py vs the contract.

INTENTIONAL FAILURES: these tests fail on the first run, by design. They are
the evidence attached to the bug report, so they are neither skipped nor
xfailed. They go green only when npc_knowledge.py honours shared/contracts.py.

Violations demonstrated (one test each):
 (a) npc_knowledge.NPCContext is a dict subclass (known_facts /
     suspected_facts / cover_story), not shared.contracts.NPCContext
     (authorized_fact_ids / permitted_evidence_ids).
 (b) npc_knowledge.UnknownNPCError is a different class object from
     shared.contracts.UnknownNPCError, so `except UnknownNPCError` written
     against the contract never catches his error.
 (c) build_npc_context(make_case_001(), "gardener") raises his
     UnknownNPCError: he looks up npcs / facts / npc_lookup, but the fixture
     (and Richa's engine) use npc_grants / canonical_facts.
Passing tests elsewhere use the conftest make_npc_context shim instead.
"""
import pytest

from shared.contracts import NPCContext, UnknownNPCError
from shared.fixture_case import make_case_001
from npc_knowledge import (
    NPCContext as AnandNPCContext,
    UnknownNPCError as AnandUnknownNPCError,
    build_npc_context,
)


def test_TC_BUGANAND_001_npc_context_is_not_the_contract_type():
    """(a) His NPCContext must be the shared dataclass, not a dict subclass."""
    assert AnandNPCContext is NPCContext, (
        f"npc_knowledge.NPCContext ({AnandNPCContext.__mro__}) is not "
        f"shared.contracts.NPCContext")
    assert not issubclass(AnandNPCContext, dict), \
        "npc_knowledge.NPCContext is a dict subclass"


def test_TC_BUGANAND_002_unknown_npc_error_is_a_different_class():
    """(b) His UnknownNPCError must be the contract's class object."""
    assert AnandUnknownNPCError is UnknownNPCError, (
        f"npc_knowledge.UnknownNPCError (id {id(AnandUnknownNPCError)}) is not "
        f"shared.contracts.UnknownNPCError (id {id(UnknownNPCError)})")


def test_TC_BUGANAND_003_builder_rejects_the_golden_fixture():
    """(c) build_npc_context(make_case_001(), 'gardener') must not raise."""
    case = make_case_001()
    try:
        ctx = build_npc_context(case, "gardener")
    except AnandUnknownNPCError as exc:
        pytest.fail(
            f"build_npc_context raised UnknownNPCError({exc}) for 'gardener', "
            f"which exists in the fixture: it reads npcs/facts/npc_lookup but "
            f"the fixture has npc_grants={sorted(case.npc_grants)} and "
            f"canonical_facts")
    assert isinstance(ctx, NPCContext), f"got {type(ctx)}"
    assert ctx.authorized_fact_ids == ["F001", "F002"], ctx
