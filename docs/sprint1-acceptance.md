# Sprint 1 acceptance record (audit 2)

Status legend: **PASS** = directly supported by reproducible evidence · **FAIL** = verified requirement not met ·
**BLOCKED** = needs infrastructure/credentials/people that are unavailable · **NOT RUN** = no valid execution evidence.

Evidence base: the GitHub archive of commit **`44126a96e851a5b03615b86e9bf5c2fe7f2c9087`** (merged PR #7), identified by the
archive comment; it carries no `.git`, so git objects, history, remotes and member branches were NOT inspected. The patch was
generated against, and dry-run tested (`git apply --check`) on, exactly that archive's tree - not against a live checkout.
All runs: Python 3.12.3, offline, deterministic mock provider, no credentials. Re-verify with the commands shown.

## 1. Headline results (clean-room: fresh venv, pristine ZIP + final patch, only `requirements.txt` installed)

| Command | Result |
|---|---|
| `python -m pytest` | **506 passed, 3 skipped, 0 failed, 0 errors** (262 subtests passed) |
| `python -m pytest tests/test_reference_flow.py` | 105 passed (file byte-identical to audit 1) |
| `python scripts/run_security_suite.py` | 50 rows, 50 passed -> `results/security_test_log.csv` |
| `python scripts/validate_benchmark_questions.py` | valid, 0 errors (30 questions) |
| `python scripts/run_benchmark.py --all --warm-passes 20` then `python scripts/make_benchmark_report.py` | 630 rows/mode; report regenerated |
| `python -m pytest tests/test_evidence_artifacts.py` | 10 passed (artifacts recomputed from scratch; not stale) |

Environments run (Python 3.12.3): **base** venv = `requirements.txt` only (pytest 9.2.0, pluggy 1.7.0, iniconfig 2.3.1, packaging 26.3,
Pygments 2.21.0; unpinned `pytest` in `requirements.txt` resolves to the latest). **Optional** venv = base + `jsonschema 4.26.0` +
`requests 2.34.2`: `python -m pytest` -> **507 passed, 2 skipped** (only the live-Ollama smoke tests remain skipped); with `requests`
the real Ollama HTTP branch is exercised against a dead endpoint (`GEN_ERROR` fallback).

Skips (3, base venv): `jsonschema` not installed (optional; passes when installed), 2 live-Ollama smoke tests (opt-in, BLOCKED below).
Per suite: tests/ 233 (+1 skip) · ananya 11 · anshul 38 (+2 skip) · gagan 35 · harsh 64 · khushi 39 · richa 19 · paras 67.

## 2. Audit-2 defects: reproduced, fixed, regression-tested

| ID | Defect (reproduced first) | Fix | Regression evidence |
|---|---|---|---|
| A / UNSUP-03 | Unsupported claim beside a valid citation passed (18 of 19 probe cases accepted). The validator only checked term ownership, so a citation legitimised the whole reply | Deterministic claim-support check in `members/harsh/validator.py` (vocabulary, grounding, citation reflection, polarity) -> `UNCITED_ASSERTION` | `tests/test_validator_claim_support.py` (37); scenarios UNSUP-03..09; disabling the check fails 28 tests |
| B1 | Hung validator/retrieval/NPC builder blocked the caller (only generation was under the deadline) | One whole-call deadline on a daemon worker; reasons map by stage | `tests/test_timeout_robustness.py` (15) |
| B2 | Non-daemon pool threads leaked per timeout and blocked interpreter exit (subprocess still running after 40 s) | Daemon workers, cap `MAX_ABANDONED_WORKERS=8`, fail-fast `GEN_TIMEOUT` at the cap, late results discarded | same file; scenarios TMO-04/05 |
| C | Production vs stub wiring ambiguity (`default_deps()` stubs vs `src/pipeline.py`) | Single documented entry point `src.pipeline.interrogate`; stub default labelled `DEFAULT_DEPS_ARE_STUBS`; guard test | `tests/test_production_entry_point.py` |
| C | Mock default text cited a fact it did not reflect (would fail claim support) | Mock quotes its cited fact verbatim | `members/anshul` 38 pass; reference flow |
| 3 | Legacy cases without `fact_meta` crashed the new check into `VALIDATOR_ERROR` (found by Harsh's own test) | `.get()` guard | `test_support_check_survives_missing_fact_metadata` |

Existing tests changed, with reasons (none deleted or skipped): Harsh `test_known_limit_false_combination_of_visible_terms_can_pass`
(example sentence now correctly rejected; limitation preserved with an all-cited-words sentence, plus a new assertion);
scenario-table expectations UNSUP-03 (the fix itself) and IINJ-01 (harmless negation now falls back; recorded as IINJ-03 false positive).
`tests/test_reference_flow.py` is unchanged.

## 3. Original Definition of Done

| # | Criterion | Status | Command | Artifact |
|---|---|---|---|---|
| 1 | Canonical case loads, equals shared fixture | PASS | `python -m pytest tests/test_reference_flow.py -k "fixture or canonical"` | `members/richa/case_engine.py`, `tests/test_reference_flow.py` |
| 2 | NPC knowledge respects authorization/progression | PASS | `python -m pytest tests/test_npc_knowledge.py tests/test_state_integrity.py` | exhaustive NPC x progression x both cases, independent oracle |
| 3 | Retrieval deterministic, respects reveal | PASS (module-level) | `python -m pytest members/gagan` | 35 tests; exercised in every pipeline run; not re-audited in depth |
| 4 | Generation works with offline mock | PASS | `python -m pytest members/anshul` | 38 pass; real provider NOT part of this criterion (see 6) |
| 5 | Validation + fallback obey v2 | PASS, with documented lexical limits | `python -m pytest members/harsh tests/test_validator_claim_support.py` | `docs/security-residual-risks.md` |
| 6 | Real pipeline works end to end | PASS (mock generator); real-model **BLOCKED** | `python -m pytest tests/test_reference_flow.py tests/test_production_entry_point.py` | `src/pipeline.py` |
| 7 | Reference-flow acceptance passes | PASS | `python -m pytest tests/test_reference_flow.py` | 105 passed |
| 8 | Security tests cover all required categories | PASS | `python -m pytest tests/test_reference_flow.py::test_every_required_security_category_is_covered` | 10/10 categories, 50 scenarios |
| 9 | Security results in required CSV | PASS | `python scripts/run_security_suite.py` | `results/security_test_log.csv` (header == `TestRecord`) |
| 10 | Canonical question set exists + validated | PASS | `python scripts/validate_benchmark_questions.py` | `test_cases/benchmark_questions.json` (unchanged) |
| 11 | Dynamic and branching run on comparable cases | PASS | `python -m pytest tests/test_benchmark_validator_and_modes.py` | identical questions/NPCs/evidence/progression |
| 12 | Benchmark has real measurements + limitations | PASS for mock + fixed-tree; real-model **BLOCKED** | `python scripts/run_benchmark.py --all --warm-passes 20 && python scripts/make_benchmark_report.py` | `results/benchmark_results.csv`, `docs/benchmark-report.md` |
| 13 | Playtests recorded or marked pending | **BLOCKED** (needs human participants) - marked pending | - | `members/ananya/playtest_protocol.md`, empty template; no results exist |
| 14 | Docs/submissions match the implementation | PASS for code-vs-doc claims; branch/SHA claims **NOT RUN** (no git) | `python -m pytest tests/test_evidence_artifacts.py` | README, CONTRIBUTING, `docs/team-contributions.md`, SUBMISSION files |
| 15 | Documented commands reproduce the results | PASS | clean-room procedure in section 6 | - |

## 4. Other Sprint 1 requirements

| Requirement | Status | Evidence / note |
|---|---|---|
| Real-model validation (Ollama/other) | **BLOCKED** | no `ollama`, no server, no credentials, `ollama.com` unreachable; steps in `docs/real-model-validation.md` |
| Provider-failure handling (dead endpoint, bad provider, missing `requests`) | PASS | `tests/test_provider_failure.py` (clean venv exercises the missing-`requests` branch; with `requests` installed the connection-refused branch runs) |
| TTFT measured; sub-800 ms target | **NOT RUN** | mock does not stream; cells left empty |
| Cost measured | **NOT RUN** | no backend reported cost; cells left empty |
| Dynamic vs branching *quality* comparison | **NOT RUN** | dynamic uses the canned mock; its `answer_correct` is not a quality signal |
| Member deliverables: Preksha (contract/authorization tests), Devansh (adversarial), Chhavi (benchmark) | **FAIL** (not submitted; README only) | lead-authored substitutes exist and are labelled in `docs/team-contributions.md` |
| Branches / commit SHAs of members | **NOT RUN** | ZIP has no `.git`; SHAs quoted in member files are unverified |
| Shared contracts unchanged | PASS | `shared/` byte-identical to the original ZIP |

## 5. Trust invariants -> evidence

Authorization/reveal gating, exact case-sensitive IDs, fresh objects, no mutation by untrusted data, only integration advances
state, validation before player text, citations never trusted, reason codes without IDs, identical fallback text, whole-call
metrics (`total_ms == latency_ms`), TTFT distinct from total, never raises: covered by `tests/test_reference_flow.py`,
`tests/test_state_integrity.py`, `tests/test_timeout_robustness.py`, `tests/test_validator_claim_support.py`.
The validator's lexical nature and all known holes are listed in `docs/security-residual-risks.md`.

## 6. Reproduce

    unzip red_thread_ai_detective-main.zip && cd red_thread_ai_detective-main
    git init -q . && git apply --check -p1 ../sprint1_integration.patch && git apply -p1 ../sprint1_integration.patch && rm -rf .git
    python -m venv .venv && . .venv/bin/activate && python -m pip install -r requirements.txt
    python -m pytest                                         # 506 passed, 3 skipped
    python -m pytest tests/test_reference_flow.py            # 105 passed
    python scripts/run_security_suite.py && python scripts/validate_benchmark_questions.py
    python scripts/run_benchmark.py --all --warm-passes 20 && python scripts/make_benchmark_report.py
    python -m pip install jsonschema requests && python -m pytest tests/test_benchmark_questions.py tests/test_provider_failure.py   # optional deps

## 7. Decisions still needed from the lead

1. **`SUPPORT_SCOPE`**: default `"grounded"` keeps the v2 sentence "text with no case terms needs no citation", leaving uncited,
   term-free accusations as a residual. `"all"` closes it but rejects most free-form role-play. Product/contract decision.
2. **`UNCITED_ASSERTION` reuse** for "reply not supported by its citations" (no `shared/` change was made). Consider a dedicated code.
3. Whether to switch `members.khushi.integration.default_deps()` to the real modules (kept stub-backed for member isolation).
4. Copying approved modules into their final `src/` location (`src/pipeline.py` currently imports from `members/`).
