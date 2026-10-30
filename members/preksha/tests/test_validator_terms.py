"""Term-matching tests (TC_TERMS_*), fixture source: make_case_001().

Rules enforced (validator, lexical):
 * Terms match on WORD boundaries after NFKC + casefold + whitespace
   folding: "willful" must not hit the term "will" (owned by F003).
 * Multi-word terms ("lady ashby") match across any whitespace run.
 * A term owned only by facts the NPC may not know -> PROTECTED_TERM_LEAK;
   owned by an authorized fact that is not cited -> UNCITED_ASSERTION.
 * Look-alike characters must not slip past term matching (see TC_TERMS_009).
"""
import pytest

from shared.contracts import (
    DialogueDraft, DialogueRequest, Reason, SAFE_FALLBACK_TEXT,
)
from shared.fixture_case import make_case_001
from validator import validate_dialogue
from conftest import make_npc_context


def _validate(npc_id, text, facts=(), evidence=()):
    case = make_case_001()
    npc = make_npc_context(case, npc_id)
    request = DialogueRequest(
        npc_id=npc_id, question="What happened?",
        authorized_fact_ids=list(npc.authorized_fact_ids),
        permitted_evidence_ids=list(npc.permitted_evidence_ids),
        facts={f: case.canonical_facts[f] for f in npc.authorized_fact_ids},
        evidence=[case.evidence[e] for e in npc.permitted_evidence_ids])
    draft = DialogueDraft(npc_id=npc_id, text=text, cited_fact_ids=list(facts),
                          cited_evidence_ids=list(evidence))
    return validate_dialogue(request, draft, case, npc)


def _assert_fallback(result, reason):
    assert reason in result.reasons, f"expected {reason}, got {result.reasons}"
    assert result.used_fallback is True and result.valid is False
    assert result.text == SAFE_FALLBACK_TEXT
    assert result.cited_fact_ids == [] and result.cited_evidence_ids == []


def _assert_valid(result):
    assert Reason.OK in result.reasons, result.reasons
    assert result.used_fallback is False and result.valid is True


@pytest.mark.parametrize("npc_id", ["gardener", "cook"])
@pytest.mark.parametrize("text", [
    "He is a willful man.", "The willow tree shaded us.",
    "Goodwill is rare here.", "She was unwilling.",
], ids=["willful", "willow", "goodwill", "unwilling"])
def test_TC_TERMS_001_term_inside_longer_word_is_not_a_hit(npc_id, text):
    """'will' inside willful/willow/goodwill/unwilling must NOT match."""
    result = _validate(npc_id, text)
    assert Reason.PROTECTED_TERM_LEAK not in result.reasons, \
        f"substring match on 'will': {result.reasons}"
    assert Reason.UNCITED_ASSERTION not in result.reasons, result.reasons
    _assert_valid(result)


def test_TC_TERMS_002_multiword_term_uncited_is_uncited_assertion():
    """Cook may know F003: saying 'lady ashby' without citing it fails."""
    result = _validate("cook", "Lady Ashby looked upset.")
    _assert_fallback(result, Reason.UNCITED_ASSERTION)
    assert Reason.PROTECTED_TERM_LEAK not in result.reasons, result.reasons


def test_TC_TERMS_003_multiword_term_is_protected_for_gardener():
    """Gardener has no F003 grant: 'lady ashby' is a protected-term leak."""
    result = _validate("gardener", "Lady Ashby looked upset.")
    _assert_fallback(result, Reason.PROTECTED_TERM_LEAK)


def test_TC_TERMS_004_multiword_term_cited_is_accepted():
    """Positive control: cook cites F003 and may say 'lady ashby'."""
    result = _validate("cook", "Lady Ashby looked upset.", facts=["F003"])
    _assert_valid(result)
    assert result.cited_fact_ids == ["F003"]


@pytest.mark.parametrize("text", [
    "Lady    Ashby looked upset.", "Lady\nAshby looked upset.",
    "Lady\tAshby looked upset.", "LADY ASHBY looked upset.",
    "ＬＡＤＹ ＡＳＨＢＹ looked upset.",
], ids=["spaces", "newline", "tab", "uppercase", "fullwidth"])
def test_TC_TERMS_005_multiword_term_survives_formatting_tricks(text):
    """Whitespace runs, case and fullwidth forms still match 'lady ashby'."""
    _assert_fallback(_validate("cook", text), Reason.UNCITED_ASSERTION)


def test_TC_TERMS_006_partial_multiword_term_is_not_a_hit():
    """'Ashby' alone is not the term 'lady ashby'."""
    _assert_valid(_validate("cook", "Ashby was upset."))


def test_TC_TERMS_007_nfkc_fullwidth_will_is_folded():
    """NFKC folds fullwidth 'will' to ASCII, so the leak is caught."""
    text = "The ｗｉｌｌ was mentioned."
    _assert_fallback(_validate("gardener", text), Reason.PROTECTED_TERM_LEAK)


@pytest.mark.parametrize("npc_id,reason", [
    ("gardener", Reason.PROTECTED_TERM_LEAK),
    ("cook", Reason.UNCITED_ASSERTION),
], ids=["gardener_protected", "cook_uncited"])
def test_TC_TERMS_008_cyrillic_homoglyph_must_not_evade_terms(npc_id, reason):
    """'wіll' (Cyrillic U+0456) must still trigger the 'will' check.

    NOTE: NFKC has no mapping for Cyrillic 'i', so a plain NFKC+casefold
    normalizer leaves it unchanged and this check can fail. A failure here
    is a real validator gap (homoglyph bypass), not a test error.
    """
    result = _validate(npc_id, "Somebody changed the wіll.")
    _assert_fallback(result, reason)
