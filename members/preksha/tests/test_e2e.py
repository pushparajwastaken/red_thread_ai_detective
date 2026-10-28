# """End-to-end tests (TC_E2E_*), source: case_engine.load_case(CASE_ID).

# Rules enforced (full pipeline, offline mock provider):
#  * load_case -> make_npc_context -> DialogueRequest -> generate_dialogue
#    -> validate_dialogue yields an accepted result for NPC 'rohan'.
#  * An accepted result: valid True, used_fallback False, Reason.OK in reasons,
#    citations drawn only from what the NPC is authorized to use.
#  * The pipeline never mutates the loaded case.
# The mock reply is scripted (term-free text, one authorized citation) so the
# test exercises the real generator parser and validator, not mock wording.
# Uses Richa's real case data, NOT the make_case_001() fixture.
# """
# import copy
# import json

# import pytest

# from shared.contracts import (
#     DialogueRequest, Reason, SAFE_FALLBACK_TEXT, TurnMetrics,
# )
# from case_engine import load_case, CASE_ID
# from validator import validate_dialogue
# from dialogue_generator import generate_dialogue, set_mock_script
# from conftest import make_npc_context

# REQUEST_ID = "req-e2e-rohan"


# @pytest.fixture(autouse=True)
# def _mock_provider(monkeypatch):
#     """Force the offline mock provider: no network, no Ollama."""
#     monkeypatch.setenv("LLM_PROVIDER", "mock")


# def _run(case, npc_id="rohan"):
#     npc = make_npc_context(case, npc_id)
#     facts = list(npc.authorized_fact_ids)[:1]
#     set_mock_script(REQUEST_ID, json.dumps({
#         "text": "I prefer to answer carefully.",
#         "cited_fact_ids": facts, "cited_evidence_ids": []}))
#     req = DialogueRequest(
#         npc_id=npc_id, question="Where were you last night?",
#         authorized_fact_ids=list(npc.authorized_fact_ids),
#         permitted_evidence_ids=list(npc.permitted_evidence_ids),
#         facts={f: case.canonical_facts[f] for f in npc.authorized_fact_ids},
#         evidence=[case.evidence[e] for e in npc.permitted_evidence_ids],
#         persona=npc.persona, request_id=REQUEST_ID)
#     draft = generate_dialogue(req)
#     return npc, draft, validate_dialogue(req, draft, case, npc)


# def test_TC_E2E_001_happy_path_is_accepted(mock_cleanup):
#     """rohan: generate -> validate gives valid, no fallback, OK."""
#     _, draft, result = _run(load_case(CASE_ID))
#     assert draft.status == "ok", f"draft.status={draft.status!r} ({draft.error})"
#     assert result.valid is True, f"reasons={result.reasons}"
#     assert result.used_fallback is False
#     assert Reason.OK in result.reasons, f"expected OK, got {result.reasons}"


# def test_TC_E2E_002_accepted_result_is_not_the_fallback(mock_cleanup):
#     """An accepted turn shows the draft text, not SAFE_FALLBACK_TEXT."""
#     _, draft, result = _run(load_case(CASE_ID))
#     assert result.npc_id == "rohan"
#     assert result.text == draft.text.strip(), "player text must be the draft"
#     assert result.text != SAFE_FALLBACK_TEXT


# def test_TC_E2E_003_citations_stay_inside_the_grant(mock_cleanup):
#     """Cited IDs are a subset of what rohan is authorized to use."""
#     npc, _, result = _run(load_case(CASE_ID))
#     assert result.valid is True, f"reasons={result.reasons}"
#     assert set(result.cited_fact_ids) <= set(npc.authorized_fact_ids), \
#         f"{result.cited_fact_ids} not within {npc.authorized_fact_ids}"
#     assert set(result.cited_evidence_ids) <= set(npc.permitted_evidence_ids)


# def test_TC_E2E_004_metrics_and_latency_are_consistent(mock_cleanup):
#     """Accepted result carries metrics; latency_ms == metrics.total_ms."""
#     _, _, result = _run(load_case(CASE_ID))
#     assert isinstance(result.metrics, TurnMetrics), f"got {result.metrics!r}"
#     assert result.latency_ms == result.metrics.total_ms
#     assert result.metrics.validation_ms > 0, "validation was not measured"


# def test_TC_E2E_005_pipeline_does_not_mutate_the_case(mock_cleanup):
#     """Running the pipeline leaves the loaded CaseState unchanged."""
#     case = load_case(CASE_ID)
#     before = copy.deepcopy(case)
#     _run(case)
#     assert case == before, "pipeline mutated CaseState"
#     assert case.progression == before.progression
