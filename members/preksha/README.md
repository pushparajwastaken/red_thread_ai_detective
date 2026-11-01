# Red Thread — Sprint 1 QA & Validation Suite

**Owner:** Preksha Wani (QA/Validation Engineer)  
**Sprint:** 1 — Case Engine & Epistemic Schema  
**Scope:** Contract enforcement, authorization boundaries, and adversarial spoiler testing.

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

# Run the full suite (from the project root)
python -m pytest members/preksha -v

```
## 📁FOLDER STRUCTURE
```text 

members/preksha/
├── conftest.py                    # Environment setup, shims, and CSV reporting hooks
├── README.md                      # Test suite documentation
├── SUBMISSION.md                  # Formal DoD hand-off for the Integration Lead
├── RESULTS.md                     # QA Execution Report and Verification Milestones
├── data/                          # Placeholder for local test data
├── results/                       # Auto-generated test reports (CSV & Markdown)
│   ├── latest_run.txt             # Quick reference of the latest test run stats
│   ├── summary.csv                # Master CSV of all test results
│   ├── summary.md                 # Human-readable summary for Sprint Review
│   ├── by_category/               # CSVs aggregated by DoD test categories
│   ├── by_file/                   # CSVs containing per-test-file results
│   └── logs/                      # Raw run logs (if captured via script)
└── tests/                         # 16 active test files mapped to DoD requirements
    ├── test_authorization.py      # Rejects unauthorized facts/evidence
    ├── test_case_engine_load.py   # Verifies CASE_001_ID loading logic
    ├── test_contracts.py          # Validates trusted/untrusted boundaries
    ├── test_demo.py               # basic sanity check
    ├── test_e2e.py                # Full pipeline integration
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
    └── test_validator_terms.py    # Tests word boundary and homoglyphs

# Note: `pytest.ini` is located at the project root.
# Note: Archived bug evidence is located at `docs/bug_evidence/`.
```
### 🧪 Test Coverage Map (Sprint 1 DoD)

| DoD Category | Test File(s) | Purpose |
| :--- | :--- | :--- |
| **Authorization** | `test_authorization.py`<br>`test_request_security.py` | Ensures `DialogueRequest` rejects unauthorized facts/evidence. |
| **Spoiler Gating** | `test_spoiler.py`<br>`test_progression.py` | Blocks future facts (`F004`) until `reveal_at` progression is met. |
| **Unsupported Claim** | `test_unsupported_claim.py`<br>`test_validator_terms.py` | Catches protected terms leaked in prose without citations. |
| **Malformed Output** | `test_malformed_output.py` | Ensures invalid LLM JSON returns `SCHEMA_INVALID`. |
| **Validator Failure** | `test_validator_failclosed.py` | Verifies the validator never raises exceptions on garbage input. |
| **Timeout/Fallback** | `test_timeout.py`<br>`test_make_fallback.py` | Tests generator timeouts and verifies `SAFE_FALLBACK_TEXT`. |
| **E2E Pipeline** | `test_e2e.py` | Full integration test from Case Loading to Dialogue Validation. |

> **📝 Note on Terminology:** 
> Keywords referenced in the "Purpose" column—such as `DialogueRequest`, `reveal_at`, `SAFE_FALLBACK_TEXT`, and Reason codes like `SCHEMA_INVALID`—are imported directly from `shared/contracts.py`. Specific Fact IDs like `F004` are defined in the golden fixture at `shared/fixture_case.py`.

### 🛡️ QA Verification Milestones (Sprint 1)

During Sprint 1, this test suite caught and verified fixes for several critical integration blockers. The exact proof files are archived at `docs/bug_evidence/`.

1. **Case Engine Fixture Drift:** **Fixed.** `case_001` now perfectly matches the golden fixture.
2. **NPC Knowledge Contract:** **Fixed.** `build_npc_context()` now returns the correct `NPCContext` dataclass and handles the fixture properly.
3. **Validator Strict Lexical Matching & Homoglyphs:** **Fixed.** The validator now successfully blocks TR39 confusables (Cyrillic `wіll`) and correctly handles strict citations.
