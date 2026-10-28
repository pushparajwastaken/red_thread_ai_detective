"""Case Engine module.

The case's clues and ground-truth timeline are private authored data. Other
modules receive the shared CaseState contract, but must not inspect those fields.
"""

from __future__ import annotations

from shared.contracts import (
    CaseState,
    ContractError,
    EvidenceItem,
    FactMeta,
    NPCGrant,
)


CASE_ID = "case_001"
SUSPECT_IDS = {"aman", "neha", "rohan"}
VICTIM_ID = "lord_ashby"


def _build_case() -> CaseState:
    """Build a fresh copy of the authored case data for each load."""
    canonical_facts = {
        "F001": "A figure was seen near the greenhouse at nine o'clock.",
        "F002": "Glass broke in the study at half past nine.",
        "F003": "Neha argued with Lord Ashby about the will.",
        "F004": "The brandy decanter was poisoned with arsenic.",
        "F005": "Aman had a financial dispute with the victim.",
        "F006": "Neha was present in the office that night.",
        "F007": "The victim received a threat message.",
        "F008": "A security camera was disabled.",
        "F009": "A witness heard shouting before the death.",
        "F010": "Poison was purchased earlier that day.",
        "F011": "Rohan added arsenic to the decanter before 9:10 PM.",
        "L001": "Rohan claims, 'I never poisoned the brandy.'",
    }
    fact_meta = {
        "F001": FactMeta(0, "fact", ["figure", "figures", "greenhouse", "see", "saw", "seen"]),
        "F002": FactMeta(0, "fact", ["glass", "break", "broke", "broken", "study"]),
        "F003": FactMeta(0, "fact", ["neha", "lord ashby", "argue", "argued", "argues", "will"]),
        "F004": FactMeta(2, "fact", ["brandy", "decanter", "poison", "poisoned", "arsenic"]),
        "F005": FactMeta(0, "fact", ["aman", "financial", "dispute", "disputes", "victim"]),
        "F006": FactMeta(0, "fact", ["neha", "present", "presence", "office", "night"]),
        "F007": FactMeta(1, "fact", ["victim", "receive", "received", "threat", "threatened", "message"]),
        "F008": FactMeta(1, "fact", ["security", "camera", "disable", "disabled", "disabling"]),
        "F009": FactMeta(1, "fact", ["witness", "hear", "heard", "hearing", "shout", "shouting", "death"]),
        "F010": FactMeta(1, "fact", ["poison", "purchase", "purchased", "purchasing", "earlier", "day"]),
        "F011": FactMeta(2, "fact", ["rohan", "arsenic", "decanter", "add", "added", "adding"]),
        "L001": FactMeta(0, "cover_story", ["rohan", "never poisoned", "brandy"]),
    }
    evidence = {
        "E001": EvidenceItem(
            "E001", "A torn glove was found by the greenhouse door.",
            ["F001"], 0, ["torn", "glove", "greenhouse"],
        ),
        "E002": EvidenceItem(
            "E002", "A bank record documents Aman's financial dispute with Lord Ashby.",
            ["F005"], 0, ["bank", "record", "aman", "financial", "dispute"],
        ),
        "E003": EvidenceItem(
            "E003", "Glass fragments were recovered from the study floor.",
            ["F002"], 0, ["glass", "fragments", "study"],
        ),
        "E004": EvidenceItem(
            "E004", "The victim's phone contains a threat message received that evening.",
            ["F007"], 1, ["phone", "threat", "message", "received"],
        ),
        "E005": EvidenceItem(
            "E005", "Security logs show that the office camera was disabled.",
            ["F008"], 1, ["security", "logs", "office", "camera", "disabled"],
        ),
        "E006": EvidenceItem(
            "E006", "A witness statement reports shouting shortly before Lord Ashby's death.",
            ["F009"], 1, ["witness", "statement", "shouting", "death"],
        ),
        "E007": EvidenceItem(
            "E007", "A receipt confirms poison was purchased earlier on the day of the murder.",
            ["F010"], 1, ["receipt", "poison", "purchased", "earlier", "day"],
        ),
        "E008": EvidenceItem(
            "E008", "Lab tests confirm arsenic in the brandy decanter.",
            ["F004"], 2, ["lab", "tests", "arsenic", "brandy", "decanter"],
        ),
        "E009": EvidenceItem(
            "E009", "A glass fragment was recovered from the study.",
            ["F002"], 0, ["glass", "fragment", "study"],
        ),
        "E010": EvidenceItem(
            "E010", "A letter confirms Neha argued with Lord Ashby about the will.",
            ["F003"], 0, ["letter", "neha", "argued", "will"],
        ),
        "E011": EvidenceItem(
            "E011", "Rohan's prints were found on the poisoned decanter.",
            ["F011"], 2, ["rohan", "prints", "poisoned", "decanter"],
        ),
        "E012": EvidenceItem(
            "E012", "The office access log places Neha there on the night of the murder.",
            ["F006"], 0, ["office", "access", "log", "neha", "night"],
        ),
    }
    npc_grants = {
        "aman": NPCGrant(
            ["F001", "F005"], ["E001", "E002"], "A guarded business associate.",
        ),
        "neha": NPCGrant(
            ["F003", "F006"], ["E010", "E012"], "A composed office colleague.",
        ),
        "rohan": NPCGrant(
            ["F007", "F008", "F009", "F010", "L001"],
            ["E004", "E005", "E006", "E007"],
            "A precise and guarded steward.",
        ),
    }
    clues = [
        {"clue_id": "C001", "fact_ids": ["F001"], "evidence_ids": ["E001"], "suspect_ids": ["aman"]},
        {"clue_id": "C002", "fact_ids": ["F005"], "evidence_ids": ["E002"], "suspect_ids": ["aman"]},
        {"clue_id": "C003", "fact_ids": ["F006"], "evidence_ids": ["E012"], "suspect_ids": ["neha"]},
        {"clue_id": "C004", "fact_ids": ["F007"], "evidence_ids": ["E004"], "suspect_ids": ["aman", "neha", "rohan"]},
        {"clue_id": "C005", "fact_ids": ["F008"], "evidence_ids": ["E005"], "suspect_ids": ["aman", "neha", "rohan"]},
        {"clue_id": "C006", "fact_ids": ["F009"], "evidence_ids": ["E006"], "suspect_ids": ["aman", "neha", "rohan"]},
        {"clue_id": "C007", "fact_ids": ["F010"], "evidence_ids": ["E007"], "suspect_ids": ["aman", "neha", "rohan"]},
        {"clue_id": "C008", "fact_ids": ["F004", "F011"], "evidence_ids": ["E008", "E011"], "suspect_ids": ["rohan"]},
        {"clue_id": "C009", "fact_ids": ["F002"], "evidence_ids": ["E003", "E009"], "suspect_ids": ["aman", "neha", "rohan"]},
        {"clue_id": "C010", "fact_ids": ["F003"], "evidence_ids": ["E010"], "suspect_ids": ["neha"]},
    ]
    timeline = [
        {"event_id": "T001", "time_minute": 18 * 60, "event": "Poison is purchased earlier that day.", "victim_id": VICTIM_ID, "suspect_ids": ["rohan"]},
        {"event_id": "T002", "time_minute": 20 * 60, "event": "Aman has a financial dispute with Lord Ashby.", "victim_id": VICTIM_ID, "suspect_ids": ["aman"]},
        {"event_id": "T003", "time_minute": 20 * 60 + 20, "event": "Neha argues with Lord Ashby about the will.", "victim_id": VICTIM_ID, "suspect_ids": ["neha"]},
        {"event_id": "T004", "time_minute": 20 * 60 + 45, "event": "Lord Ashby receives a threat message.", "victim_id": VICTIM_ID, "suspect_ids": ["aman", "neha", "rohan"]},
        {"event_id": "T005", "time_minute": 20 * 60 + 55, "event": "Neha is present in the office that night.", "victim_id": VICTIM_ID, "suspect_ids": ["neha"]},
        {"event_id": "T006", "time_minute": 21 * 60, "event": "A figure is seen near the greenhouse at nine o'clock.", "victim_id": VICTIM_ID, "suspect_ids": ["aman"]},
        {"event_id": "T007", "time_minute": 21 * 60 + 5, "event": "The office security camera is disabled.", "victim_id": VICTIM_ID, "suspect_ids": ["rohan"]},
        {"event_id": "T008", "time_minute": 21 * 60 + 9, "event": "Rohan adds arsenic to the brandy decanter.", "victim_id": VICTIM_ID, "suspect_ids": ["rohan"]},
        {"event_id": "T009", "time_minute": 21 * 60 + 23, "event": "A witness hears shouting before the death.", "victim_id": VICTIM_ID, "suspect_ids": ["aman", "neha", "rohan"]},
        {"event_id": "T010", "time_minute": 21 * 60 + 30, "event": "Glass breaks in the study.", "victim_id": VICTIM_ID, "suspect_ids": ["rohan"]},
        {"event_id": "T011", "time_minute": 21 * 60 + 35, "event": "Lord Ashby dies of arsenic poisoning.", "victim_id": VICTIM_ID, "suspect_ids": ["rohan"]},
    ]
    return CaseState(
        case_id=CASE_ID,
        canonical_facts=canonical_facts,
        clues=clues,
        timeline=timeline,
        progression=0,
        fact_meta=fact_meta,
        evidence=evidence,
        npc_grants=npc_grants,
        discovered_evidence_ids=["E001", "E003"],
    )


def _validate_case(case: CaseState) -> None:
    """Validate fixture-specific rules not enforced by the shared dataclass."""
    if case.case_id != CASE_ID:
        raise ContractError(f"Invalid case fixture id: {case.case_id!r}")
    if set(case.canonical_facts) != set(case.fact_meta):
        raise ContractError("Every canonical fact must have exactly one fact_meta entry")
    for fact_id, meta in case.fact_meta.items():
        if meta.kind not in {"fact", "cover_story"}:
            raise ContractError(f"Invalid kind for {fact_id}: {meta.kind!r}")
        if meta.reveal_at < 0:
            raise ContractError(f"Invalid reveal_at for {fact_id}")
        if not meta.terms or any(
            not isinstance(term, str) or not term or term != term.lower()
            for term in meta.terms
        ):
            raise ContractError(f"Invalid terms for {fact_id}")
    if case.fact_meta.get("L001") is None or case.fact_meta["L001"].kind != "cover_story":
        raise ContractError("L001 must remain an authored cover_story")
    if set(case.npc_grants) != SUSPECT_IDS:
        raise ContractError("The case must define exactly the three authored suspects")
    if len(case.clues) != 10:
        raise ContractError("The case must contain exactly ten clues")
    clue_ids: list[str] = []
    for clue in case.clues:
        if not isinstance(clue, dict) or not isinstance(clue.get("clue_id"), str):
            raise ContractError("Every clue must have a string clue_id")
        clue_ids.append(clue["clue_id"])
        if not set(clue.get("fact_ids", [])).issubset(case.canonical_facts):
            raise ContractError(f"Clue {clue['clue_id']} references an unknown fact")
        if not set(clue.get("evidence_ids", [])).issubset(case.evidence):
            raise ContractError(f"Clue {clue['clue_id']} references unknown evidence")
        if not set(clue.get("suspect_ids", [])).issubset(case.npc_grants):
            raise ContractError(f"Clue {clue['clue_id']} references an unknown suspect")
    if len(clue_ids) != len(set(clue_ids)):
        raise ContractError("Clue IDs must be unique")

    event_ids: list[str] = []
    victim_ids: set[str] = set()
    previous_time = -1
    for event in case.timeline:
        if not isinstance(event, dict) or not isinstance(event.get("event_id"), str):
            raise ContractError("Every timeline event must have a string event_id")
        event_ids.append(event["event_id"])
        event_time = event.get("time_minute")
        if not isinstance(event_time, int) or event_time < previous_time:
            raise ContractError("Timeline events must have ordered integer times")
        previous_time = event_time
        victim_id = event.get("victim_id")
        if not isinstance(victim_id, str) or not victim_id:
            raise ContractError(f"Timeline event {event['event_id']} has no victim")
        victim_ids.add(victim_id)
        if not set(event.get("suspect_ids", [])).issubset(case.npc_grants):
            raise ContractError(f"Timeline event {event['event_id']} references an unknown suspect")
    if len(event_ids) != len(set(event_ids)):
        raise ContractError("Timeline event IDs must be unique")
    if victim_ids != {VICTIM_ID}:
        raise ContractError("The timeline must describe exactly one victim")


def load_case(case_id: str) -> CaseState:
    """Load the authored case, raising ContractError for unknown or invalid IDs."""
    if not isinstance(case_id, str) or case_id != CASE_ID:
        raise ContractError(f"Unknown case id: {case_id!r}")
    case = _build_case()
    _validate_case(case)
    return case
