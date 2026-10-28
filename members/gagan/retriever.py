"""Deterministic lexical evidence retrieval for shared/contracts.py v2 (Module 3).

Pure function: no LLM calls, no network, no randomness, no state mutation.
The question is treated as DATA. It is only tokenized and compared, never
executed or interpreted. Evidence authority comes from `case` plus the
`permitted_evidence_ids` supplied by Integration, never from the question.
"""
from __future__ import annotations

import re
import unicodedata

from shared.contracts import CaseState, EvidenceItem

# Policy constants (documented in README.md).
TERM_WEIGHT = 3             # points per distinct authored EvidenceItem.terms hit
CONTENT_WEIGHT = 1          # points per distinct shared content word
MAX_QUESTION_CHARS = 2000   # longer questions are truncated, not rejected
MIN_TOKEN_LEN = 3           # shorter words are ignored for content overlap

_STOPWORDS = frozenset(
    "the and for you your was were what who why how when where did does "
    "have has had not but are with that this there then them they his her "
    "she him about from into over say said tell any can could would should "
    "which whose been being than too very just also".split()
)
_WORD = re.compile(r"\w+")


def _normalize(text: str) -> str:
    """NFKC + case-fold + whitespace collapse. Never applied to identifiers."""
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def _tokens(normalized: str) -> set[str]:
    return {t for t in _WORD.findall(normalized)
            if len(t) >= MIN_TOKEN_LEN and t not in _STOPWORDS}


def _has_phrase(normalized_text: str, normalized_term: str) -> bool:
    """Whole-word / whole-phrase match (so 'will' does not match 'willing')."""
    if not normalized_term:
        return False
    pattern = r"(?<!\w)" + re.escape(normalized_term) + r"(?!\w)"
    return re.search(pattern, normalized_text) is not None


def _score(item: EvidenceItem, q_norm: str, q_tokens: set[str]) -> int:
    score = 0
    seen_terms: set[str] = set()
    for term in item.terms if isinstance(item.terms, list) else []:
        if type(term) is not str:
            continue
        t = _normalize(term)
        if t and t not in seen_terms:
            seen_terms.add(t)
            if _has_phrase(q_norm, t):
                score += TERM_WEIGHT
    if type(item.content) is str:
        score += CONTENT_WEIGHT * len(q_tokens & _tokens(_normalize(item.content)))
    return score


def _top_k_ok(top_k: object) -> bool:
    return type(top_k) is int and top_k >= 1


def _retrieve(question, permitted_evidence_ids, case, top_k) -> list[EvidenceItem]:
    if type(question) is not str or type(case) is not CaseState:
        return []
    if type(permitted_evidence_ids) is not list or not _top_k_ok(top_k):
        return []

    q_norm = _normalize(question[:MAX_QUESTION_CHARS])
    q_tokens = _tokens(q_norm)

    scored: list[tuple[int, str]] = []
    seen_ids: set[str] = set()
    for eid in permitted_evidence_ids:
        # IDs are exact, case-sensitive strings: no trimming, no case folding.
        if type(eid) is not str or eid in seen_ids:
            continue
        seen_ids.add(eid)
        item = case.evidence.get(eid)                 # unknown ID -> skipped
        if item is None:
            continue
        if type(item.reveal_at) is not int or item.reveal_at > case.progression:
            continue                                  # spoiler gate
        score = _score(item, q_norm, q_tokens)
        if score > 0:                                 # no match -> not returned
            scored.append((score, eid))

    scored.sort(key=lambda pair: (-pair[0], pair[1]))  # score desc, id asc
    results: list[EvidenceItem] = []
    for _, eid in scored[:top_k]:
        src = case.evidence[eid]
        # Fresh copy: callers can never alias or mutate the trusted case.
        results.append(EvidenceItem(
            evidence_id=src.evidence_id, content=src.content,
            fact_ids=list(src.fact_ids), reveal_at=src.reveal_at,
            terms=list(src.terms),
        ))
    return results


def retrieve_evidence(question: str, permitted_evidence_ids: list[str],
                      *, case: CaseState, top_k: int = 3) -> list[EvidenceItem]:
    """Return up to `top_k` relevant, permitted, already-revealed evidence items.

    Sorted by (score desc, evidence_id asc). An empty list is a valid answer.
    Bad input or any unexpected internal error fails closed with [].
    """
    try:
        return _retrieve(question, permitted_evidence_ids, case, top_k)
    except Exception:  # noqa: BLE001 - contract: retrieval must not break a turn
        return []
