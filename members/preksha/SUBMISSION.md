# SUBMISSION — Sprint 1 QA & Validation Suite

**Author:** Preksha Wani  
**Role:** QA/Validation Engineer (Module 7)  
**Branch:** `feature/preksha-qa`  
**Commit SHA:** `21d8321`  
**Target Reviewer:** Pushparaj Singh Parmar (Integration Lead)  

---

## 1. 📦 Deliverables
This submission satisfies the Module 7 (Testing) DoD for Sprint 1.

**Inside my module folder (`members/preksha/`):**
- **`tests/`**: 17 Active Test Files containing **285 passing tests** covering authorization, spoiler gating, timeout, fallback, and E2E flows.
- **`conftest.py`**: Environment setup + `make_npc_context` shim + CSV reporting hooks.
- **`results/`**: Automated Reports (`summary.csv`, `summary.md`, `by_file/`, `by_category/`).

**Outside my module folder (Repository Root):**
- **`pytest.ini`**: Standardized test execution config (owned by the root).
- **`docs/bug_evidence/preksha`**: 2 archived files proving the bugs QA caught during Sprint 1.

---

## 2. 🏃 Execution Instructions
Dependencies: `pytest` (already in `requirements.txt`). No external APIs are called.
```bash
cd members/preksha
python -m pytest -v

## 3. ✅ Definition of Done (DoD) Checklist
- [x] Tests categories: `authorization`, `spoiler`, `unsupported_claim`, `malformed_output`, `validator_failure`, `timeout`, `fallback`, `e2e`.
- [x] Asserts `DialogueResult.reasons` and `used_fallback`, never relying solely on message text.
- [x] Tests exact, case-sensitive IDs (`F001`, `F004`, `E003`, `gardener`, `cook`).
- [x] Tests progression boundaries using `reveal_at`.
- [x] Tests are reproducible and submitted under `members/preksha/`.
- [x] Commands and actual results recorded in `RESULTS.md` and `results/` CSVs.
- [x] Tested against exact contract boundaries; central `tests/` and `shared/` untouched.

---

## 4. 🛡️ QA Verification & Bug Evidence (Resolved)
During Sprint 1, this test suite caught critical integration blockers. The exact scripts used to prove these bugs have been archived in `docs/bug_evidence/preksha` for the integration lead's review. **All bugs have been successfully resolved by the respective owners.**

1. **Case Engine:** `docs/bug_evidence/preksha/test_bug_case_engine_vs_fixture.py` — Documented the structural drift between `case_engine.py` and the golden fixture. (The active pipeline test `test_case_engine_load.py` now verifies the fixed data). **Status: Resolved.**
2. **NPC Knowledge:** `docs/bug_evidence/preksha/test_bug_npc_knowledge_vs_contract.py` — Documented the 3 contract violations in `build_npc_context()`. **Status: Resolved.**
3. **Validator:** Documented strict lexical matching issues and Unicode Homoglyph bypasses. **Status: Resolved** (validator now successfully catches TR39 confusables and handles strict citations).