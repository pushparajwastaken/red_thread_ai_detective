# SUBMISSION — Module 7: Regression & Reference-Flow Tests
**Author:** Paras Gupta  
**Module:** 7 (Regression and Reference-Flow Tests)  
**Sprint:** 1 — Case Engine & Epistemic Schema



## Files Submitted

| File | Purpose |
|---|---|
| `members/paras/test_regression.py` | All regression and reference-flow tests |
| `members/paras/SUBMISSION.md` | This submission document |

---

## Dependencies

| Package | Version | In requirements.txt? |
|---|---|---|
| pytest | 9.0.3 | Yes |

No additional dependencies required. All imports are from `shared/` only.

---

## Run Command

From the **repository root**:

```bash
python -m pytest members/paras/test_regression.py -v
```

---

## Test Output (Actual)

```
============================== test session starts ==============================
platform win32 -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
configfile: pytest.ini
plugins: anyio-4.13.0
collected 67 items

members/paras/test_regression.py::TestCaseStateContract::test_valid_case_state_constructs_without_error PASSED
members/paras/test_regression.py::TestCaseStateContract::test_valid_case_state_at_higher_progression PASSED
members/paras/test_regression.py::TestCaseStateContract::test_negative_progression_raises_contract_error PASSED
members/paras/test_regression.py::TestCaseStateContract::test_fact_meta_key_not_in_canonical_facts_raises PASSED
members/paras/test_regression.py::TestCaseStateContract::test_evidence_key_mismatch_raises PASSED
members/paras/test_regression.py::TestCaseStateContract::test_evidence_referencing_unknown_fact_raises PASSED
members/paras/test_regression.py::TestCaseStateContract::test_npc_grant_referencing_unknown_fact_raises PASSED
members/paras/test_regression.py::TestCaseStateContract::test_npc_grant_referencing_unknown_evidence_raises PASSED
members/paras/test_regression.py::TestCaseStateContract::test_discovered_evidence_id_not_in_evidence_raises PASSED
members/paras/test_regression.py::TestCaseStateContract::test_empty_case_state_constructs_with_defaults PASSED
members/paras/test_regression.py::TestDialogueRequestContract::test_valid_dialogue_request_constructs PASSED
members/paras/test_regression.py::TestDialogueRequestContract::test_unauthorized_fact_in_facts_dict_raises PASSED
members/paras/test_regression.py::TestDialogueRequestContract::test_unpermitted_evidence_in_evidence_list_raises PASSED
members/paras/test_regression.py::TestDialogueRequestContract::test_presented_id_not_in_permitted_raises PASSED
members/paras/test_regression.py::TestDialogueRequestContract::test_empty_facts_evidence_presented_is_valid_edge_case PASSED
members/paras/test_regression.py::TestDialogueRequestContract::test_multiple_authorized_facts_all_included_is_valid PASSED
members/paras/test_regression.py::TestDialogueResultContract::test_valid_result_true_false PASSED
members/paras/test_regression.py::TestDialogueResultContract::test_valid_result_false_true PASSED
members/paras/test_regression.py::TestDialogueResultContract::test_both_valid_and_fallback_true_raises PASSED
members/paras/test_regression.py::TestDialogueResultContract::test_both_valid_and_fallback_false_raises PASSED
members/paras/test_regression.py::TestDialogueResultContract::test_negative_latency_raises PASSED
members/paras/test_regression.py::TestDialogueResultContract::test_zero_latency_is_valid PASSED
members/paras/test_regression.py::TestDialogueResultContract::test_fallback_with_cited_facts_raises PASSED
members/paras/test_regression.py::TestDialogueResultContract::test_fallback_with_cited_evidence_raises PASSED
members/paras/test_regression.py::TestDialogueResultContract::test_safe_fallback_text_exact_value PASSED
members/paras/test_regression.py::TestDialogueResultContract::test_reason_codes_are_correct_string_constants PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_make_case_001_called_twice_identical_facts PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_make_case_001_progression_parameter_changes_only_progression PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_f004_is_spoiler_at_progression_zero PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_f004_is_revealed_at_progression_two PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_e009_is_unrevealed_at_progression_zero PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_e009_is_revealed_at_progression_two PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_gardener_grant_includes_f001_f002 PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_cook_grant_includes_f003_l001 PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_gardener_evidence_grant PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_cook_has_no_evidence_grant PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_l001_is_cover_story_kind PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_f001_is_regular_fact_kind PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_case_sensitive_id_f001_vs_lowercase PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_case_sensitive_id_e001_vs_lowercase PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_discovered_evidence_ids_in_fixture PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_e003_is_hostile_injection_fixture PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_f004_terms_include_poison_variants PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_all_fact_meta_keys_exist_in_canonical_facts PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_all_evidence_keys_match_evidence_ids PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_npc_grant_fact_ids_exist_in_canonical_facts PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_npc_grant_evidence_ids_exist_in_evidence PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_dialogue_draft_defaults PASSED
members/paras/test_regression.py::TestDeterminismAndEdgeCases::test_turn_metrics_default_mode PASSED
members/paras/test_regression.py::TestReferenceFlowSignatures::test_load_case_signature SKIPPED
members/paras/test_regression.py::TestReferenceFlowSignatures::test_build_npc_context_signature SKIPPED
members/paras/test_regression.py::TestReferenceFlowSignatures::test_retrieve_evidence_signature SKIPPED
members/paras/test_regression.py::TestReferenceFlowSignatures::test_generate_dialogue_signature SKIPPED
members/paras/test_regression.py::TestReferenceFlowSignatures::test_validate_dialogue_signature SKIPPED
members/paras/test_regression.py::TestReferenceFlowSignatures::test_make_fallback_signature SKIPPED
members/paras/test_regression.py::TestReferenceFlowSignatures::test_interrogate_signature SKIPPED
members/paras/test_regression.py::TestProgressionBoundary::test_f004_unrevealed_boundary PASSED
members/paras/test_regression.py::TestProgressionBoundary::test_f004_exactly_at_reveal_boundary PASSED
members/paras/test_regression.py::TestProgressionBoundary::test_f001_always_revealed PASSED
members/paras/test_regression.py::TestProgressionBoundary::test_e009_unrevealed_at_progression_zero PASSED
members/paras/test_regression.py::TestProgressionBoundary::test_e009_revealed_at_progression_two PASSED
members/paras/test_regression.py::TestProgressionBoundary::test_e001_always_accessible PASSED
members/paras/test_regression.py::TestProgressionBoundary::test_e003_accessible_at_progression_zero PASSED
members/paras/test_regression.py::TestProgressionBoundary::test_reveal_at_helper_returns_zero_for_unknown_fact PASSED
members/paras/test_regression.py::TestProgressionBoundary::test_reveal_at_helper_returns_correct_value_for_f004 PASSED
members/paras/test_regression.py::TestProgressionBoundary::test_all_evidence_reveal_at_values_are_non_negative PASSED
members/paras/test_regression.py::TestProgressionBoundary::test_all_fact_meta_reveal_at_values_are_non_negative PASSED

========================= 64 passed, 3 skipped in 0.10s =========================
```

**Result: 64 PASSED, 3 SKIPPED (0 FAILED)**

---

## Test Categories Covered

| Section | Category | Count |
|---|---|---|
| 1 | CaseState contract integrity | 10 |
| 2 | DialogueRequest contract | 6 |
| 3 | DialogueResult contract + Reason codes | 10 |
| 4 | Determinism & edge cases | 23 |
| 5 | Reference-flow signatures (skip-guarded) | 7 skipped |
| 6 | Progression boundary regression | 11 |
| **Total** | | **64 passed, 7 skipped** |

---

## Known Limits

1. **Reference-flow signature tests (Section 5) are skipped** when a teammate's module is not yet importable. They will activate automatically once the implementation is placed at the expected module path (e.g., `members/richa/case_engine.py`). No test edits required.

2. **Lexical / data-only coverage.** These tests verify contract invariants and fixture data integrity. They do not cover live LLM outputs, hallucination detection, or runtime NPC dialogue — those are validated by the Validator module (Harsh) and the integration test suite.

3. **No `tests/test_reference_flow.py` was modified.** This file was not touched at any point.

4. **No `src/`, `shared/`, or other member folders were modified.** All work is isolated to `members/paras/`.

---

## Deferred to Sprint 2

- Activate and expand Section 5 (signature tests) once all module owners have committed their implementations.
- Add end-to-end regression tests over the full `interrogate()` pipeline once Integration (Pushparaj) is available.
- Cross-reference failing reason codes from the full suite to confirm Section 6 progression-gate logic aligns with live `retrieve_evidence()` and `build_npc_context()` filtering.
