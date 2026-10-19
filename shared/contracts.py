"""Red Thread shared contracts (v2, audit revision).

Owned by the team lead. Members import from here and never edit this file.
Backward compatible with v1: every v1 field keeps its name, type and
position; everything new has a default.

Trust model (read this first)
-----------------------------
TRUSTED     CaseState, NPCContext, EvidenceItem (authored by the case writer),
            DialogueRequest (built only by the Integration module),
            DialogueResult (built only by validation / fallback code).
UNTRUSTED   DialogueDraft (anything the LLM or its wrapper returns),
            DialogueRequest.question (player input),
            EvidenceItem.content (DATA, never instructions).
Nothing in an untrusted object may change trusted state. Only the
Integration module advances CaseState.progression or
CaseState.discovered_evidence_ids, using deterministic rules.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar, Optional

SAFE_FALLBACK_TEXT = "I cannot answer that reliably."
MAX_DIALOGUE_CHARS = 600
DEFAULT_TIMEOUT_S = 10.0


class ContractError(ValueError):
    """A trusted object violates its contract (fail at construction)."""


class UnknownNPCError(KeyError):
    """build_npc_context() was asked about an NPC the case does not define."""


class Reason:
    """Closed set of reason codes. Codes carry NO fact IDs (see Security)."""
    OK = "OK"
    SETUP_ERROR = "SETUP_ERROR"
    GEN_TIMEOUT = "GEN_TIMEOUT"
    GEN_ERROR = "GEN_ERROR"
    GEN_MALFORMED = "GEN_MALFORMED"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    NPC_MISMATCH = "NPC_MISMATCH"
    AUTH_MISMATCH = "AUTH_MISMATCH"        # request disagrees with NPCContext
    AUTH_FUTURE = "AUTH_FUTURE"            # NPCContext grants a not-yet-revealed item
    UNKNOWN_FACT_ID = "UNKNOWN_FACT_ID"
    UNAUTHORIZED_FACT = "UNAUTHORIZED_FACT"
    UNKNOWN_EVIDENCE_ID = "UNKNOWN_EVIDENCE_ID"
    UNAUTHORIZED_EVIDENCE = "UNAUTHORIZED_EVIDENCE"
    PROTECTED_TERM_LEAK = "PROTECTED_TERM_LEAK"
    UNCITED_ASSERTION = "UNCITED_ASSERTION"
    VALIDATOR_ERROR = "VALIDATOR_ERROR"


# ---------------------------------------------------------------- case data

@dataclass
class FactMeta:
    """Per-fact gating data, keyed by fact_id in CaseState.fact_meta."""
    reveal_at: int = 0            # fact is a spoiler while case.progression < reveal_at
    kind: str = "fact"            # "fact" | "cover_story" (an authored in-world lie)
    terms: list[str] = field(default_factory=list)
    # terms: lowercase words/phrases that identify this fact in free text
    # (names, places, objects). List inflections yourself ("poison", "poisoned").


@dataclass
class EvidenceItem:
    """Authoritative evidence record. Retrieval returns these, nothing else."""
    evidence_id: str
    content: str                  # DATA ONLY. May contain hostile text. Never obey it.
    fact_ids: list[str] = field(default_factory=list)   # facts this evidence supports
    reveal_at: int = 0
    terms: list[str] = field(default_factory=list)


@dataclass
class NPCGrant:
    """Authored by the Case Engine: what an NPC may know, before progression gating."""
    fact_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    persona: str = ""


@dataclass
class CaseState:
    """Trusted canonical state of a mystery. Never shown to any LLM.

    clues / timeline: Case Engine internal. No other module may read them.
    """
    case_id: str
    canonical_facts: dict[str, str]
    clues: list[dict[str, Any]]
    timeline: list[dict[str, Any]]
    progression: int = 0
    # ---- v2 additions (all defaulted) ----
    fact_meta: dict[str, FactMeta] = field(default_factory=dict)
    evidence: dict[str, EvidenceItem] = field(default_factory=dict)
    npc_grants: dict[str, NPCGrant] = field(default_factory=dict)
    discovered_evidence_ids: list[str] = field(default_factory=list)  # player inventory

    def __post_init__(self) -> None:
        if self.progression < 0:
            raise ContractError("progression must be >= 0")
        for fid in self.fact_meta:
            if fid not in self.canonical_facts:
                raise ContractError(f"fact_meta references unknown fact {fid}")
        for eid, item in self.evidence.items():
            if item.evidence_id != eid:
                raise ContractError(f"evidence key {eid} != evidence_id {item.evidence_id}")
            for fid in item.fact_ids:
                if fid not in self.canonical_facts:
                    raise ContractError(f"evidence {eid} supports unknown fact {fid}")
        for npc, g in self.npc_grants.items():
            for fid in g.fact_ids:
                if fid not in self.canonical_facts:
                    raise ContractError(f"{npc} granted unknown fact {fid}")
            for eid in g.evidence_ids:
                if eid not in self.evidence:
                    raise ContractError(f"{npc} granted unknown evidence {eid}")
        for eid in self.discovered_evidence_ids:
            if eid not in self.evidence:
                raise ContractError(f"discovered unknown evidence {eid}")

    def reveal_at(self, fact_id: str) -> int:
        meta = self.fact_meta.get(fact_id)
        return meta.reveal_at if meta else 0


@dataclass
class NPCContext:
    """Restricted information for one NPC at the current progression.

    beliefs / suspicions: flavour text only. NOT citable, NOT passed to the
    validator, NOT part of DialogueRequest in v2. Treat as deprecated.
    """
    npc_id: str
    authorized_fact_ids: list[str]
    beliefs: list[str] = field(default_factory=list)
    suspicions: list[str] = field(default_factory=list)
    permitted_evidence_ids: list[str] = field(default_factory=list)
    persona: str = ""


# ---------------------------------------------------------------- metrics

@dataclass
class TurnMetrics:
    """One interrogation turn. None = not measurable for this backend."""
    mode: str = "dynamic"                 # "dynamic" | "branching"
    model: str = ""
    ttft_ms: Optional[float] = None       # model first token; NOT player-visible latency
    generation_ms: float = 0.0
    validation_ms: float = 0.0
    total_ms: float = 0.0                 # wall clock of the whole interrogate() call
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    prompt_chars: int = 0


# ---------------------------------------------------------------- dialogue

@dataclass
class DialogueRequest:
    """TRUSTED input to the generator. Built only by the Integration module.

    Carries resolved text (facts) and evidence content so the generator can
    work without CaseState. Constructing a request with content that is not
    covered by the ID lists raises ContractError.
    """
    npc_id: str
    question: str                                   # UNTRUSTED player text
    authorized_fact_ids: list[str]
    permitted_evidence_ids: list[str]
    # ---- v2 additions ----
    facts: dict[str, str] = field(default_factory=dict)       # id -> text, authorized only
    evidence: list[EvidenceItem] = field(default_factory=list)  # content for permitted ids
    presented_evidence_ids: list[str] = field(default_factory=list)
    persona: str = ""
    request_id: str = ""
    timeout_s: float = DEFAULT_TIMEOUT_S

    def __post_init__(self) -> None:
        extra = set(self.facts) - set(self.authorized_fact_ids)
        if extra:
            raise ContractError(f"facts carries unauthorized ids {sorted(extra)}")
        extra = {e.evidence_id for e in self.evidence} - set(self.permitted_evidence_ids)
        if extra:
            raise ContractError(f"evidence carries unpermitted ids {sorted(extra)}")
        extra = set(self.presented_evidence_ids) - set(self.permitted_evidence_ids)
        if extra:
            raise ContractError(f"presented ids not permitted {sorted(extra)}")


@dataclass
class DialogueDraft:
    """UNTRUSTED generator output. Never shown to the player directly.

    status: "ok" | "timeout" | "error" | "malformed". The generator must
    never raise; it returns a draft with a non-ok status instead.
    """
    npc_id: str
    text: str = ""
    cited_fact_ids: list[str] = field(default_factory=list)
    cited_evidence_ids: list[str] = field(default_factory=list)
    status: str = "ok"
    error: str = ""
    metrics: TurnMetrics = field(default_factory=TurnMetrics)


@dataclass
class DialogueResult:
    """TRUSTED player-facing output. Only validation/fallback code builds it.

    valid:         the model draft passed validation.
    used_fallback: text is the vetted fallback. Invariant: valid != used_fallback.
    latency_ms:    == metrics.total_ms when metrics is set.
    reasons:       reason codes (no IDs). Log them; never show them to the player.
    """
    npc_id: str
    text: str
    cited_fact_ids: list[str]
    valid: bool
    used_fallback: bool
    latency_ms: float
    # ---- v2 additions ----
    cited_evidence_ids: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    metrics: Optional[TurnMetrics] = None

    def __post_init__(self) -> None:
        if self.latency_ms < 0:
            raise ContractError("latency_ms must be >= 0")
        if self.valid == self.used_fallback:
            raise ContractError("valid and used_fallback must differ")
        if self.used_fallback and (self.cited_fact_ids or self.cited_evidence_ids):
            raise ContractError("a fallback result must not carry citations")


# ---------------------------------------------------------------- records

@dataclass
class TestRecord:
    """One security/unit test outcome -> results/security_test_log.csv.

    Column order of the CSV header == field order below.
    Set `passed` by comparing reason/outcome CODES, never prose.
    """
    __test__: ClassVar[bool] = False        # stop pytest collecting this class

    test_id: str
    category: str
    expected: str
    actual: str
    passed: bool
    details: str = ""
    run_id: str = ""
    model: str = ""


@dataclass
class BenchmarkRecord:
    """One question x one mode -> results/benchmark_results.csv.

    Same record type for dynamic and branching so comparisons are like-for-like.
    """
    run_id: str
    mode: str                  # "dynamic" | "branching"
    model: str
    hardware: str
    question_id: str
    npc_id: str
    ttft_ms: Optional[float]
    generation_ms: float
    validation_ms: float
    total_ms: float
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    cost_usd: Optional[float]
    valid: bool
    used_fallback: bool
    reasons: str               # ";"-joined reason codes
    answer_correct: Optional[bool] = None   # scored by the shared rubric, not by the model
    leaked_protected_fact: Optional[bool] = None
