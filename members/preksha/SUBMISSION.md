# SUBMISSION — Sprint 1 QA & Validation Suite

**Author:** Preksha Wani  
**Role:** QA/Validation Engineer (Module 7)  
**Branch:** `feature/preksha-qa`   

---

## 1. 📦 Deliverables
This submission satisfies the Module 7 (Testing) DoD for Sprint 1.
- **19 Test Files** containing 278 test cases covering authorization, spoiler gating, timeout, fallback, and E2E flows.
- **`conftest.py`** (Environment setup + `make_npc_context` shim + CSV reporting hooks).
- **`pytest.ini`** (Standardized test execution config).
- **Automated Reports** in `results/` (`summary.csv`, `summary.md`, `by_file/`, `by_category/`).

---

## 2. 🏃 Execution Instructions
Dependencies: `pytest` (already in `requirements.txt`). No external APIs are called; the test suite uses an offline mock provider.
```bash
cd members/preksha
python -m pytest -v