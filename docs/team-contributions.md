# Team contributions (evidence from the reviewed snapshot only)

Source: files in the GitHub archive of commit `44126a96e851a5b03615b86e9bf5c2fe7f2c9087` (the archive carries no `.git`) and each
member's `SUBMISSION.md`. **Branch status and commit SHAs could not be verified** (no repository history was available). SHAs below
are copied from member files, not checked. Nothing here is a claim about effort or authorship beyond what the files show.

| Module | Owner | Delivered in snapshot | Recorded branch / SHA (member-reported, unverified) | Lead notes |
|---|---|---|---|---|
| 1 Case Engine | Richa Bharti | `members/richa/case_engine.py`, tests, SUBMISSION | none recorded | `case_001` realigned to the fixture; her original 12-fact case kept as `case_002` |
| 2 NPC Knowledge | Anand Kumar Sahni | `members/anand/npc_knowledge.py`, SUBMISSION, `tests/test_npc_knowledge.py` | none recorded | Original did not use shared types; refactored by lead onto the contract |
| 3 Evidence Retrieval | Gagan Chaurasia | `members/gagan/retriever.py`, tests, demo | `gagan/evidence-retrieval`; SHA placeholder not filled | 35 tests pass; not otherwise audited in depth |
| 4 Dialogue Generator | Anshul Prajapati | `members/anshul/dialogue_generator.py`, tests | `members/anshul`; SHA placeholder not filled | One stale test assertion fixed; mock default text now quotes its cited fact; live Ollama path **untested** (no server available) |
| 5 Validator/Fallback | Harsh Gupta | `members/harsh/validator.py`, tests | `harsh/validator-fallback-v2` @ `166864a4...` | 64 tests pass; audit-2 added a claim-support check to the validator (lead edit; one test edited and flagged in-file) |
| 6 Integration | Pushparaj Singh Parmar / Khushi Kumari | `members/khushi/integration.py` (+stubs, tests); `members/pushparaj/` has only a README | `khushi/integration-v2` @ `17ca20a8...` | Audit-2: whole-call deadline with daemon workers (lead edit); `default_deps()` kept stub-backed and labelled; her 39 tests pass unchanged. Real wiring in `src/pipeline.py` |
| 7 Testing - contract/authorization | Preksha Wani | **nothing** (README only) | - | Gap; lead-authored coverage in `tests/` (see below) |
| 7 Testing - regression/reference flow | Paras Gupta | `members/paras/sprint1/test_regression.py` | none recorded | Two stale skip-guards repaired |
| 7 Testing - adversarial | Devansh Vinayak | **nothing** (README only) | - | Gap; adversarial scenarios authored by lead in `tests/security_scenarios.py` |
| 8 Benchmarking | Chhavi Sharma | **nothing** (README only) | - | Gap; runner/report scripts authored by lead (`scripts/run_benchmark.py`, `make_benchmark_report.py`) |
| 9 Branching Baseline | Ananya Narula | `members/ananya/` baseline, tests, playtest protocol/template; PR #7 (merged in 44126a9) | `feature/ananya-branching-baseline`, integration commit `50ce755` (her SUBMISSION.md; unverified) | The 0.0 ms latency defect was fixed by PR #7 (kept as merged). The shared-question-set path defect is fixed by the integration patch. Playtests pending |

Lead-authored in this integration pass (not member work): `tests/test_reference_flow.py`,
`tests/security_scenarios.py`, `tests/test_benchmark_validator_and_modes.py`, `src/pipeline.py`, `scripts/*`,
`results/*`, `docs/benchmark-report.md`, `docs/security-residual-risks.md`, `docs/real-model-validation.md`, `docs/sprint1-acceptance.md`,
`tests/test_validator_claim_support.py`, `tests/test_timeout_robustness.py`, `tests/test_state_integrity.py`, `tests/test_production_entry_point.py`,
`tests/test_provider_failure.py`, `tests/test_evidence_artifacts.py`. Members may adopt, review or replace these.
