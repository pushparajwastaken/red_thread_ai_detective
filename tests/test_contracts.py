from shared.contracts import (
    CaseState,
    NPCContext,
    DialogueRequest,
    DialogueResult,
    TestRecord,
)


def test_case_state_contract():
    case = CaseState(
        case_id="case_001",
        canonical_facts={"F001": "A clue exists."},
        clues=[],
        timeline=[],
    )

    assert case.case_id == "case_001"
    assert "F001" in case.canonical_facts
    assert case.progression == 0


def test_npc_context_contract():
    npc = NPCContext(
        npc_id="gardener",
        authorized_fact_ids=["F002"],
        permitted_evidence_ids=["E001"],
    )

    assert npc.npc_id == "gardener"
    assert npc.authorized_fact_ids == ["F002"]
    assert npc.permitted_evidence_ids == ["E001"]


def test_dialogue_request_and_result_contract():
    request = DialogueRequest(
        npc_id="gardener",
        question="What did you see?",
        authorized_fact_ids=["F002"],
        permitted_evidence_ids=["E001"],
    )

    result = DialogueResult(
        npc_id=request.npc_id,
        text="I saw someone enter the garden.",
        cited_fact_ids=["F002"],
        valid=True,
        used_fallback=False,
        latency_ms=120.0,
    )

    assert result.npc_id == request.npc_id
    assert set(result.cited_fact_ids).issubset(
        set(request.authorized_fact_ids)
    )


def test_fallback_result_can_be_represented():
    result = DialogueResult(
        npc_id="gardener",
        text="I cannot answer that reliably.",
        cited_fact_ids=[],
        valid=False,
        used_fallback=True,
        latency_ms=20.0,
    )

    assert result.used_fallback is True


def test_test_record_contract():
    record = TestRecord(
        test_id="SEC-001",
        category="authorization",
        expected="Unauthorized fact rejected",
        actual="Unauthorized fact rejected",
        passed=True,
    )

    assert record.passed is True
