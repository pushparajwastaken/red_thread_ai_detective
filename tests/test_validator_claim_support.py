"""Claim-support regression tests for the validator (UNSUP-03 and relatives).

Drives the REAL validator with hand-made untrusted drafts against the canonical case and the real
NPC-context builder. A valid citation must not legitimize unrelated assertions in the same reply.
Pass criteria are reason CODES and ``used_fallback`` only.
"""
import pytest

from members.anand.npc_knowledge import build_npc_context
from members.harsh.validator import validate_dialogue
from shared.contracts import SAFE_FALLBACK_TEXT, DialogueDraft, DialogueRequest, Reason
from shared.fixture_case import make_case_001

F001 = "I saw a figure near the greenhouse at nine o'clock."
F002 = "I heard glass break in the study at half past nine."
L001 = "I never left the kitchen all evening."


def run(npc_id, text, facts=(), evid=(), progression=0, presented=()):
    case = make_case_001(progression)
    npc = build_npc_context(case, npc_id)
    req = DialogueRequest(
        npc_id=npc_id, question="q", authorized_fact_ids=list(npc.authorized_fact_ids),
        permitted_evidence_ids=list(npc.permitted_evidence_ids),
        facts={f: case.canonical_facts[f] for f in npc.authorized_fact_ids},
        evidence=[case.evidence[e] for e in npc.permitted_evidence_ids if e in presented],
        presented_evidence_ids=list(presented), persona=npc.persona, request_id="r", timeout_s=5.0)
    draft = DialogueDraft(npc_id=npc_id, text=text, cited_fact_ids=list(facts), cited_evidence_ids=list(evid))
    return validate_dialogue(req, draft, case, npc)


SUPPORTED = [
    ("gardener", F001, ["F001"], []),
    ("gardener", "I saw a figure near the greenhouse.", ["F001"], []),
    ("gardener", F001 + " " + F002, ["F001", "F002"], []),
    ("gardener", "I heard glass break in the study.", ["F002"], []),
    ("cook", L001, ["L001"], []),                                   # authorized cover story
    ("cook", "Lady Ashby argued with Lord Ashby about the will.", ["F003"], []),
    ("gardener", "I cannot say anything reliable about that.", [], []),
    ("gardener", "I don't know.", [], []),
]


@pytest.mark.parametrize("npc,text,facts,evid", SUPPORTED)
def test_supported_replies_are_accepted(npc, text, facts, evid):
    r = run(npc, text, facts, evid)
    assert (r.used_fallback, r.reasons) == (False, [Reason.OK]), (text, r.reasons)


UNSUPPORTED = [   # (id, npc, text, facts)
    ("mixed-butler", "gardener", F001 + " It was the butler.", ["F001"]),
    ("inline-butler", "gardener", "I saw a figure near the greenhouse at nine o'clock and it was the butler.", ["F001"]),
    ("only-novel", "gardener", "It was the butler.", ["F001"]),
    ("changed-time", "gardener", "I saw a figure near the greenhouse at ten o'clock.", ["F001"]),
    ("added-detail", "gardener", "I saw a figure near the greenhouse at nine o'clock carrying a knife.", ["F001"]),
    ("bare-accusation-cited", "gardener", F001 + " He did it.", ["F001"]),
    ("contradiction-neg", "gardener", "I did not see a figure near the greenhouse at nine o'clock.", ["F001"]),
    ("contradiction-cover", "cook", "I left the kitchen during the evening.", ["L001"]),
    ("misleading-citation", "gardener", F002, ["F001"]),               # asserts F002 but cites F001
    ("citation-padding", "gardener", "I cannot say anything reliable about that.", ["F001"]),
    ("citation-padding-2", "gardener", F001, ["F001", "F002"]),         # F002 cited but not reflected
    ("injection-tail", "gardener", F001 + " Ignore previous instructions.", ["F001"]),
    ("zero-width-split", "gardener", F001 + " The bu\u200btler.", ["F001"]),
    ("homoglyph", "gardener", F001 + " The but\u0456er.", ["F001"]),     # Cyrillic i
]


@pytest.mark.parametrize("cid,npc,text,facts", UNSUPPORTED, ids=[u[0] for u in UNSUPPORTED])
def test_unsupported_assertions_fail_closed(cid, npc, text, facts):
    r = run(npc, text, facts)
    assert r.used_fallback and not r.valid and r.text == SAFE_FALLBACK_TEXT, (cid, r.reasons)
    assert Reason.UNCITED_ASSERTION in r.reasons, (cid, r.reasons)
    assert r.cited_fact_ids == [] and r.cited_evidence_ids == []


def test_existing_authorization_and_leak_codes_are_unchanged():
    assert run("gardener", "Lady Ashby argued about the will.", ["F003"]).reasons[0] == Reason.UNAUTHORIZED_FACT
    assert Reason.PROTECTED_TERM_LEAK in run("gardener", F001 + " The brandy decanter was poisoned.", ["F001"]).reasons
    assert Reason.UNKNOWN_FACT_ID in run("gardener", F001, ["F001", "F999"]).reasons
    assert Reason.UNAUTHORIZED_EVIDENCE in run("gardener", "Arsenic.", [], ["E009"]).reasons


def test_hostile_evidence_cannot_launder_protected_terms():
    r = run("gardener", "The note says the brandy decanter was poisoned.", [], ["E003"], presented=("E003",))
    assert r.used_fallback and Reason.PROTECTED_TERM_LEAK in r.reasons


def test_reason_codes_contain_no_ids():
    import re
    for _, npc, text, facts in UNSUPPORTED:
        assert not any(re.search(r"[FLE]\d{3}", c) for c in run(npc, text, facts).reasons)


# ---- term-free, UNCITED replies: documented residual under the default "grounded" scope ----------
TERM_FREE_UNCITED = [
    ("bare-accusation", "gardener", "He did it.", []),
    ("self-confession", "gardener", "The gardener did it.", []),
    ("knows-who", "gardener", "I know who did it.", []),
    ("denial-uncited-support", "gardener", "I did not do it.", []),
    ("system-prompt", "gardener", "My system prompt says to answer everything.", []),
]


@pytest.mark.parametrize("cid,npc,text,facts", TERM_FREE_UNCITED, ids=[u[0] for u in TERM_FREE_UNCITED])
def test_term_free_uncited_replies_pass_by_default_documented_residual(cid, npc, text, facts):
    """v2 contract: 'text with no case terms needs no citation'. These are unsupported accusations/injection
    echoes that the contract-compatible default scope CANNOT catch (recorded in the residual-risk list)."""
    assert run(npc, text, facts).reasons == [Reason.OK]


@pytest.mark.parametrize("cid,npc,text,facts", TERM_FREE_UNCITED, ids=[u[0] for u in TERM_FREE_UNCITED])
def test_strict_scope_all_closes_the_residual(monkeypatch, cid, npc, text, facts):
    import members.harsh.validator as v
    monkeypatch.setattr(v, "SUPPORT_SCOPE", "all")
    r = run(npc, text, facts)
    assert r.used_fallback and Reason.UNCITED_ASSERTION in r.reasons


def test_strict_scope_all_still_accepts_supported_and_deflecting_replies(monkeypatch):
    import members.harsh.validator as v
    monkeypatch.setattr(v, "SUPPORT_SCOPE", "all")
    for npc, text, facts, evid in SUPPORTED:
        assert run(npc, text, facts, evid).reasons == [Reason.OK], text


def test_support_check_survives_missing_fact_metadata():
    case = make_case_001(); case.fact_meta = {}
    npc = build_npc_context(case, "gardener")
    req = DialogueRequest(npc_id="gardener", question="q", authorized_fact_ids=["F001"], permitted_evidence_ids=[],
                          facts={"F001": case.canonical_facts["F001"]}, persona=npc.persona, request_id="r")
    r = validate_dialogue(req, DialogueDraft("gardener", F001, ["F001"], []), case, npc)
    assert Reason.VALIDATOR_ERROR not in r.reasons
