# Red Thread — Sprint 1 QA & Validation Suite

**Owner:** Preksha Wani (QA/Validation Engineer)  
**Sprint:** 1 — Case Engine & Epistemic Schema  
**Scope:** Contract enforcement, authorization boundaries testing.

## 📖 Overview
This directory contains the automated test suite for the Red Thread AI Detective game. The suite ensures that the deterministic Case Engine, the NPC Knowledge module, and the Dialogue Validator strictly adhere to the `shared/contracts.py` rulebook. It prevents unauthorized fact disclosure, enforces timeline gating, and ensures the LLM fails closed.

## 📊 Test Reporting
Every time you run `pytest`, the `conftest.py` automatically generates CSV and Markdown reports in the `results/` directory.
- View `results/summary.md` for a human-readable breakdown.
- View `results/by_category/` to see tests grouped by DoD requirements.
- View `results/by_file/` for isolated test module reports.

## 🚀 Quick Start

```bash
# Navigate to the test directory
cd members/preksha
```
```bash
# Run the full suite
python -m pytest
```

## 📁 Folder Structure

```text
members/preksha/
├── conftest.py                    # Environment setup, shims, and CSV reporting hooks
├── pytest.ini                     # Pytest configuration (verbose, short tracebacks)
├── README.md                      # Test suite documentation
├── terminal_log.txt               # Captured test execution output (evidence)
├── data/                          # Placeholder for local test data
├── results/                       # Auto-generated test reports (CSV & Markdown)
│   ├── latest_run.txt             # Quick reference of the latest test run stats
│   ├── summary.csv                # Master CSV of all test results
│   ├── summary.md                 # Human-readable summary for Sprint Review
│   ├── by_category/               # CSVs aggregated by DoD test categories
│   ├── by_file/                   # CSVs containing per-test-file results
│   └── logs/                      # Raw run logs (if captured via script)
└── tests/                         # 17 test files mapped to DoD requirements
    ├── test_authorization.py      # Rejects unauthorized facts/evidence
    ├── test_case_engine_load.py   # Verifies CASE_ID loading logic
    ├── test_contracts.py          # Validates trusted/untrusted boundaries
    ├── test_demo.py               # Basic sanity checks
    ├── test_fixture.py            # Verifies fixture invariant structure
    ├── test_make_fallback.py      # Tests SAFE_FALLBACK_TEXT generation
    ├── test_malformed_output.py   # Tests SCHEMA_INVALID handling
    ├── test_npc_shim.py           # Tests the contract-compliant NPC shim
    ├── test_progression.py        # Tests reveal_at spoiler gating
    ├── test_request_security.py   # Tests DialogueRequest post-init invariants
    ├── test_spoiler.py            # Catches unauthorized fact citation
    ├── test_timeout.py            # Tests GEN_TIMEOUT handling
    ├── test_unsupported_claim.py  # Catches uncited protected terms
    ├── test_validator_failclosed.py # Ensures validator never raises
    ├── test_validator_ids.py      # Tests case-sensitive ID enforcement
    ├── test_validator_metrics.py  # Tests validation timing metrics
    ├── test_validator_terms.py    # Tests word boundary and homoglyphs
    ├── test_bug_case_engine_vs_fixture.py # INTENTIONAL case drift evidence
    ├── test_bug_npc_knowledge_vs_contract.py # INTENTIONAL contract violations
    

```

### 🧪 Test Coverage Map (Sprint 1 DoD)

| DoD Category | Test File(s) | Purpose |
| :--- | :--- | :--- |
| **Authorization** | `test_authorization.py`, `test_request_security.py` | Ensures `DialogueRequest` rejects unauthorized facts/evidence. |
| **Spoiler Gating** | `test_spoiler.py`, `test_progression.py` | Blocks future facts (`F004`) until `reveal_at` progression is met. |
| **Unsupported Claim** | `test_unsupported_claim.py`, `test_validator_terms.py` | Catches protected terms leaked in prose without citations. |
| **Malformed Output** | `test_malformed_output.py` | Ensures invalid LLM JSON returns `SCHEMA_INVALID`. |
| **Validator Failure** | `test_validator_failclosed.py` | Verifies the validator never raises exceptions on garbage input. |
| **Timeout/Fallback** | `test_timeout.py`, `test_make_fallback.py` | Tests generator timeouts and verifies `SAFE_FALLBACK_TEXT`. |
| **Bug Evidence** *(Intentional Fail)* | `test_bug_case_engine_vs_fixture.py`<br>`test_bug_npc_knowledge_vs_contract.py` | **Signed evidence** of integration blockers  |
| **E2E Pipeline** | `test_e2e.py` | Full integration test from Case Loading to Dialogue Validation. |



## ⚠️ Known Limitations & Deferred Edge Cases

### 1. Unicode Homoglyph Bypass (Deferred to Sprint 12)

**Status:** 🔴 Documented Limitation (Not a Sprint 1 Blocker)

#### 📝 Description
A **Unicode Homoglyph Attack** occurs when an attacker (or a malicious LLM prompt) uses visually identical characters from different alphabets to bypass text filters. 
- **Target:** The protected term `"will"` (belonging to Fact `F003`).
- **Attack:** Using a Cyrillic `і` (U+0456) instead of a Latin `i` (U+0069) to spell `"wіll"`. 
- **Result:** The text looks identical to a human reader, but it bypasses the validator's protected-term check.

#### 🔍 Technical Root Cause
The current validator does a standard string match. While it may apply basic normalization, **standard Unicode NFKC normalization does not map Cyrillic characters to their Latin visual equivalents**. Because `"wіll"` (Cyrillic) is technically a different string than `"will"` (Latin), the validator returns `['OK']` instead of raising `PROTECTED_TERM_LEAK`.

#### 📜 DoD Alignment (Why this is not a Sprint 1 Bug)
Per **Sprint1Plan.md (Module 5 — Validator)**:
> *"Known lexical limitations are documented; no claim of complete hallucination prevention is made."*

Fixing this requires advanced adversarial hardening (Unicode TR39 "Confusables" skeleton mapping), which is explicitly scheduled for **MVP3 (Sprint 12: H12 Adversarial Hardening)**. Blocking Sprint 1 for this edge case would violate the agreed project scope.

#### 🛡️ Current Mitigation (QA Action)
As the QA owner, I have:
1. **Documented** the limitation in `RESULTS.md`.
2. **Isolated** the test in `test_validator_terms.py` to assert the *current* behavior (proving we know the system fails open on this edge case), rather than letting it be an unhandled exception.
3. **Filed** this as a backlog item for Sprint 12.

#### 💻 Reproduction (For Reviewers)
To verify the limitation, run the following in a Python shell from the project root:
```python
from shared.fixture_case import make_case_001
from validator import validate_dialogue
from conftest import make_npc_context
from shared.contracts import DialogueRequest, DialogueDraft

case = make_case_001()
npc = make_npc_context(case, "gardener")
req = DialogueRequest(npc_id="gardener", question="What happened?", authorized_fact_ids=npc.authorized_fact_ids, permitted_evidence_ids=[])

# Text contains Cyrillic 'і' (wіll) instead of Latin 'i'
draft = DialogueDraft(npc_id="gardener", text="Somebody changed the wіll.", status="ok")

result = validate_dialogue(req, draft, case, npc)
print(result.reasons) 
# Output: ['OK'] (vulnerable to bypass - expected PROTECTED_TERM_LEAK)