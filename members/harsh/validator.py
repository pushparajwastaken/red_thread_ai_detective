"""Deterministic lexical validation for shared/contracts.py v2.

No LLM calls, state mutations, or semantic-truth judgements. The case and
NPC context establish authority; request/draft fields cannot enlarge it.
"""
from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import replace
from time import perf_counter

from shared.contracts import (
    CaseState, DialogueDraft, DialogueRequest, DialogueResult, EvidenceItem,
    FactMeta, MAX_DIALOGUE_CHARS, NPCContext, NPCGrant, Reason,
    SAFE_FALLBACK_TEXT, TurnMetrics,
)

_REASONS = frozenset(
    value for name, value in vars(Reason).items()
    if name.isupper() and type(value) is str and value != Reason.OK
)
_GEN_REASONS = {
    "timeout": Reason.GEN_TIMEOUT,
    "error": Reason.GEN_ERROR,
    "malformed": Reason.GEN_MALFORMED,
}


def _identifier(value: object) -> bool:
    # IDs are exact strings: never strip, case-fold, or repair them.
    return type(value) is str and bool(value)


def _ids(value: object) -> bool:
    return (type(value) is list and all(_identifier(v) for v in value)
            and len(value) == len(set(value)))


def _nonnegative_int(value: object) -> bool:
    return type(value) is int and value >= 0


def _number(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def _copy_metrics(value: object) -> TurnMetrics | None:
    """Reject malformed telemetry; never alias or trust a model-owned object."""
    if type(value) is not TurnMetrics:
        return None
    try:
        if type(value.mode) is not str or value.mode not in ("dynamic", "branching"):
            return None
        if type(value.model) is not str or not _nonnegative_int(value.prompt_chars):
            return None
        if not all(_number(getattr(value, k)) for k in
                   ("generation_ms", "validation_ms", "total_ms")):
            return None
        if not all(getattr(value, k) is None or _number(getattr(value, k))
                   for k in ("ttft_ms", "cost_usd")):
            return None
        if not all(getattr(value, k) is None or _nonnegative_int(getattr(value, k))
                   for k in ("prompt_tokens", "completion_tokens")):
            return None
        return replace(value)
    except Exception:
        return None


def make_fallback(npc_id: str, reasons: list[str],
                  metrics: TurnMetrics | None = None) -> DialogueResult:
    """Return a constant, citation-free reply even for malformed arguments."""
    safe_reasons: list[str] = []
    try:
        if type(reasons) is list:
            for reason in reasons:
                code = reason if type(reason) is str and reason in _REASONS else Reason.VALIDATOR_ERROR
                if code not in safe_reasons:
                    safe_reasons.append(code)
    except Exception:
        safe_reasons = [Reason.VALIDATOR_ERROR]
    safe_metrics = _copy_metrics(metrics)
    return DialogueResult(
        npc_id=npc_id if type(npc_id) is str else "",
        text=SAFE_FALLBACK_TEXT,
        cited_fact_ids=[], cited_evidence_ids=[],
        valid=False, used_fallback=True,
        latency_ms=safe_metrics.total_ms if safe_metrics is not None else 0.0,
        reasons=safe_reasons or [Reason.VALIDATOR_ERROR], metrics=safe_metrics,
    )


def _normalize(text: str) -> str:
    # Text normalization ONLY. IDs remain exact and case-sensitive.
    normalized = unicodedata.normalize("NFKC", text).casefold()
    # Fold common Cyrillic homoglyphs used to evade protected-term matching.
    normalized = normalized.replace("\u0456", "i")  # Cyrillic small letter і
    return " ".join(normalized.split())

def _terms(value: object) -> bool:
    return type(value) is list and all(type(t) is str and bool(_normalize(t)) for t in value)


def _trusted_shape(case: CaseState, npc: NPCContext) -> bool:
    """Validate only the public case fields; never read clues or timeline."""
    if type(case) is not CaseState or type(npc) is not NPCContext:
        return False
    if not _identifier(case.case_id) or not _identifier(npc.npc_id):
        return False
    if not _nonnegative_int(case.progression):
        return False
    if not _ids(npc.authorized_fact_ids) or not _ids(npc.permitted_evidence_ids):
        return False
    if type(case.canonical_facts) is not dict or not all(
        _identifier(k) and type(v) is str for k, v in case.canonical_facts.items()
    ):
        return False
    if type(case.fact_meta) is not dict or type(case.evidence) is not dict:
        return False
    for fid, meta in case.fact_meta.items():
        if (fid not in case.canonical_facts or type(meta) is not FactMeta
                or not _nonnegative_int(meta.reveal_at)
                or type(meta.kind) is not str or meta.kind not in ("fact", "cover_story")
                or not _terms(meta.terms)):
            return False
    for eid, item in case.evidence.items():
        if (not _identifier(eid) or type(item) is not EvidenceItem
                or type(item.evidence_id) is not str or item.evidence_id != eid
                or type(item.content) is not str or not _ids(item.fact_ids)
                or not set(item.fact_ids).issubset(case.canonical_facts)
                or not _nonnegative_int(item.reveal_at) or not _terms(item.terms)):
            return False
    if not _ids(case.discovered_evidence_ids) or not set(case.discovered_evidence_ids).issubset(case.evidence):
        return False
    if type(case.npc_grants) is not dict:
        return False
    for key, grant in case.npc_grants.items():
        if (not _identifier(key) or type(grant) is not NPCGrant
                or not _ids(grant.fact_ids) or not _ids(grant.evidence_ids)
                or not set(grant.fact_ids).issubset(case.canonical_facts)
                or not set(grant.evidence_ids).issubset(case.evidence)):
            return False
    return True


def _request_shape(request: DialogueRequest) -> bool:
    return (
        type(request) is DialogueRequest and _identifier(request.npc_id)
        and type(request.question) is str
        and _ids(request.authorized_fact_ids) and _ids(request.permitted_evidence_ids)
        and _ids(request.presented_evidence_ids)
        and type(request.facts) is dict
        and all(_identifier(k) and type(v) is str for k, v in request.facts.items())
        and type(request.evidence) is list
        and all(type(v) is EvidenceItem for v in request.evidence)
    )


def _authorization(request: DialogueRequest, case: CaseState, npc: NPCContext) -> list[str]:
    facts, evidence = set(npc.authorized_fact_ids), set(npc.permitted_evidence_ids)
    reasons: list[str] = []
    if not facts.issubset(case.canonical_facts) or not evidence.issubset(case.evidence):
        return [Reason.AUTH_MISMATCH]
    if (any(case.reveal_at(fid) > case.progression for fid in facts)
            or any(case.evidence[eid].reveal_at > case.progression for eid in evidence)):
        reasons.append(Reason.AUTH_FUTURE)
    if case.npc_grants:
        grant = case.npc_grants.get(npc.npc_id)
        if grant is None or not facts.issubset(grant.fact_ids) or not evidence.issubset(grant.evidence_ids):
            reasons.append(Reason.AUTH_MISMATCH)
    if (set(request.authorized_fact_ids) != facts
            or set(request.permitted_evidence_ids) != evidence):
        reasons.append(Reason.AUTH_MISMATCH)
    # Empty resolved payloads remain valid for legacy v1 callers. Present
    # payloads must be exact, authorized copies, never replacement authority.
    if any(fid not in facts or text != case.canonical_facts[fid]
           for fid, text in request.facts.items()):
        reasons.append(Reason.AUTH_MISMATCH)
    seen = set()
    for item in request.evidence:
        if (not _identifier(item.evidence_id) or item.evidence_id in seen
                or item.evidence_id not in evidence
                or item != case.evidence[item.evidence_id]):
            reasons.append(Reason.AUTH_MISMATCH)
            break
        seen.add(item.evidence_id)
    if (not set(request.presented_evidence_ids).issubset(evidence)
            or not set(request.presented_evidence_ids).issubset(case.discovered_evidence_ids)):
        reasons.append(Reason.AUTH_MISMATCH)
    return list(dict.fromkeys(reasons))


# ---------------------------------------------------------------- claim support
# Deterministic, LEXICAL claim-support check (added after audit finding UNSUP-03).
#
# A valid citation used to legitimize every other word in the same reply ("...at nine o'clock and it
# was the butler" passed). Now the reply must be accounted for by what it cites:
#   1. VOCABULARY  every token must be a closed-class/function word (_ALLOWED), a word of the NPC's
#                  trusted persona, or a word of an item the reply CITES (statement text + terms).
#                  Anything else is novel content -> unsupported.
#   2. GROUNDING   every sentence must either share a content word with a cited item, or be a
#                  recognised deflection (a negation plus a "know/say/tell/..." marker, e.g.
#                  "I cannot say anything reliable about that"). Pure-pronoun accusations ("He did it.")
#                  therefore fail.
#   3. REFLECTION  every cited item must be visible in the reply (shares a content word), so citations
#                  cannot be padded onto unrelated text.
#   4. POLARITY    a sentence that restates cited content may not negate it, nor drop the negation of
#                  a cited authored statement (e.g. the cover story "I never left the kitchen").
# Failure -> Reason.UNCITED_ASSERTION ("assertion not supported by its citations"; the closed Reason set
# has no separate code and shared/ is unchanged). Fail-closed by design: legitimate paraphrase that uses
# words absent from the cited statements will be rejected and replaced by the standard fallback.
#
# NOT hallucination prevention. Still undetected: reordered/recombined authorized words that change the
# meaning (e.g. swapped roles "Lord Ashby argued with Lady Ashby"), numerals/negation phrased with
# non-listed words, and anything expressible purely with function words plus cited words.
STRICT_SUPPORT = True
# Scope of the check. "grounded" (DEFAULT, contract-compatible): applies to any reply that cites an item or
# mentions a case term, so a citation can never lend credibility to extra claims, while pure small talk keeps
# the documented v2 behaviour "text with no case terms needs no citation". "all": applies the closed
# vocabulary to EVERY reply (closes term-free accusations such as "He did it." but rejects most free-form
# role-play); it changes agreed product behaviour, so it is OFF until the integration lead approves it.
SUPPORT_SCOPE = "grounded"

_ALLOWED = frozenset("""
a an the this that these those my your his her its our their some any every each all both such other another
more most much many few little i me mine myself you yours he him hers it we us they them who whom whose what
which where when why how am is are was were be been being do does did done doing have has had having will would
shall should can could may might must of in on at by for with from to into onto over under near about around
after before during until since through between among against upon within without and or but nor so yet if then
than as because while though although either neither not no never yes well oh hmm hm ah okay ok please sorry
indeed really just only also too very quite rather still even now here there again once say said tell told
know knew known think thought remember recall sure certain mean let ask answer answers question reliable
reliably anything something nothing everything one ones thing things way comment discuss talk cannot can't don't
didn't won't isn't wasn't wouldn't couldn't i'm i've i'd i'll it's that's there's what's let's
""".split())
_NEGATIONS = frozenset({"not", "no", "never", "nothing", "nobody", "none", "neither", "nor", "without", "cannot"})
_DEFLECT_VERBS = frozenset({"know", "say", "tell", "remember", "recall", "sure", "answer", "reliable", "reliably",
                            "comment", "discuss", "talk", "certain"})
_TOKEN = re.compile(r"[^\W_]+(?:'[^\W_]+)*")
_SENTENCES = re.compile(r"(?<=[.!?])\s+|[;\n]+")


def _toks(text: str) -> list[str]:
    return _TOKEN.findall(_normalize(text).replace("\u2019", "'"))


def _is_negation(tok: str) -> bool:
    return tok in _NEGATIONS or tok.endswith("n't")


def _support_check(text: str, npc: NPCContext, case: CaseState, cited_facts: list[str],
                   cited_evidence: list[str]) -> bool:
    """True iff every sentence of ``text`` is supported by the reply's own (authorized) citations."""
    statements: list[tuple[set[str], bool, set[str]]] = []   # (all words, negated?, reflection keys)
    for fid in cited_facts:
        stmt = case.canonical_facts[fid]
        meta = case.fact_meta.get(fid)                       # legacy cases may lack metadata
        fterms = list(meta.terms) if meta is not None else []
        words = set(_toks(stmt)) | {w for t in fterms for w in _toks(t)}
        keys = {w for t in fterms for w in _toks(t)} - _ALLOWED
        statements.append((words, any(_is_negation(w) for w in _toks(stmt)), keys or (words - _ALLOWED)))
    for eid in cited_evidence:
        item = case.evidence[eid]
        words = set(_toks(item.content)) | {w for t in item.terms for w in _toks(t)}
        keys = {w for t in item.terms for w in _toks(t)} - _ALLOWED
        statements.append((words, any(_is_negation(w) for w in _toks(item.content)), keys or (words - _ALLOWED)))
    cited_vocab = set().union(*(w for w, _, _ in statements)) if statements else set()
    vocab = _ALLOWED | set(_toks(npc.persona)) | cited_vocab

    text_tokens = set(_toks(text))
    for _, _, keys in statements:                                       # 3. REFLECTION (terms, not incidental words)
        if not (keys & text_tokens):
            return False
    saw_sentence = False
    for sentence in _SENTENCES.split(_normalize(text).replace("\u2019", "'")):
        toks = _TOKEN.findall(sentence)
        if not toks:
            if sentence.strip(" .!?,\"'-"):                              # punctuation-only is fine; stray symbols are not
                return False
            continue
        saw_sentence = True
        if any(t not in vocab for t in toks):                           # 1. VOCABULARY
            return False
        negated = any(_is_negation(t) for t in toks)
        grounded = bool(set(toks) & (cited_vocab - _ALLOWED))           # 2. GROUNDING
        if not grounded:
            if not (negated and set(toks) & _DEFLECT_VERBS):
                return False
            continue
        negs = [n for words, n, _ in statements if words & set(toks) - _ALLOWED]   # 4. POLARITY
        if negated and not any(negs):
            return False
        if not negated and negs and all(negs):
            return False
    return saw_sentence


def _check(request: DialogueRequest, draft: DialogueDraft,
           case: CaseState, npc: NPCContext) -> list[str]:
    if not _trusted_shape(case, npc):
        return [Reason.SETUP_ERROR]
    if not _request_shape(request) or type(draft) is not DialogueDraft:
        return [Reason.SCHEMA_INVALID]
    if not all(hasattr(draft, name) for name in
               ("npc_id", "text", "cited_fact_ids", "cited_evidence_ids", "status", "error", "metrics")):
        return [Reason.SCHEMA_INVALID]
    if type(draft.status) is not str or draft.status not in {"ok", *_GEN_REASONS}:
        return [Reason.SCHEMA_INVALID]
    if request.npc_id != npc.npc_id:
        return [Reason.NPC_MISMATCH]
    auth = _authorization(request, case, npc)
    if auth:
        return auth
    if draft.status != "ok":
        return [_GEN_REASONS[draft.status]]
    if (not _identifier(draft.npc_id) or type(draft.text) is not str
            or not draft.text.strip() or len(draft.text) > MAX_DIALOGUE_CHARS
            or not _ids(draft.cited_fact_ids) or not _ids(draft.cited_evidence_ids)
            or type(draft.error) is not str or _copy_metrics(draft.metrics) is None):
        return [Reason.SCHEMA_INVALID]
    if draft.npc_id != npc.npc_id:
        return [Reason.NPC_MISMATCH]
    reasons = []
    for fid in draft.cited_fact_ids:
        if fid not in case.canonical_facts:
            reasons.append(Reason.UNKNOWN_FACT_ID)
        elif fid not in npc.authorized_fact_ids or case.reveal_at(fid) > case.progression:
            reasons.append(Reason.UNAUTHORIZED_FACT)
    for eid in draft.cited_evidence_ids:
        if eid not in case.evidence:
            reasons.append(Reason.UNKNOWN_EVIDENCE_ID)
        elif eid not in npc.permitted_evidence_ids or case.evidence[eid].reveal_at > case.progression:
            reasons.append(Reason.UNAUTHORIZED_EVIDENCE)

    owners: dict[str, set[tuple[str, str]]] = {}
    for fid, meta in case.fact_meta.items():
        for term in meta.terms:
            owners.setdefault(_normalize(term), set()).add(("fact", fid))
    for eid, item in case.evidence.items():
        for term in item.terms:
            owners.setdefault(_normalize(term), set()).add(("evidence", eid))
    allowed = {
        ("fact", fid) for fid in npc.authorized_fact_ids
        if case.reveal_at(fid) <= case.progression
    } | {
        ("evidence", eid) for eid in npc.permitted_evidence_ids
        if case.evidence[eid].reveal_at <= case.progression
    }
    cited = ({("fact", fid) for fid in draft.cited_fact_ids}
             | {("evidence", eid) for eid in draft.cited_evidence_ids})
    text = _normalize(draft.text)
    term_visible = False
    for term, term_owners in owners.items():
        if not re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text):
            continue
        term_visible = True
        visible_owners = term_owners & allowed
        if not visible_owners:
            reasons.append(Reason.PROTECTED_TERM_LEAK)
        elif not (visible_owners & cited):
            reasons.append(Reason.UNCITED_ASSERTION)
    in_scope = (draft.cited_fact_ids or draft.cited_evidence_ids or term_visible or SUPPORT_SCOPE == "all")
    if STRICT_SUPPORT and in_scope and not reasons:
        # Only reached when every citation is known+authorized and no term rule fired, so the cited ids
        # below are safe to resolve from the trusted case.
        if not _support_check(draft.text, npc, case, list(draft.cited_fact_ids), list(draft.cited_evidence_ids)):
            reasons.append(Reason.UNCITED_ASSERTION)
    return list(dict.fromkeys(reasons))


def validate_dialogue(request: DialogueRequest, draft: DialogueDraft,
                      case: CaseState, npc: NPCContext) -> DialogueResult:
    """Return accepted dialogue or fail closed. Never propagate bad-input errors."""
    start = perf_counter()
    npc_id = ""
    metrics = None
    try:
        if type(npc) is NPCContext and _identifier(npc.npc_id):
            npc_id = npc.npc_id
        if type(draft) is DialogueDraft:
            metrics = _copy_metrics(getattr(draft, "metrics", None))
        reasons = _check(request, draft, case, npc)
        if metrics is not None:
            metrics.validation_ms = (perf_counter() - start) * 1000
        if reasons:
            return make_fallback(npc_id, reasons, metrics)
        return DialogueResult(
            npc_id=npc_id, text=draft.text,
            cited_fact_ids=list(draft.cited_fact_ids),
            cited_evidence_ids=list(draft.cited_evidence_ids),
            valid=True, used_fallback=False, reasons=[Reason.OK],
            latency_ms=metrics.total_ms, metrics=metrics,
        )
    except Exception:
        if metrics is not None:
            metrics.validation_ms = (perf_counter() - start) * 1000
        return make_fallback(npc_id, [Reason.VALIDATOR_ERROR], metrics)
