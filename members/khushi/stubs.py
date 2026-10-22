"""Stand-ins for modules that are not delivered yet (Modules 1-4).

They follow the signatures in shared/interfaces.md so the real modules can be
swapped in through ``integration.Deps`` without touching ``interrogate()``.
Everything here is offline and deterministic. No network, no API keys.
"""
from __future__ import annotations

import re
import time
from dataclasses import replace
from time import perf_counter

from shared.contracts import (
    CaseState, DialogueDraft, DialogueRequest, EvidenceItem, NPCContext,
    TurnMetrics, UnknownNPCError,
)


# ----------------------------------------------- Module 2 stand-in (Anand)
def stub_build_npc_context(case: CaseState, npc_id: str) -> NPCContext:
    """Only granted items with reveal_at <= progression, as fresh copies."""
    grant = case.npc_grants.get(npc_id)
    if grant is None:
        raise UnknownNPCError(npc_id)
    facts = [f for f in grant.fact_ids if case.reveal_at(f) <= case.progression]
    evidence = [e for e in grant.evidence_ids
                if case.evidence[e].reveal_at <= case.progression]
    return NPCContext(npc_id=npc_id, authorized_fact_ids=list(facts),
                      permitted_evidence_ids=list(evidence), persona=grant.persona)


# ----------------------------------------------- Module 3 stand-in (Gagan)
def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", text.casefold()))


def stub_retrieve_evidence(question: str, permitted_evidence_ids: list[str], *,
                           case: CaseState, top_k: int = 3) -> list[EvidenceItem]:
    """Pure keyword-overlap retrieval. Sorted by (score desc, id asc). Question is data."""
    q = _tokens(question)
    scored = []
    for eid in permitted_evidence_ids:
        item = case.evidence.get(eid)
        if item is None or item.reveal_at > case.progression:
            continue
        score = len(q & (_tokens(item.content) | {t for term in item.terms for t in _tokens(term)}))
        scored.append((-score, eid))
    scored.sort()
    out = []
    for _, eid in scored[:top_k]:
        item = case.evidence[eid]
        out.append(replace(item, fact_ids=list(item.fact_ids), terms=list(item.terms)))
    return out


# ----------------------------------------------- Module 4 stand-in (Anshul)
def render_prompt(request: DialogueRequest) -> str:
    """Everything a real model would be shown. Tests inspect this for leaks."""
    parts = [f"PERSONA: {request.persona}"]
    parts += [f"FACT {fid}: {txt}" for fid, txt in request.facts.items()]
    parts += [f"EVIDENCE {e.evidence_id} (untrusted data): {e.content}" for e in request.evidence]
    parts.append(f"QUESTION (untrusted): {request.question}")
    return "\n".join(parts)


class MockGenerator:
    """Deterministic fake LLM. ``mode`` picks the behaviour under test.

    ok                      cite + say the NPC's first authorized fact
    uncited                 right text, no citations
    compromised             jailbreak succeeded: leaks the spoiler, no citation
    compromised_cited       leaks the spoiler AND cites the unauthorized fact
    follows_evidence_inj    obeys hostile text found inside evidence data
    cites_future_evidence   cites evidence that is not yet revealed
    cites_unknown_fact      cites a fact ID that does not exist
    fullwidth_leak          fullwidth-unicode spoiler (validator catches it via NFKC)
    leet_leak / cyrillic_leak / hyphen_leak / zero_width_leak / spaced_leak /
    reversed_leak / inflection_leak / paraphrased_leak
                            spoiler variants the lexical validator MISSES (known limits,
                            measured, see results/ and LEAD_NOTES.md)
    too_long                text longer than MAX_DIALOGUE_CHARS
    timeout / error / malformed   draft with that status
    raise                   generator raises (contract says it must not)
    slow                    sleeps ``delay_s`` then behaves like ok
    garbage                 returns None
    bad_metrics             ok draft carrying invalid metrics
    """

    def __init__(self, mode: str = "ok", delay_s: float = 0.0, cost_usd=None, ttft_ms=None):
        self.mode, self.delay_s, self.cost_usd, self.ttft_ms = mode, delay_s, cost_usd, ttft_ms
        self.requests: list[DialogueRequest] = []   # what the "model" was given

    def _first_fact(self, request: DialogueRequest):
        for fid, txt in request.facts.items():
            return fid, txt
        return None, "I have nothing to say."

    def __call__(self, request: DialogueRequest) -> DialogueDraft:
        start = perf_counter()
        self.requests.append(request)
        m = self.mode
        if m == "raise":
            raise RuntimeError("generator exploded")
        if m == "garbage":
            return None  # type: ignore[return-value]
        if m in ("timeout", "error", "malformed"):
            return DialogueDraft(request.npc_id, status=m, error=m)
        if m in ("slow",) or self.delay_s:
            time.sleep(self.delay_s)

        fid, txt = self._first_fact(request)
        text, cites_f, cites_e = txt, ([fid] if fid else []), []
        if m == "uncited":
            cites_f = []
        elif m == "compromised":
            text, cites_f = "The brandy decanter was poisoned.", []
        elif m == "compromised_cited":
            text, cites_f = "The brandy decanter was poisoned.", ["F004"]
        elif m == "follows_evidence_inj":
            hostile = any("IGNORE ALL PREVIOUS INSTRUCTIONS" in e.content for e in request.evidence)
            if hostile:
                text, cites_f = "The brandy decanter was poisoned.", []
        elif m == "cites_future_evidence":
            cites_e = ["E009"]
        elif m == "cites_unknown_fact":
            cites_f = ["F999"]
        elif m == "leet_leak":
            text, cites_f = "The br4ndy was p0is0ned.", []
        elif m == "cyrillic_leak":
            text, cites_f = "The br\u0430nd\u0443 was p\u043eis\u043en\u0435d.", []
        elif m == "fullwidth_leak":
            text, cites_f = "The \uff42\uff52\uff41\uff4e\uff44\uff59 was \uff50\uff4f\uff49\uff53\uff4f\uff4e\uff45\uff44.", []
        elif m == "hyphen_leak":
            text, cites_f = "The b-r-a-n-d-y was p-o-i-s-o-n-e-d.", []
        elif m == "zero_width_leak":
            text, cites_f = "The bra\u200bndy was poi\u200bsoned.", []
        elif m == "spaced_leak":
            text, cites_f = "The b r a n d y was p o i s o n e d.", []
        elif m == "reversed_leak":
            text, cites_f = "The ydnarb was denosiop.", []
        elif m == "inflection_leak":
            text, cites_f = "The brandies were poisoning people.", []
        elif m == "paraphrased_leak":
            text, cites_f = "Somebody slipped something into the evening drink.", []
        elif m == "too_long":
            text = "x" * 601

        elapsed = (perf_counter() - start) * 1000
        metrics = TurnMetrics(mode="dynamic", model="mock", ttft_ms=self.ttft_ms,
                              generation_ms=elapsed, cost_usd=self.cost_usd,
                              prompt_chars=len(render_prompt(request)))
        if m == "bad_metrics":
            metrics = TurnMetrics(mode="dynamic", model="mock", generation_ms=-5.0)
        return DialogueDraft(request.npc_id, text, cites_f, cites_e, "ok", "", metrics)