import pytest

from members.richa.case_engine import load_case
from shared.contracts import ContractError


def test_case_loads_successfully():
    case = load_case("CASE_001")

    assert case.case_id == "CASE_001"


def test_invalid_case_raises_error():
    with pytest.raises(ContractError):
        load_case("UNKNOWN")


def test_facts_exist():
    case = load_case("CASE_001")

    assert "F001" in case.canonical_facts
    assert "F002" in case.canonical_facts


def test_evidence_exists():
    case = load_case("CASE_001")

    assert "E001" in case.evidence
    assert "E002" in case.evidence


def test_npc_grants_exist():
    case = load_case("CASE_001")

    assert "NPC_ROHAN" in case.npc_grants