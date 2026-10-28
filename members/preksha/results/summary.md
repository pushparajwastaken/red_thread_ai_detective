# Test Run Summary

**Run ID:** `20261028_204853`  
**Started:** 2026-10-28T20:48:53.362599  
**Duration:** 1.23s

## Overall

| Metric | Count |
|---|---|
| Total | 279 |
| ✅ Passed | 272 |
| ❌ Failed | 7 |
| ⏭ Skipped | 0 |

## By File

| File | Total | Passed | Failed |
|---|---|---|---|
| `test_authorization.py` | 11 | 11 | 0 |
| `test_bug_case_engine_vs_fixture.py` | 3 | 1 | 2 |
| `test_bug_npc_knowledge_vs_contract.py` | 3 | 0 | 3 |
| `test_case_engine_load.py` | 10 | 10 | 0 |
| `test_contracts.py` | 14 | 14 | 0 |
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

- **`test_bug_case_engine_vs_fixture.py::test_bug_npc_names_drift`** — AssertionError: NPC drift: engine ['aman', 'neha', 'rohan'] != fixture ['cook', 'gardener']
- **`test_bug_case_engine_vs_fixture.py::test_bug_evidence_set_drift`** — AssertionError: evidence drift: engine ['E001', 'E002', 'E003', 'E004', 'E005', 'E006', 'E007', 'E008', 'E009', 'E010', 'E011', 'E012'] != fixture ['E001', 'E003', 'E009']
- **`test_bug_npc_knowledge_vs_contract.py::test_TC_BUGANAND_001_npc_context_is_not_the_contract_type`** — AssertionError: npc_knowledge.NPCContext ((<class 'npc_knowledge.NPCContext'>, <class 'dict'>, <class 'object'>)) is not shared.contracts.NPCContext
- **`test_bug_npc_knowledge_vs_contract.py::test_TC_BUGANAND_002_unknown_npc_error_is_a_different_class`** — AssertionError: npc_knowledge.UnknownNPCError (id 1312673285920) is not shared.contracts.UnknownNPCError (id 1312716147168)
- **`test_bug_npc_knowledge_vs_contract.py::test_TC_BUGANAND_003_builder_rejects_the_golden_fixture`** — npc_knowledge.UnknownNPCError: 'Unknown NPC: gardener'
- **`test_validator_terms.py::test_TC_TERMS_008_cyrillic_homoglyph_must_not_evade_terms[gardener_protected]`** — AssertionError: expected PROTECTED_TERM_LEAK, got ['OK']
- **`test_validator_terms.py::test_TC_TERMS_008_cyrillic_homoglyph_must_not_evade_terms[cook_uncited]`** — AssertionError: expected UNCITED_ASSERTION, got ['OK']