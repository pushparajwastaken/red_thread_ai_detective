# Test Run Summary

**Run ID:** `20261027_021851`  
**Started:** 2026-10-27T02:18:51.023867  
**Duration:** 1.53s

## Overall

| Metric | Count |
|---|---|
| Total | 273 |
| ✅ Passed | 262 |
| ❌ Failed | 11 |
| ⏭ Skipped | 0 |

## By File

| File | Total | Passed | Failed |
|---|---|---|---|
| `test_authorization.py` | 11 | 11 | 0 |
| `test_case_engine_load.py` | 9 | 0 | 9 |
| `test_contracts.py` | 14 | 14 | 0 |
| `test_demo.py` | 1 | 1 | 0 |
| `test_fixture.py` | 16 | 16 | 0 |
| `test_make_fallback.py` | 37 | 37 | 0 |
| `test_malformed_output.py` | 26 | 26 | 0 |
| `test_npc_shim.py` | 14 | 14 | 0 |
| `test_progression.py` | 8 | 8 | 0 |
| `test_request_security.py` | 10 | 10 | 0 |
| `test_spoiler.py` | 13 | 13 | 0 |
| `test_timeout.py` | 7 | 7 | 0 |
| `test_unsupported_claim.py` | 9 | 9 | 0 |
| `test_validator_failclosed.py` | 52 | 52 | 0 |
| `test_validator_ids.py` | 14 | 14 | 0 |
| `test_validator_metrics.py` | 12 | 12 | 0 |
| `test_validator_terms.py` | 20 | 18 | 2 |

## Failures

- **`test_case_engine_load.py::test_TC_CASEENG_001_returns_case_state`** — shared.contracts.ContractError: Unknown case id: 'CASE_001'
- **`test_case_engine_load.py::test_TC_CASEENG_002_case_id_is_uppercase`** — shared.contracts.ContractError: Unknown case id: 'CASE_001'
- **`test_case_engine_load.py::test_TC_CASEENG_003_rohan_has_a_grant`** — shared.contracts.ContractError: Unknown case id: 'CASE_001'
- **`test_case_engine_load.py::test_TC_CASEENG_004_all_three_npcs_are_granted[NPC_ROHAN]`** — shared.contracts.ContractError: Unknown case id: 'CASE_001'
- **`test_case_engine_load.py::test_TC_CASEENG_004_all_three_npcs_are_granted[NPC_WITNESS]`** — shared.contracts.ContractError: Unknown case id: 'CASE_001'
- **`test_case_engine_load.py::test_TC_CASEENG_004_all_three_npcs_are_granted[NPC_FORENSIC]`** — shared.contracts.ContractError: Unknown case id: 'CASE_001'
- **`test_case_engine_load.py::test_TC_CASEENG_005_evidence_e001_and_e002_exist`** — shared.contracts.ContractError: Unknown case id: 'CASE_001'
- **`test_case_engine_load.py::test_TC_CASEENG_006_evidence_items_are_keyed_correctly[E001]`** — shared.contracts.ContractError: Unknown case id: 'CASE_001'
- **`test_case_engine_load.py::test_TC_CASEENG_006_evidence_items_are_keyed_correctly[E002]`** — shared.contracts.ContractError: Unknown case id: 'CASE_001'
- **`test_validator_terms.py::test_TC_TERMS_008_cyrillic_homoglyph_must_not_evade_terms[gardener_protected]`** — AssertionError: expected PROTECTED_TERM_LEAK, got ['OK']
- **`test_validator_terms.py::test_TC_TERMS_008_cyrillic_homoglyph_must_not_evade_terms[cook_uncited]`** — AssertionError: expected UNCITED_ASSERTION, got ['OK']