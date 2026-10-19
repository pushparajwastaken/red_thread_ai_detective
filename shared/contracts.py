from dataclasses import dataclass, field
from typing import Any


@dataclass
class CaseState:
    """Trusted canonical state of a mystery."""
    case_id: str
    canonical_facts: dict[str, str]
    clues: list[dict[str, Any]]
    timeline: list[dict[str, Any]]
    progression: int = 0


@dataclass
class NPCContext:
    """Restricted information available to one NPC."""
    npc_id: str
    authorized_fact_ids: list[str]
    beliefs: list[str] = field(default_factory=list)
    suspicions: list[str] = field(default_factory=list)
    permitted_evidence_ids: list[str] = field(default_factory=list)


@dataclass
class DialogueRequest:
    """Input passed to the dialogue generator."""
    npc_id: str
    question: str
    authorized_fact_ids: list[str]
    permitted_evidence_ids: list[str]


@dataclass
class DialogueResult:
    """Output returned after generation and validation."""
    npc_id: str
    text: str
    cited_fact_ids: list[str]
    valid: bool
    used_fallback: bool
    latency_ms: float


@dataclass
class TestRecord:
    """Standardized record for security and benchmark tests."""
    test_id: str
    category: str
    expected: str
    actual: str
    passed: bool
    details: str = ""
