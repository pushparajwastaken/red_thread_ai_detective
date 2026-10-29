# Red Thread - AI Detective Game

A prototype detective game using dynamic dialogue, evidence-based interrogation, restricted NPC
knowledge, and response validation.

**Central principle:** the case engine owns canonical truth; NPCs have bounded knowledge; the LLM
provides expression; the validator enforces authorization; integration controls trusted state and recovery.

## Project Goals

- Present evidence without revealing future plot information.
- Prevent NPCs from claiming facts they are not authorized to know.
- Validate generated dialogue and fall back safely when necessary.
- Benchmark dynamic dialogue against branching dialogue trees.

## Setup

Python 3.11 or newer (verified on 3.12).

    python -m venv .venv
    # Windows PowerShell:  .\.venv\Scripts\Activate.ps1      Linux/macOS: source .venv/bin/activate
    python -m pip install -r requirements.txt

## Run the tests (offline, deterministic, no credentials)

From the repository root:

    python -m pytest                     # root acceptance suite (tests/) AND all member suites (members/)
    python -m pytest tests/test_reference_flow.py -q     # the Sprint 1 acceptance suite only

`tests/test_reference_flow.py` runs the REAL modules end to end (no stubs) with the offline mock generator.
Live-LLM smoke tests are optional and skipped unless you start Ollama and set `RUN_LLM_SMOKE=1`.
`jsonschema` is optional; without it one schema test is skipped.

## Regenerate evidence artifacts (from real runs)

    python scripts/run_security_suite.py                                   # -> results/security_test_log.csv
    python scripts/validate_benchmark_questions.py                         # validates test_cases/benchmark_questions.json
    python scripts/run_benchmark.py --all --warm-passes 20                 # -> results/benchmark_results.csv
    python scripts/make_benchmark_report.py                                # -> docs/benchmark-report.md
    python scripts/run_tests.py                                            # pytest + question-set validator

Real-model run (needs Ollama; NOT executed in this repo's evidence): `docs/real-model-validation.md`.
Security limits and residual risks: `docs/security-residual-risks.md`. Acceptance checklist: `docs/sprint1-acceptance.md`.

## Production entry point

`src.pipeline.interrogate(case, npc_id, question, *, presented_evidence_ids=())` is the one production entry point and uses
the real modules. `members.khushi.integration.interrogate` without `deps` uses member-dev **stubs** (kept so members can work
in isolation); `tests/test_production_entry_point.py` fails if `src/` or `scripts/` ever depend on it.

## Runtime flow

    load_case (Richa) -> build_npc_context (Anand) -> retrieve_evidence (Gagan)
    -> DialogueRequest -> generate_dialogue (Anshul) -> validate_dialogue / make_fallback (Harsh)
    -> DialogueResult      orchestrated by interrogate() (Khushi/Pushparaj); real wiring: src/pipeline.py

## Repository Structure

- shared/: contracts and fixture (source of truth: `shared/interfaces.md`; only the integration lead edits)
- members/: each member's module, tests and `SUBMISSION.md`
- src/: integration glue wiring the real modules (`src/pipeline.py`)
- tests/: acceptance, contract, benchmark-set and NPC-knowledge tests
- test_cases/: shared benchmark questions (`benchmark_questions.json`) + schema
- results/: measured outputs (`security_test_log.csv`, `benchmark_results.csv`)
- docs/: benchmark report, contributions, acceptance record
- scripts/: test and evidence entry points

## Team Workflow

See `CONTRIBUTING.md`. In short: work only in `members/<name>/`, push your own branch, do NOT open a
pull request into `main` and do NOT merge. The integration lead reviews and copies approved work.

## Security Notice

NPC prompts must contain only authorized facts and evidence. Never expose the entire canonical case
state to the LLM. Do not commit credentials, API keys or private configuration files (copy
`.env.example` to `.env`, which is git-ignored). Lexical validation is a control, not hallucination prevention.
