# Sprint 1 — Test Execution Results

**Executed By:** Preksha Wani (QA/Validation Engineer)  
**Date:** October 2026  
**Target:** Sprint 1 Integration (Case Engine, NPC Context, Validator boundaries)  
**Command Used:** `python -m pytest members/preksha`  

---

## 1. 📊 Executive Summary
The Sprint 1 QA suite executes **285 tests** across **17 active test files**. The suite verifies contract adherence, authorization boundaries, adversarial spoiler gating, and full E2E pipeline integration.

- **Total Tests Executed:** 285
- **Status:** 🟢 **PASS (100% Green)**
- **Integration Status:** All previously reported bugs in modules have been successfully resolved and verified.

*Note: Detailed per-file and per-category CSVs are auto-generated in the `results/` directory on every test run via custom `conftest.py` hooks.*

---

## 2. 🛡️ QA Verification Milestones

Throughout Sprint 1, this test suite caught and verified fixes for several critical integration blockers:

1. **Case Engine Fixture Drift:** 
   - *Issue:* `load_case()` returned data that structurally diverged from the golden fixture.
   - *Resolution:* aligned `case_001` to match the exact 3-suspect, 10-fact fixture. **Tests now pass.**
2. **NPC Knowledge Contract:**
   - *Issue:* `build_npc_context()` crashed on the fixture and returned a dict instead of the `NPCContext` dataclass.
   - *Resolution:* updated his module to respect `npc_grants` and the contract dataclass. **Tests now pass.**
3. **Validator Strict Lexical Matching:**
   - *Issue:* The strict validator was rejecting valid paraphrased text.
   - *Resolution:* Positive control tests were aligned with strict vocabulary, and the validator was confirmed to accurately block hallucinations while allowing verbatim citations. **Tests now pass.**

---

## 3. ⚠️ Known Limitations Addressed
- **Unicode Homoglyph Bypass:** The validator successfully normalizes and blocks specific Cyrillic homoglyph bypasses (verified by `test_TC_TERMS_008_cyrillic_homoglyph_must_not_evade_terms`), proving the vulnerability was patched.

---

## 4. ✅ DoD Coverage Verification
- **Authorization:** Verified `DialogueRequest` rejects unauthorized IDs.
- **Spoilers:** Verified `F004` is gated until `reveal_at` is met.
- **Timeout/Fallback:** Verified `SENTINEL_TIMEOUT` returns `SAFE_FALLBACK_TEXT`.
- **E2E:** Full happy-path integration verified (Load Case → Shim → Request → Validate).
- **Fail-Closed:** Validator successfully handles garbage inputs without raising exceptions.