# Sprint 1 — Test Execution Results & Bug Report

**Executed By:** Preksha Wani (QA/Validation Engineer)  
**Date:** October 2026  
**Target:** Sprint 1 (Case Engine, NPC Context, Validator boundaries)  
**Command Used:** `python -m pytest members/preksha/tests -v`

---

## 1. 📊 Executive Summary
The Sprint 1 QA suite executes **278 parametrized tests** across 19 files. The suite verifies contract adherence, authorization boundaries, adversarial spoiler gating, and full E2E pipeline integration.

- **Total Tests Collected:** 278
- **Status:** 🟢 **PASS** (Core logic & contracts) / 🔴 **BUGS FOUND** (Teammate implementations)
- **Intentional Failures:** `test_bug_case_engine_vs_fixture.py` and `test_bug_npc_knowledge_vs_contract.py` intentionally fail to provide signed bug evidence for the integration lead.

*Note: Detailed per-file and per-category CSVs are auto-generated in the `results/` directory on every test run via custom `conftest.py` hooks.*

---

## 2. 🐛 Bug Evidence (Action Required)

As per the Sprint 1 DoD, QA validates module boundaries. My suite discovered critical integration blockers in Richa's and Anand's modules. **No teammate files were edited to hide these bugs.**

### Bug 1: Case Engine Fixture Drift 
- **File:** `tests/test_bug_case_engine_vs_fixture.py`
- **Severity:** High (Integration Blocker)
- **Description:** `load_case(CASE_ID)` returns data that structurally diverges from the golden `make_case_001()` fixture.
- **Findings:**
  - `case_id` mismatch (`CASE_001` vs `case_001`).
  - NPC names mismatch (`NPC_ROHAN`, `NPC_WITNESS` vs `gardener`, `cook`).
  - Evidence IDs mismatch (`E001`, `E002` vs `E001`, `E003`, `E009`).
- **QA Resolution:** Updated `test_case_engine_load.py` and `test_e2e.py` to dynamically import `CASE_ID` from `case_engine.py` to prevent hardcoded dependency failures, while keeping the bug evidence isolated.

### Bug 2: NPC Knowledge Contract Violations
- **File:** `tests/test_bug_npc_knowledge_vs_contract.py`
- **Severity:** High (Contract Violation)
- **Description:** `build_npc_context()` fails on the golden fixture and breaks type expectations.
- **Findings:**
  1. Returns a `dict` subclass instead of `shared.contracts.NPCContext`.
  2. Defines a custom `UnknownNPCError` (breaks `pytest.raises` and integration exception handling).
  3. Raises an error on `gardener` because it searches for `case.npcs` instead of `case.npc_grants`.
- **Workaround:** QA implemented a `make_npc_context` shim in `conftest.py` to unblock testing of the Validator and E2E pipeline.

---

## 3. ⚠️ Known Limitations (Deferred)

### Unicode Homoglyph Bypass
- **Status:** Documented (Deferred to Sprint 12)
- **Description:** The validator does not normalize Unicode homoglyphs. A Cyrillic `і` (U+0456) in `"wіll"` bypasses the protected-term check.
- **DoD Alignment:** Module 5 DoD explicitly allows *"Known lexical limitations"*.
- **Mitigation:** Tested via `test_validator_terms.py`. The test asserts the *current* behavior (fails open) to prevent unexpected regressions and documents the exact limitation.

---

## 4. ✅ DoD Coverage Verification
- **Authorization:** Verified `DialogueRequest` rejects unauthorized IDs and cross-field tampering.
- **Spoilers:** Verified `F004` is gated until `reveal_at` progression is met.
- **Timeout/Fallback:** Verified `SENTINEL_TIMEOUT` correctly routes to `SAFE_FALLBACK_TEXT`.
- **E2E:** Full happy-path integration verified (Load Case → NPC Shim → Request → Generate → Validate).
- **Fail-Closed:** Validator successfully handles garbage inputs without raising unhandled exceptions.