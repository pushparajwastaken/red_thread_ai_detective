"""NPC shim tests (TC_SHIM_*), fixture source: make_case_001().

Rule enforced: conftest.make_npc_context(case, npc_id) returns the CONTRACT
shared.contracts.NPCContext dataclass (authorized_fact_ids /
permitted_evidence_ids), built straight from CaseState.npc_grants. It is
used instead of Anand's npc_knowledge.build_npc_context, whose dict-based
NPCContext does not match the contract.
"""
import pytest

from shared.contracts import DialogueDraft, DialogueRequest, NPCContext, Reason
from shared.fixture_case import make_case_001
from validator import validate_dialogue
from conftest import make_npc_context


def test_TC_SHIM_001_gardener_returns_contract_context():
    """make_npc_context(case, 'gardener') is the contract NPCContext."""
    ctx = make_npc_context(make_case_001(), "gardener")
    assert type(ctx) is NPCContext, f"got {type(ctx)}"
    assert not isinstance(ctx, dict), "must not be Anand's dict-style context"
    assert ctx.npc_id == "gardener"


def test_TC_SHIM_002_cook_returns_contract_context():
    """make_npc_context(case, 'cook') is the contract NPCContext."""
    ctx = make_npc_context(make_case_001(), "cook")
    assert type(ctx) is NPCContext, f"got {type(ctx)}"
    assert not isinstance(ctx, dict), "must not be Anand's dict-style context"
    assert ctx.npc_id == "cook"


def test_TC_SHIM_003_gardener_authorized_facts_exact():
    """Gardener is authorized for exactly F001 and F002, in that order."""
    ctx = make_npc_context(make_case_001(), "gardener")
    assert ctx.authorized_fact_ids == ["F001", "F002"], ctx.authorized_fact_ids


def test_TC_SHIM_004_cook_includes_cover_story():
    """Cook's authorized facts include the cover story L001."""
    ctx = make_npc_context(make_case_001(), "cook")
    assert "L001" in ctx.authorized_fact_ids, ctx.authorized_fact_ids
    assert ctx.authorized_fact_ids == ["F003", "L001"], ctx.authorized_fact_ids


@pytest.mark.parametrize("npc_id,evidence", [
    ("gardener", ["E001", "E003"]),
    ("cook", []),
])
def test_TC_SHIM_005_permitted_evidence_matches_grant(npc_id, evidence):
    """permitted_evidence_ids mirror the NPCGrant evidence list exactly."""
    ctx = make_npc_context(make_case_001(), npc_id)
    assert ctx.permitted_evidence_ids == evidence, ctx.permitted_evidence_ids


@pytest.mark.parametrize("npc_id,persona", [
    ("gardener", "A blunt old gardener."),
    ("cook", "A nervous cook."),
])
def test_TC_SHIM_006_persona_is_copied_from_grant(npc_id, persona):
    """The persona string comes from the NPCGrant."""
    assert make_npc_context(make_case_001(), npc_id).persona == persona


@pytest.mark.parametrize("npc_id", ["gardener", "cook"])
def test_TC_SHIM_007_spoilers_are_never_authorized(npc_id):
    """The fixture grants F004 / E009 to nobody, so the shim omits them."""
    ctx = make_npc_context(make_case_001(), npc_id)
    assert "F004" not in ctx.authorized_fact_ids
    assert "E009" not in ctx.permitted_evidence_ids


def test_TC_SHIM_008_lists_are_independent_copies():
    """Mutating the context must not change the case's NPCGrant."""
    case = make_case_001()
    ctx = make_npc_context(case, "gardener")
    ctx.authorized_fact_ids.append("F004")
    ctx.permitted_evidence_ids.append("E009")
    grant = case.npc_grants["gardener"]
    assert grant.fact_ids == ["F001", "F002"], grant.fact_ids
    assert grant.evidence_ids == ["E001", "E003"], grant.evidence_ids


def test_TC_SHIM_009_unknown_npc_raises_key_error():
    """An NPC with no grant is a KeyError from the shim (not a fallback)."""
    with pytest.raises(KeyError):
        make_npc_context(make_case_001(), "butler")


@pytest.mark.parametrize("npc_id,text,facts", [
    ("gardener", "I saw a figure by the greenhouse.", ["F001"]),
    ("cook", "I never left the kitchen all evening.", ["L001"]),
])
def test_TC_SHIM_010_shim_context_is_accepted_by_validator(npc_id, text, facts):
    """Positive control: validate_dialogue accepts a shim context."""
    case = make_case_001()
    npc = make_npc_context(case, npc_id)
    request = DialogueRequest(
        npc_id=npc_id, question="What happened?",
        authorized_fact_ids=list(npc.authorized_fact_ids),
        permitted_evidence_ids=list(npc.permitted_evidence_ids),
        facts={f: case.canonical_facts[f] for f in npc.authorized_fact_ids},
        evidence=[case.evidence[e] for e in npc.permitted_evidence_ids])
    draft = DialogueDraft(npc_id=npc_id, text=text, cited_fact_ids=facts,
                          cited_evidence_ids=[])
    result = validate_dialogue(request, draft, case, npc)
    assert Reason.OK in result.reasons, result.reasons
    assert result.used_fallback is False and result.valid is True
    assert result.cited_fact_ids == facts