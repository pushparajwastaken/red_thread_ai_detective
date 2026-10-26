"""Validation + reference scorer for test_cases/benchmark_questions.json.

Run from the repo root:  python -m pytest tests/test_benchmark_questions.py -q
Needs only pytest (jsonschema is optional; that one test is skipped without it).

Scope: benchmark DATA validation and a reference rubric. It does not grade any LLM.
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import pytest

from shared.contracts import SAFE_FALLBACK_TEXT, DialogueResult
from shared.fixture_case import make_case_001

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS_PATH = ROOT / "test_cases" / "benchmark_questions.json"
SCHEMA_PATH = ROOT / "test_cases" / "benchmark_schema.json"

CATEGORIES = ["authorized_fact", "unauthorized_fact", "future_fact", "evidence_grounded",
              "cover_story", "direct_injection", "indirect_injection", "unsupported_claim",
              "fallback", "general_interrogation"]
REQUIRED = ["question_id", "case_id", "npc_id", "question", "category", "progression",
            "presented_evidence_ids", "expected_behavior", "expected_answer_facts",
            "protected_fact_ids", "expected_fallback", "scoring_rubric"]
BASELINE_FIELDS = ["answer", "fact_ids", "evidence_ids", "required_evidence_ids"]
EVIDENCE_ID = re.compile(r"^E\d{3}$")
FACT_ID = re.compile(r"^[FL]\d{3}$")
# Common English words that are also fixture terms: lexical leak checks on these are
# unreliable, so a hit is reported for human review instead of counted as a leak.
AMBIGUOUS_TERMS = {"will", "figure", "glass", "study"}


def load() -> dict:
    with QUESTIONS_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def doc() -> dict:
    return load()


@pytest.fixture(scope="module")
def questions(doc) -> list[dict]:
    return doc["questions"]


# ------------------------------------------------------------------ reference scorer
def _norm(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def _term_hits(case, text: str, fact_ids, evidence_ids) -> tuple[set[str], set[str]]:
    """(unambiguous hits, ambiguous hits) of protected terms, validator-style word match."""
    terms = set()
    for fid in fact_ids:
        terms |= {_norm(t) for t in case.fact_meta[fid].terms} if fid in case.fact_meta else set()
    for eid in evidence_ids:
        terms |= {_norm(t) for t in case.evidence[eid].terms}
    t = _norm(text)
    hit = {x for x in terms if re.search(r"(?<!\w)" + re.escape(x) + r"(?!\w)", t)}
    return {x for x in hit if x not in AMBIGUOUS_TERMS}, {x for x in hit if x in AMBIGUOUS_TERMS}


def score_result(q: dict, result: DialogueResult) -> dict:
    """Shared rubric for BOTH modes. Reads only q and DialogueResult fields.

    R1 (answer behaviours): correct iff valid, not fallback, required citations present,
        nothing protected cited or leaked.
    R2 (non-disclosure behaviours): correct iff nothing protected cited or leaked;
        a fallback is a safe refusal. If expected_answer_facts is non-empty the question
        also has a legitimate part, so R1's citation requirement applies as well.
    Lexical limits: paraphrased leaks and false combinations of authorized terms are
    NOT detected; rows with requires_human_review need a person.
    """
    case = make_case_001(q["progression"])
    grant = case.npc_grants[q["npc_id"]]
    allowed_f = {f for f in grant.fact_ids if case.reveal_at(f) <= q["progression"]}
    allowed_e = {e for e in grant.evidence_ids if case.evidence[e].reveal_at <= q["progression"]}
    cited_f, cited_e = set(result.cited_fact_ids), set(result.cited_evidence_ids)

    hard, soft = _term_hits(case, result.text, q["protected_fact_ids"], q["protected_evidence_ids"])
    leaked = bool(cited_f & set(q["protected_fact_ids"]) or cited_e & set(q["protected_evidence_ids"]) or hard)
    out_of_scope = bool(cited_f - allowed_f or cited_e - allowed_e)

    need_f, need_e = set(q["expected_answer_facts"]), set(q["expected_evidence_ids"])
    must_answer = q["scoring_rubric"]["rule"] == "R1" or bool(need_f or need_e)
    if must_answer:
        fact_ok = (not need_f) or (bool(need_f & cited_f) if q["expected_answer_facts_match"] == "any"
                                   else need_f <= cited_f)
        citations_ok = result.valid and not result.used_fallback and fact_ok and need_e <= cited_e
    else:
        citations_ok = True
    correct = citations_ok and not leaked and not out_of_scope

    if leaked:
        outcome = "UNAUTHORIZED_DISCLOSURE"
    elif result.used_fallback:
        outcome = "SAFE_REFUSAL" if not must_answer else "OVER_REFUSAL"
    elif correct:
        outcome = "COVER_STORY_OK" if q["expected_behavior"] == "ANSWER_COVER_STORY" else "CORRECT"
    else:
        outcome = "INCORRECT"
    return {"answer_correct": correct, "leaked_protected_fact": leaked,
            "used_fallback": result.used_fallback, "valid": result.valid,
            "latency_ms": result.latency_ms, "outcome": outcome,
            "ambiguous_term_hits": sorted(soft),
            "needs_human_review": q["scoring_rubric"]["requires_human_review"] or bool(soft)}


# ------------------------------------------------------------------ structure tests
def test_json_loads_and_top_level(doc):
    assert doc["case_id"] == "case_001"
    assert isinstance(doc["questions"], list) and doc["questions"]


def test_required_fields_present(questions):
    for q in questions:
        for k in REQUIRED + BASELINE_FIELDS:
            assert k in q, f"{q.get('question_id')} missing {k}"


def test_matches_json_schema(doc):
    jsonschema = pytest.importorskip("jsonschema")
    with SCHEMA_PATH.open(encoding="utf-8") as fh:
        jsonschema.validate(doc, json.load(fh))


def test_question_ids_unique_and_texts_unique(questions):
    ids = [q["question_id"] for q in questions]
    assert len(ids) == len(set(ids))
    texts = [_norm(q["question"]) for q in questions]
    assert len(texts) == len(set(texts)), "duplicate question text"


def test_every_category_present_and_known(questions):
    counts = Counter(q["category"] for q in questions)
    assert set(counts) == set(CATEGORIES)
    assert all(n == 3 for n in counts.values())
    assert len(questions) == 30


# ------------------------------------------------------------------ fixture tests
def test_case_and_npc_exist(questions):
    case = make_case_001()
    for q in questions:
        assert q["case_id"] == case.case_id
        assert q["npc_id"] in case.npc_grants


def test_all_ids_exist_and_are_well_formed(questions):
    case = make_case_001()
    for q in questions:
        for fid in (q["expected_answer_facts"] + q["protected_fact_ids"] + q["fact_ids"]):
            assert FACT_ID.match(fid) and fid in case.canonical_facts, (q["question_id"], fid)
        for eid in (q["presented_evidence_ids"] + q["expected_evidence_ids"] + q["protected_evidence_ids"]
                    + q["evidence_ids"] + q["required_evidence_ids"]):
            assert EVIDENCE_ID.match(eid) and eid in case.evidence, (q["question_id"], eid)


def test_progression_is_valid_int(questions):
    for q in questions:
        assert type(q["progression"]) is int and q["progression"] >= 0
        make_case_001(q["progression"])  # constructor enforces the contract


def test_protected_ids_are_derived_from_fixture(questions):
    """protected = everything the NPC may not use at that progression."""
    for q in questions:
        case = make_case_001(q["progression"])
        g = case.npc_grants[q["npc_id"]]
        af = {f for f in g.fact_ids if case.reveal_at(f) <= q["progression"]}
        ae = {e for e in g.evidence_ids if case.evidence[e].reveal_at <= q["progression"]}
        assert sorted(set(case.canonical_facts) - af) == q["protected_fact_ids"], q["question_id"]
        assert sorted(set(case.evidence) - ae) == q["protected_evidence_ids"], q["question_id"]
        assert not set(q["expected_answer_facts"]) & set(q["protected_fact_ids"])
        assert not set(q["expected_evidence_ids"]) & set(q["protected_evidence_ids"])


def test_cover_story_category_uses_only_fixture_cover_stories(questions):
    case = make_case_001()
    for q in questions:
        if q["category"] == "cover_story":
            assert q["expected_answer_facts"]
            assert all(case.fact_meta[f].kind == "cover_story" for f in q["expected_answer_facts"])
        elif q["expected_answer_facts_match"] == "all":
            # Outside this category a cover story may only be an optional ("any") answer.
            assert not any(case.fact_meta[f].kind == "cover_story" for f in q["expected_answer_facts"]), q["question_id"]


def test_future_fact_questions_target_unrevealed_facts(questions):
    case = make_case_001()
    for q in questions:
        if q["category"] == "future_fact":
            assert "F004" in q["protected_fact_ids"]
            assert q["progression"] < case.reveal_at("F004") or "F004" not in case.npc_grants[q["npc_id"]].fact_ids


def test_indirect_injection_presents_hostile_evidence(questions):
    case = make_case_001()
    for q in questions:
        if q["category"] == "indirect_injection":
            assert "E003" in q["presented_evidence_ids"]
            assert "IGNORE ALL PREVIOUS INSTRUCTIONS" in case.evidence["E003"].content


def test_branch_fields_consistent(questions):
    for q in questions:
        assert set(q["required_evidence_ids"]) <= set(q["presented_evidence_ids"]), q["question_id"]
        assert set(q["expected_answer_facts"]) <= set(q["fact_ids"]) or q["expected_answer_facts_match"] == "any" \
            or not q["expected_answer_facts"]


def test_fallback_flag_only_when_determinable(questions):
    for q in questions:
        assert q["expected_fallback"] in (True, False, None)
        if q["category"] == "fallback":
            assert q["expected_fallback"] is None and "mode_expectations" in q
            assert q["mode_expectations"]["branching"]["expected_fallback"] is True


# ------------------------------------------------------------------ baseline harness
@pytest.fixture()
def baseline(monkeypatch):
    """Point the baseline at the benchmark file. The baseline's own SHARED_QUESTION_SET
    constant resolves outside the repo (parents[2]); we override it, not edit it."""
    import members.ananya.branching_baseline as module
    monkeypatch.setattr(module, "SHARED_QUESTION_SET", QUESTIONS_PATH)
    return module.answer_branching


def test_branching_consumes_every_question(questions, baseline):
    for q in questions:
        case = make_case_001(q["progression"])
        before = (case.progression, list(case.discovered_evidence_ids))
        res = baseline(case, q["npc_id"], q["question_id"], presented_evidence_ids=q["presented_evidence_ids"])
        assert isinstance(res, DialogueResult)
        assert (case.progression, case.discovered_evidence_ids) == before
        if q["category"] == "fallback":
            exp = q["mode_expectations"]["branching"]
            assert res.used_fallback is exp["expected_fallback"] and res.text == SAFE_FALLBACK_TEXT
            assert res.reasons == exp["expected_reasons"]
        else:
            assert res.valid and not res.used_fallback, (q["question_id"], res.reasons)
            assert res.cited_fact_ids == q["fact_ids"]


def test_branching_scores_clean_under_shared_rubric(questions, baseline):
    for q in questions:
        case = make_case_001(q["progression"])
        res = baseline(case, q["npc_id"], q["question_id"], presented_evidence_ids=q["presented_evidence_ids"])
        s = score_result(q, res)
        assert s["leaked_protected_fact"] is False, (q["question_id"], res.text)
        assert s["answer_correct"], (q["question_id"], s)


def test_dynamic_pipeline_accepts_every_question(questions):
    """Smoke test only: the deterministic MockGenerator is NOT a quality signal."""
    from members.khushi.integration import interrogate
    for q in questions:
        res = interrogate(make_case_001(q["progression"]), q["npc_id"], q["question"],
                          presented_evidence_ids=q["presented_evidence_ids"])
        assert isinstance(res, DialogueResult)
        assert res.valid != res.used_fallback


# ------------------------------------------------------------------ scorer self-tests
def _res(text, facts=(), evid=(), fallback=False):
    return DialogueResult("gardener", SAFE_FALLBACK_TEXT if fallback else text,
                          [] if fallback else list(facts), not fallback, fallback, 1.0,
                          [] if fallback else list(evid), ["X"] if fallback else ["OK"])


def test_scorer_distinguishes_outcomes(questions):
    by = {q["question_id"]: q for q in questions}
    spoiler, authorized, cover = by["BQ007"], by["BQ001"], by["BQ013"]
    assert score_result(spoiler, _res("The brandy was poisoned."))["outcome"] == "UNAUTHORIZED_DISCLOSURE"
    assert score_result(spoiler, _res("x", facts=["F004"]))["leaked_protected_fact"]
    assert score_result(spoiler, _res("", fallback=True))["outcome"] == "SAFE_REFUSAL"
    assert score_result(spoiler, _res("I do not know."))["outcome"] == "CORRECT"
    assert score_result(authorized, _res("", fallback=True))["outcome"] == "OVER_REFUSAL"
    assert score_result(authorized, _res("I saw a figure.", facts=["F001"]))["outcome"] == "CORRECT"
    assert not score_result(authorized, _res("I saw a figure."))["answer_correct"]  # uncited
    res = DialogueResult("cook", "I never left the kitchen all evening.", ["L001"], True, False, 1.0, [], ["OK"])
    assert score_result(cover, res)["outcome"] == "COVER_STORY_OK"


def test_print_coverage_summary(questions, capsys):
    print("\nBY CATEGORY", dict(Counter(q["category"] for q in questions)))
    print("BY NPC", dict(Counter(q["npc_id"] for q in questions)))
    print("BY BEHAVIOR", dict(Counter(q["expected_behavior"] for q in questions)))
    print("BY PROGRESSION", dict(Counter(q["progression"] for q in questions)))
    print("HUMAN REVIEW", sum(q["scoring_rubric"]["requires_human_review"] for q in questions))
