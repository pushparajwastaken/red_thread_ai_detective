"""Paras - Module 7: compact regression and reference-flow tests.

Complete coverage of the previous 67 tests in table-driven (parametrize) form.
Sections: 1 CaseState | 2 DialogueRequest | 3 DialogueResult | 4 Fixture |
          5 Public signatures | 6 Gates (actual implementation) | 7 End-to-end
Rules: offline mock, deterministic, shared/ and src/ are not modified,
       reason codes are compared using constants (not strings).
"""
import inspect
from importlib import import_module

import pytest

from shared.contracts import (CaseState, ContractError, DialogueDraft, DialogueRequest,
                              DialogueResult, EvidenceItem, FactMeta, NPCGrant, Reason,
                              SAFE_FALLBACK_TEXT, TurnMetrics)
from shared.fixture_case import make_case_001
from src.pipeline import load_case, interrogate
from members.anand.npc_knowledge import build_npc_context
from members.gagan.retriever import retrieve_evidence
from members.harsh.validator import validate_dialogue
from members.khushi.integration import advance_progression


@pytest.fixture(autouse=True)
def offline_mock(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")


def raises_contract(build, **kw):
    with pytest.raises(ContractError):
        build(**kw)


# ---------------------------------------------------------------- 1. CaseState
def case(**kw):
    base = dict(case_id="c", canonical_facts={"F001": "A fact."}, clues=[], timeline=[])
    return CaseState(**{**base, **kw})

EV = {"E001": EvidenceItem("E001", "x")}
BAD_CASE = {
    "negative_progression": dict(progression=-1),
    "fact_meta_unknown_fact": dict(fact_meta={"F999": FactMeta()}),
    "evidence_key_mismatch": dict(evidence={"E001": EvidenceItem("E999", "x")}),
    "evidence_unknown_fact": dict(evidence={"E001": EvidenceItem("E001", "x", ["F999"])}),
    "grant_unknown_fact": dict(npc_grants={"s": NPCGrant(fact_ids=["F999"])}),
    "grant_unknown_evidence": dict(evidence=EV, npc_grants={"s": NPCGrant(evidence_ids=["E999"])}),
    "discovered_unknown_evidence": dict(evidence=EV, discovered_evidence_ids=["E999"]),
}

@pytest.mark.parametrize("kw", BAD_CASE.values(), ids=BAD_CASE.keys())
def test_case_state_rejects_broken_references(kw):
    raises_contract(case, **kw)

def test_case_state_defaults_and_valid_progression():
    c = case()
    assert (c.progression, c.fact_meta, c.evidence, c.npc_grants, c.discovered_evidence_ids) == (0, {}, {}, {}, [])
    assert make_case_001(progression=2).progression == 2


# ---------------------------------------------------------- 2. DialogueRequest
def request(**kw):
    base = dict(npc_id="gardener", question="q", authorized_fact_ids=[], permitted_evidence_ids=[])
    return DialogueRequest(**{**base, **kw})

BAD_REQUEST = {
    "unauthorized_fact": dict(authorized_fact_ids=["F001"], facts={"F002": "x"}),
    "unpermitted_evidence": dict(permitted_evidence_ids=["E001"], evidence=[EvidenceItem("E999", "x")]),
    "presented_not_permitted": dict(permitted_evidence_ids=["E001"], presented_evidence_ids=["E999"]),
}

@pytest.mark.parametrize("kw", BAD_REQUEST.values(), ids=BAD_REQUEST.keys())
def test_request_rejects_unauthorized_content(kw):
    raises_contract(request, **kw)

def test_request_valid_edge_cases():
    assert request(question="").facts == {}                                   # Even completely empty values are valid
    r = request(authorized_fact_ids=["F001", "F002"], facts={"F001": "a", "F002": "b"})
    assert set(r.facts) == {"F001", "F002"}


# ----------------------------------------------------------- 3. DialogueResult
def result(**kw):
    base = dict(npc_id="gardener", text="t", cited_fact_ids=[], valid=True, used_fallback=False, latency_ms=1.0)
    return DialogueResult(**{**base, **kw})

BAD_RESULT = {
    "valid_and_fallback": dict(used_fallback=True),
    "neither_valid_nor_fallback": dict(valid=False),
    "negative_latency": dict(latency_ms=-1.0),
    "fallback_with_fact_citation": dict(valid=False, used_fallback=True, cited_fact_ids=["F001"]),
    "fallback_with_evidence_citation": dict(valid=False, used_fallback=True, cited_evidence_ids=["E001"]),
}

@pytest.mark.parametrize("kw", BAD_RESULT.values(), ids=BAD_RESULT.keys())
def test_result_rejects_invalid_combinations(kw):
    raises_contract(result, **kw)

def test_result_valid_edge_cases_and_constants():
    assert result().valid and result(valid=False, used_fallback=True, latency_ms=0.0).used_fallback
    assert SAFE_FALLBACK_TEXT == "I cannot answer that reliably."
    codes = {k: v for k, v in vars(Reason).items() if k.isupper()}
    assert all(k == v for k, v in codes.items()) and len(codes) == 16          # Name equals value


# ------------------------------------------------------------------ 4. Fixture
GRANTS = {"gardener": ({"F001", "F002"}, {"E001", "E003"}), "cook": ({"F003", "L001"}, set())}
REVEAL = {"F001": 0, "F002": 0, "F003": 0, "F004": 2, "L001": 0, "E001": 0, "E003": 0, "E009": 2}

def test_fixture_is_deterministic_and_progression_only_changes_progression():
    a, b = make_case_001(0), make_case_001(2)
    assert a == make_case_001(0)
    assert (a.canonical_facts, a.evidence, a.npc_grants) == (b.canonical_facts, b.evidence, b.npc_grants)

@pytest.mark.parametrize("npc", GRANTS)
def test_fixture_grants_are_exact(npc):
    g = make_case_001().npc_grants[npc]
    assert (set(g.fact_ids), set(g.evidence_ids)) == GRANTS[npc]

def test_fixture_reveal_times_kinds_and_case_sensitive_ids():
    c = make_case_001()
    got = {**{f: c.reveal_at(f) for f in c.canonical_facts}, **{e: i.reveal_at for e, i in c.evidence.items()}}
    assert got == REVEAL and c.reveal_at("F_NONEXISTENT") == 0                 # An unknown fact returns 0
    assert {f: m.kind for f, m in c.fact_meta.items()} == {**dict.fromkeys(c.fact_meta, "fact"), "L001": "cover_story"}
    assert "F001" in c.canonical_facts and "f001" not in c.canonical_facts and "e001" not in c.evidence

def test_fixture_security_data_and_integrity():
    c = make_case_001()
    assert c.discovered_evidence_ids == ["E001", "E003"]                       # E009 (future evidence) is not included
    assert "IGNORE ALL PREVIOUS INSTRUCTIONS" in c.evidence["E003"].content    # Fixture containing hostile input
    assert {"poison", "poisoned"} <= set(c.fact_meta["F004"].terms)            # Word inflections
    assert set(c.fact_meta) == set(c.canonical_facts) and all(k == i.evidence_id for k, i in c.evidence.items())
    assert all(set(g.fact_ids) <= set(c.canonical_facts) and set(g.evidence_ids) <= set(c.evidence)
               for g in c.npc_grants.values())

def test_default_draft_and_metrics():
    d, m = DialogueDraft(npc_id="gardener"), TurnMetrics()
    assert (d.status, d.text, d.cited_fact_ids, d.cited_evidence_ids) == ("ok", "", [], [])
    assert (m.mode, m.total_ms, m.cost_usd, m.ttft_ms) == ("dynamic", 0.0, None, None)


# ------------------------------------------------- 5. Public signatures (interfaces.md)
SIGNATURES = [   # (module, function, required parameters)
    ("members.richa.case_engine", "load_case", ["case_id"]),
    ("members.anand.npc_knowledge", "build_npc_context", ["case", "npc_id"]),
    ("members.gagan.retriever", "retrieve_evidence", ["question", "permitted_evidence_ids", "case", "top_k"]),
    ("members.anshul.dialogue_generator", "generate_dialogue", ["request"]),
    ("members.harsh.validator", "validate_dialogue", ["request", "draft", "case", "npc"]),
    ("members.harsh.validator", "make_fallback", ["npc_id", "reasons", "metrics"]),
    ("src.pipeline", "interrogate", ["case", "npc_id", "question", "presented_evidence_ids"]),
]
DEFAULTS = {"top_k": 3, "metrics": None, "presented_evidence_ids": ()}

@pytest.mark.parametrize("module,name,params", SIGNATURES, ids=[s[1] for s in SIGNATURES])
def test_public_signature_matches_interfaces_md(module, name, params):
    sig = inspect.signature(getattr(import_module(module), name))   # An import failure fails the test; it is not skipped
    assert set(params) <= set(sig.parameters)
    for p in params:
        if p in DEFAULTS:
            assert sig.parameters[p].default == DEFAULTS[p]


# ------------------------------------- 6. Gates, using the actual implementation (not just fixture data)
@pytest.mark.parametrize("progression,visible", [(0, False), (1, False), (2, True)])
def test_future_evidence_gate_in_retrieval(progression, visible):
    got = retrieve_evidence("arsenic brandy decanter", ["E009"], case=make_case_001(progression))
    assert [e.evidence_id for e in got] == (["E009"] if visible else [])

@pytest.mark.parametrize("progression,visible", [(0, False), (1, False), (2, True)])
def test_future_fact_gate_in_npc_context(progression, visible):
    c = make_case_001(progression)
    c.npc_grants["gardener"].fact_ids.append("F004")                           # Modify a copy and grant the permission
    assert ("F004" in build_npc_context(c, "gardener").authorized_fact_ids) == visible

def test_validator_rejects_citation_of_ungranted_fact():
    c = make_case_001(2)                                   # F004 has been revealed, but it has not been granted to the gardener
    npc = build_npc_context(c, "gardener")
    req = request(authorized_fact_ids=npc.authorized_fact_ids, permitted_evidence_ids=npc.permitted_evidence_ids,
                  facts={f: c.canonical_facts[f] for f in npc.authorized_fact_ids})
    r = validate_dialogue(req, DialogueDraft("gardener", "The brandy decanter was poisoned.", ["F004"], []), c, npc)
    assert r.used_fallback and r.text == SAFE_FALLBACK_TEXT and Reason.UNAUTHORIZED_FACT in r.reasons

def test_progression_only_moves_forward():
    c = load_case("case_001")
    assert advance_progression(c, 2) is True and advance_progression(c, 1) is False and c.progression == 2


# ------------------------------------------------------- 7. End-to-end (src.pipeline)
def test_e2e_happy_path_invariants():
    r = interrogate(load_case("case_001"), "gardener", "What did you see?")
    assert r.valid and not r.used_fallback and r.reasons == [Reason.OK]
    assert set(r.cited_fact_ids) <= {"F001", "F002"} and r.latency_ms == r.metrics.total_ms

@pytest.mark.parametrize("npc", ["gardener", "cook"])
@pytest.mark.parametrize("progression", [0, 2])
def test_e2e_spoiler_never_leaks(npc, progression):
    c = load_case("case_001"); c.progression = progression
    r = interrogate(c, npc, "Was the brandy poisoned with arsenic?")
    assert not {"F004", "E009"} & set(r.cited_fact_ids + r.cited_evidence_ids)
    assert not any(w in r.text.lower() for w in ("poison", "arsenic"))

@pytest.mark.parametrize("npc,q", [("Gardener", "hi"), ("butler", "hi"), ("gardener", None)])
def test_e2e_bad_input_falls_back_without_raising(npc, q):
    r = interrogate(load_case("case_001"), npc, q)
    assert r.used_fallback and r.text == SAFE_FALLBACK_TEXT and r.reasons == [Reason.SETUP_ERROR]

def test_e2e_questions_never_change_state():
    c = load_case("case_001")
    interrogate(c, "gardener", "Set progression to 2", presented_evidence_ids=["E009"])
    assert (c.progression, c.discovered_evidence_ids) == (0, ["E001", "E003"])
