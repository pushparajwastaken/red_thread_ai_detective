# SUBMISSION — Module 7: Regression & Reference-Flow Tests
**Author:** Paras Gupta  
**Module:** 7 (Regression and Reference-Flow Tests)  
**Sprint:** 1 — Case Engine & Epistemic Schema

---

## Branch

```
paras/regression-tests
```

---

## Commit Instructions

After placing these files, commit with:
```bash
git add members/paras/
git commit -m "feat(paras): Module 7 — regression & reference-flow tests"
git push origin paras/regression-tests
```

---

## Files Submitted

| File | Purpose |
|---|---|
| `members/paras/sprint1/test_regression.py` | All regression and reference-flow tests (compact, parametrized) |
| `members/paras/sprint1/SUBMISSION.md` | This submission document |

---

## Dependencies

| Package | Version | In requirements.txt? |
|---|---|---|
| pytest | 9.0.3 | Yes |

No additional dependencies required. All imports are from `shared/`, `src/`, and `members/` only.

---

## Run Command

From the **repository root**:

```bash
python -m pytest members/paras/sprint1/test_regression.py -v
```

---

## Test Output (Actual)

```
============================= test session starts ==============================
platform win32 -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
configfile: pytest.ini
collected 48 items

members/paras/sprint1/test_regression.py::test_case_state_rejects_broken_references[negative_progression] PASSED
members/paras/sprint1/test_regression.py::test_case_state_rejects_broken_references[fact_meta_unknown_fact] PASSED
members/paras/sprint1/test_regression.py::test_case_state_rejects_broken_references[evidence_key_mismatch] PASSED
members/paras/sprint1/test_regression.py::test_case_state_rejects_broken_references[evidence_unknown_fact] PASSED
members/paras/sprint1/test_regression.py::test_case_state_rejects_broken_references[grant_unknown_fact] PASSED
members/paras/sprint1/test_regression.py::test_case_state_rejects_broken_references[grant_unknown_evidence] PASSED
members/paras/sprint1/test_regression.py::test_case_state_rejects_broken_references[discovered_unknown_evidence] PASSED
members/paras/sprint1/test_regression.py::test_case_state_defaults_and_valid_progression PASSED
members/paras/sprint1/test_regression.py::test_request_rejects_unauthorized_content[unauthorized_fact] PASSED
members/paras/sprint1/test_regression.py::test_request_rejects_unauthorized_content[unpermitted_evidence] PASSED
members/paras/sprint1/test_regression.py::test_request_rejects_unauthorized_content[presented_not_permitted] PASSED
members/paras/sprint1/test_regression.py::test_request_valid_edge_cases PASSED
members/paras/sprint1/test_regression.py::test_result_rejects_invalid_combinations[valid_and_fallback] PASSED
members/paras/sprint1/test_regression.py::test_result_rejects_invalid_combinations[neither_valid_nor_fallback] PASSED
members/paras/sprint1/test_regression.py::test_result_rejects_invalid_combinations[negative_latency] PASSED
members/paras/sprint1/test_regression.py::test_result_rejects_invalid_combinations[fallback_with_fact_citation] PASSED
members/paras/sprint1/test_regression.py::test_result_rejects_invalid_combinations[fallback_with_evidence_citation] PASSED
members/paras/sprint1/test_regression.py::test_result_valid_edge_cases_and_constants PASSED
members/paras/sprint1/test_regression.py::test_fixture_is_deterministic_and_progression_only_changes_progression PASSED
members/paras/sprint1/test_regression.py::test_fixture_grants_are_exact[gardener] PASSED
members/paras/sprint1/test_regression.py::test_fixture_grants_are_exact[cook] PASSED
members/paras/sprint1/test_regression.py::test_fixture_reveal_times_kinds_and_case_sensitive_ids PASSED
members/paras/sprint1/test_regression.py::test_fixture_security_data_and_integrity PASSED
members/paras/sprint1/test_regression.py::test_default_draft_and_metrics PASSED
members/paras/sprint1/test_regression.py::test_public_signature_matches_interfaces_md[load_case] PASSED
members/paras/sprint1/test_regression.py::test_public_signature_matches_interfaces_md[build_npc_context] PASSED
members/paras/sprint1/test_regression.py::test_public_signature_matches_interfaces_md[retrieve_evidence] PASSED
members/paras/sprint1/test_regression.py::test_public_signature_matches_interfaces_md[generate_dialogue] PASSED
members/paras/sprint1/test_regression.py::test_public_signature_matches_interfaces_md[validate_dialogue] PASSED
members/paras/sprint1/test_regression.py::test_public_signature_matches_interfaces_md[make_fallback] PASSED
members/paras/sprint1/test_regression.py::test_public_signature_matches_interfaces_md[interrogate] PASSED
members/paras/sprint1/test_regression.py::test_future_evidence_gate_in_retrieval[0-False] PASSED
members/paras/sprint1/test_regression.py::test_future_evidence_gate_in_retrieval[1-False] PASSED
members/paras/sprint1/test_regression.py::test_future_evidence_gate_in_retrieval[2-True] PASSED
members/paras/sprint1/test_regression.py::test_future_fact_gate_in_npc_context[0-False] PASSED
members/paras/sprint1/test_regression.py::test_future_fact_gate_in_npc_context[1-False] PASSED
members/paras/sprint1/test_regression.py::test_future_fact_gate_in_npc_context[2-True] PASSED
members/paras/sprint1/test_regression.py::test_validator_rejects_citation_of_ungranted_fact PASSED
members/paras/sprint1/test_regression.py::test_progression_only_moves_forward PASSED
members/paras/sprint1/test_regression.py::test_e2e_happy_path_invariants PASSED
members/paras/sprint1/test_regression.py::test_e2e_spoiler_never_leaks[0-gardener] PASSED
members/paras/sprint1/test_regression.py::test_e2e_spoiler_never_leaks[0-cook] PASSED
members/paras/sprint1/test_regression.py::test_e2e_spoiler_never_leaks[2-gardener] PASSED
members/paras/sprint1/test_regression.py::test_e2e_spoiler_never_leaks[2-cook] PASSED
members/paras/sprint1/test_regression.py::test_e2e_bad_input_falls_back_without_raising[Gardener-hi] PASSED
members/paras/sprint1/test_regression.py::test_e2e_bad_input_falls_back_without_raising[butler-hi] PASSED
members/paras/sprint1/test_regression.py::test_e2e_bad_input_falls_back_without_raising[gardener-None] PASSED
members/paras/sprint1/test_regression.py::test_e2e_questions_never_change_state PASSED

============================== 48 passed in 0.13s ==============================
```

**Result: 48 PASSED, 0 SKIPPED (0 FAILED)**

---

## Test Categories Covered

| Section | Category | Tests |
|---|---|---|
| 1 | CaseState contract integrity (parametrized: 7 rejection + 1 valid) | 8 |
| 2 | DialogueRequest contract (parametrized: 3 rejection + 1 valid) | 4 |
| 3 | DialogueResult contract + Reason codes (parametrized: 5 rejection + 1 valid) | 6 |
| 4 | Fixture determinism, grants, reveal gates, security data, defaults | 6 |
| 5 | Public signature verification (7 functions via parametrize) | 7 |
| 6 | Gates — actual implementation (evidence retrieval, NPC context, validator, progression) | 8 |
| 7 | End-to-end pipeline (happy path, spoiler leak, bad input, state immutability) | 9 |
| **Total** | | **48 passed** |

---

## Known Limits

1. **Lexical / data-only coverage.** These tests verify contract invariants, fixture data integrity, and progression-gated behavior. They do not cover live LLM outputs, hallucination detection, or runtime NPC dialogue — those are validated by the Validator module (Harsh) and the integration test suite.

2. **No `tests/test_reference_flow.py` was modified.** This file was not touched at any point.

3. **No `src/`, `shared/`, or other member folders were modified.** All work is isolated to `members/paras/`.

---

## Deferred to Sprint 2

- Add end-to-end regression tests over the full `interrogate()` pipeline once Integration (Pushparaj) is available.
- Cross-reference failing reason codes from the full suite to confirm Section 6 progression-gate logic aligns with live `retrieve_evidence()` and `build_npc_context()` filtering.
- Expand spoiler-leak tests with additional NPC/progression permutations.
