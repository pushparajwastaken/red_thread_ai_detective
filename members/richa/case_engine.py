"""
Case Engine Module
Owner: Richa Bharti

Responsible for loading mystery case data according
to the shared project contract.
"""

from shared.contracts import (
    CaseState,
    FactMeta,
    EvidenceItem,
    NPCGrant,
    ContractError,
)


def load_case(case_id: str) -> CaseState:
    """
    Loads a case and returns a CaseState object.

    Raises:
        ContractError if case does not exist.
    """

    if case_id != "CASE_001":
        raise ContractError(f"Unknown case id: {case_id}")

    canonical_facts = {
        "F001": "Victim was poisoned before death.",
        "F002": "Death occurred around 9 PM.",
        "F003": "Poison residue was found in a coffee cup.",
        "F004": "Rohan was seen near the victim's house.",
        "L001": "Rohan claims he never met the victim."
    }

    fact_meta = {
        "F001": FactMeta(
            reveal_at=0,
            kind="fact",
            terms=["victim", "poison", "poisoned"]
        ),
        "F002": FactMeta(
            reveal_at=1,
            kind="fact",
            terms=["9 pm", "time"]
        ),
        "F003": FactMeta(
            reveal_at=2,
            kind="fact",
            terms=["coffee", "cup", "poison"]
        ),
        "F004": FactMeta(
            reveal_at=2,
            kind="fact",
            terms=["rohan", "house"]
        ),
        "L001": FactMeta(
            reveal_at=0,
            kind="cover_story",
            terms=["never met", "alibi"]
        )
    }

    evidence = {
        "E001": EvidenceItem(
            evidence_id="E001",
            content="Lab report shows poison traces in the coffee cup.",
            fact_ids=["F003"],
            reveal_at=2,
            terms=["coffee", "poison"]
        ),

        "E002": EvidenceItem(
            evidence_id="E002",
            content="Camera footage shows Rohan near the victim's home.",
            fact_ids=["F004"],
            reveal_at=2,
            terms=["camera", "rohan"]
        )
    }

    npc_grants = {
        "NPC_ROHAN": NPCGrant(
            fact_ids=["L001"],
            evidence_ids=["E002"],
            persona="Nervous and defensive"
        ),

        "NPC_WITNESS": NPCGrant(
            fact_ids=["F002", "F004"],
            evidence_ids=["E002"],
            persona="Helpful witness"
        ),

        "NPC_FORENSIC": NPCGrant(
            fact_ids=["F001", "F003"],
            evidence_ids=["E001"],
            persona="Professional investigator"
        )
    }

    return CaseState(
        case_id="CASE_001",
        canonical_facts=canonical_facts,
        clues=[],
        timeline=[],
        progression=0,
        fact_meta=fact_meta,
        evidence=evidence,
        npc_grants=npc_grants,
        discovered_evidence_ids=["E001"]
    )