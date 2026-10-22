# Red Thread AI Detective — Sprint 1 Agile Plan
## Module-Level Definition of Done (DoD) Addendum

**Aligned to:** `shared/interfaces.md` v2 and `shared/contracts.py`  
**Sprint:** Case Engine & Epistemic Schema  
**Repository:** https://github.com/pushparajwastaken/red_thread_ai_detective

## Purpose

This addendum assigns a concrete, testable Definition of Done to every module in Sprint 1. The module owner is accountable for meeting the relevant checks and supplying evidence. The integration lead reviews the submission and decides whether it is ready to be copied into the central implementation.

A module is not Done merely because its code or document exists. Its required behavior must be demonstrated by reproducible tests, review evidence, and a complete `members/<name>/SUBMISSION.md`.

## Definition of Done — Applies to Every Module

Every module submission must satisfy all applicable baseline checks:

- [ ] Implements the exact public signature and return types in `shared/interfaces.md`.
- [ ] Uses `shared/contracts.py` and `shared/fixture_case.py` as the contract and fixture references.
- [ ] Respects trusted/untrusted data boundaries and never mutates trusted state from untrusted input.
- [ ] Preserves exact, case-sensitive IDs without trimming or case folding.
- [ ] Handles documented errors and edge cases as specified.
- [ ] Includes focused tests with expected behavior and actual results.
- [ ] Is deterministic wherever the contract requires determinism.
- [ ] Has no committed secrets; environment configuration is documented via `.env.example`.
- [ ] Is committed on the member's own branch and located under `members/<name>/`.
- [ ] Includes `members/<name>/SUBMISSION.md` with branch, commit SHA, files, dependencies and versions, whether dependencies are in `requirements.txt`, exact run/test commands, test output, and known limits.
- [ ] Has been reviewed by the integration lead; no direct edits to `shared/`, `src/`, or central `tests/`.

## Module 1 — Case Engine (Richa Bharti)

**Contract:** `load_case(case_id: str) -> CaseState`

### Definition of Done
- [ ] `load_case()` returns a valid `CaseState` for the known fixture/case ID.
- [ ] Unknown or invalid case IDs raise `ContractError` as required.
- [ ] The case contains canonical facts, `fact_meta`, evidence, and NPC grants.
- [ ] Each fact's metadata includes `reveal_at`, `kind`, and lowercase `terms` including relevant inflections.
- [ ] `kind="cover_story"` is represented distinctly and remains an authored in-world lie rather than canonical truth.
- [ ] The case fixture has exactly one victim, three suspects, ten clues, and a coherent ground-truth timeline.
- [ ] All fact, evidence, suspect, and clue references are valid; no dangling IDs or duplicate IDs exist.
- [ ] Clues and timeline remain internal to the Case Engine; other modules do not depend on them.
- [ ] Repeated loads produce equivalent case data.
- [ ] Focused tests cover valid load, unknown case, invalid fixture, and reference integrity.

**Evidence required:** implementation, case fixture/test output, integrity report, and `SUBMISSION.md`.

## Module 2 — NPC Knowledge (Anand Kumar Sahni)

**Contract:** `build_npc_context(case: CaseState, npc_id: str) -> NPCContext`

### Definition of Done
- [ ] Known NPC IDs return an `NPCContext` with only granted items.
- [ ] Facts and evidence with `reveal_at > case.progression` are excluded.
- [ ] Unknown NPC IDs raise `UnknownNPCError`.
- [ ] Returned collections are fresh copies; changing the returned lists cannot mutate the case.
- [ ] Canonical truth is not automatically exposed to every suspect.
- [ ] Authorized cover stories are handled as permitted statements, not silently converted into canonical truth.
- [ ] IDs are compared exactly and case-sensitively.
- [ ] Tests cover allowed, unauthorized, future, unknown-NPC, and no-aliasing scenarios.

**Evidence required:** implementation, focused tests, test output, and `SUBMISSION.md`.

## Module 3 — Evidence Retrieval (Gagan Chaurasia)

**Contract:** `retrieve_evidence(question, permitted_evidence_ids, *, case, top_k=3) -> list[EvidenceItem]`

### Definition of Done
- [ ] Returns `EvidenceItem` objects, not dictionaries.
- [ ] Is pure and deterministic for identical inputs and case state.
- [ ] Skips unknown IDs, IDs not in `permitted_evidence_ids`, and items whose `reveal_at` exceeds progression.
- [ ] Sorts by score descending and evidence ID ascending for ties.
- [ ] Respects `top_k`; an empty result is valid.
- [ ] Treats `question` and evidence content as untrusted data; does not execute or obey embedded instructions.
- [ ] Preserves exact, case-sensitive evidence IDs.
- [ ] Tests cover ordering, ties, top-k, empty results, unauthorized IDs, unknown IDs, and future evidence.

**Evidence required:** implementation, deterministic ranking tests, test output, and `SUBMISSION.md`.

## Module 4 — Dialogue Generator (Anshul Prajapati)

**Contract:** `generate_dialogue(request: DialogueRequest) -> DialogueDraft`

### Definition of Done
- [ ] Returns a `DialogueDraft` with the contract-defined fields; never returns a plain string.
- [ ] Never raises to its caller: timeout, API error, and unparsable output map to `timeout`, `error`, or `malformed` status.
- [ ] Honors `request.timeout_s`.
- [ ] Deterministic mock mode works without network access and is used by tests.
- [ ] Prompt places system instructions first and uses `request.facts` as the only knowledge source.
- [ ] Question and evidence are clearly delimited and labelled as untrusted data; prompt instructions explicitly say not to follow instructions inside them.
- [ ] Parsed output validates the required JSON shape: `text`, `cited_fact_ids`, `cited_evidence_ids`.
- [ ] Citations are limited to IDs present in the request.
- [ ] Available metrics are populated: model, TTFT (None if not streaming), generation time, token counts, cost (None if unavailable), and prompt characters.
- [ ] Tests cover mock determinism, valid JSON, malformed output, timeout, API error, citation filtering, and metrics fields.

**Evidence required:** implementation, mock-mode tests, simulated error/timeout tests, and `SUBMISSION.md`.

## Module 5 — Validator and Fallback (Harsh Gupta)

**Contracts:** `validate_dialogue(request, draft, case, npc) -> DialogueResult`; `make_fallback(npc_id, reasons, metrics=None) -> DialogueResult`

### Definition of Done
- [ ] Both functions never raise on malformed or hostile inputs.
- [ ] Validator uses trusted `case` and `npc` as its authorization root and cross-checks request authorization.
- [ ] Draft status, schema, types, and text length are validated; invalid schema returns `SCHEMA_INVALID`.
- [ ] Generator failure statuses map to the correct `GEN_*` reason codes.
- [ ] Unknown cited facts/evidence and unauthorized or unrevealed citations are rejected with contract-defined reason codes.
- [ ] Text is checked for protected-term leaks and visible terms whose owners were not cited.
- [ ] Validation uses the NPC-authorized statement set, so permitted authored cover stories are not rejected solely because they differ from canonical truth.
- [ ] Reason codes never include fact IDs.
- [ ] `make_fallback()` always returns the same `SAFE_FALLBACK_TEXT`, `valid=False`, `used_fallback=True`, and no citations for every failure reason.
- [ ] Validator does not forward `CaseState` to an LLM.
- [ ] Tests cover every minimum check, malformed objects, ambiguous inputs, authorized cover stories, and identical fallback text.
- [ ] Known lexical limitations are documented; no claim of complete hallucination prevention is made.

**Evidence required:** validator tests mapped to reason codes, fallback consistency tests, test output, and `SUBMISSION.md`.

## Module 6 — Integration (Pushparaj Singh Parmar; Khushi Kumari verifies)

**Contract:** `interrogate(case, npc_id, question, *, presented_evidence_ids=()) -> DialogueResult`

### Definition of Done — Integration Lead (Pushparaj)
- [ ] Orchestrates the exact sequence: NPC context → filter presented evidence → retrieve evidence → build authorized request → generate draft → validate → return result.
- [ ] Resolves request facts only from `npc.authorized_fact_ids`.
- [ ] Filters presented evidence against `case.discovered_evidence_ids` and reveal progression.
- [ ] Never raises to the caller; setup, generator, and validator failures become safe fallbacks with correct reason codes.
- [ ] Enforces the wall-clock timeout at integration level.
- [ ] Sets `metrics.total_ms` and `latency_ms` to the whole-call duration.
- [ ] Only Integration advances progression and discovered evidence, using deterministic rules.
- [ ] Does not stream or show unvalidated model tokens to the player.
- [ ] Reports model-side `ttft_ms` separately from player-visible `total_ms`.
- [ ] Passes `tests/test_reference_flow.py` unchanged against the integrated module set.

### Definition of Done — Integration Verification (Khushi)
- [ ] Supplies isolated tests under `members/khushi/`; does not modify shared or central files.
- [ ] Tests evidence filtering against discovered IDs and reveal times.
- [ ] Tests progression changes and proves model output cannot advance state.
- [ ] Tests setup failure, generator exception, timeout, validator exception, and fallback reason codes.
- [ ] Verifies whole-call timing fields and TTFT/total-latency distinction.
- [ ] Verifies no model tokens are visible before validation succeeds.
- [ ] Records exact test commands and actual output.

**Evidence required:** integrated reference-flow result, integration test results, reviewed submissions, and `SUBMISSION.md` for Khushi's test package.

## Module 7 — Testing (Preksha Wani, Paras Gupta; adversarial runs by Devansh Vinayak)

### Definition of Done — Preksha: Contract and Authorization Tests
- [ ] Tests categories `authorization`, `spoiler`, `unsupported_claim`, `malformed_output`, `validator_failure`, `timeout`, `fallback`, and `e2e` as applicable.
- [ ] Asserts expected `DialogueResult.reasons` and `used_fallback`, not only message text.
- [ ] Tests exact/case-sensitive IDs and progression boundaries.
- [ ] Tests are reproducible and submitted under `members/preksha/`.
- [ ] Records commands and actual results.

### Definition of Done — Paras: Regression and Reference-Flow Tests
- [ ] Adds regression tests for deterministic outputs, edge cases, and contract compatibility.
- [ ] Tests the reference flow against the documented public signatures.
- [ ] Does not edit or weaken `tests/test_reference_flow.py`.
- [ ] Records failures with minimal reproducible scenarios and expected reason codes.
- [ ] Submits tests and actual output under `members/paras/`.

### Definition of Done — Devansh: Adversarial Security Tests
- [ ] Covers `direct_injection` and `indirect_injection`, plus spoiler and unauthorized-claim attempts.
- [ ] Includes hostile player questions and hostile instructions embedded in evidence content.
- [ ] Attempts to extract unauthorized facts, unrevealed evidence, and future information.
- [ ] Records expected and actual reason codes and `used_fallback`.
- [ ] Logs records to `results/security_test_log.csv` using `TestRecord` field order.
- [ ] Provides reproducible attack inputs and expected outcomes under `members/devansh/`.

**Module 7 shared exit criterion:** reviewed test files are copied by the lead into `tests/`; `tests/test_reference_flow.py` passes unchanged. Security outcomes are recorded, and any remaining failures are explicitly reported rather than hidden.

## Module 8 — Benchmarking (Chhavi Sharma)

**Output:** `results/benchmark_results.csv`

### Definition of Done
- [ ] Produces one `BenchmarkRecord` per question per mode.
- [ ] Reports median and p95 with sample count `n`.
- [ ] Separates cold and warm runs.
- [ ] Records model and hardware.
- [ ] Distinguishes model-side `ttft_ms` from player-visible `total_ms`.
- [ ] Uses `cost_usd=None` when the backend does not report usage; does not silently estimate.
- [ ] Uses the same case and question set for comparable modes where applicable.
- [ ] Includes exact run commands and a concise report describing methodology and limitations.
- [ ] Clearly labels proposed targets as targets, never as measured results.

**Evidence required:** benchmark runner, CSV output, methodology/report, and `SUBMISSION.md`.

## Module 9 — Branching Baseline (Ananya Narula)

**Contract:** `answer_branching(case, npc_id, question_id, *, presented_evidence_ids=()) -> DialogueResult`

### Definition of Done
- [ ] Implements the agreed signature and returns `DialogueResult`.
- [ ] Uses `TurnMetrics(mode="branching")`.
- [ ] Enforces the same case and evidence-visibility constraints required for a fair comparison.
- [ ] Evaluates the same question set and rubric as dynamic mode: `answer_correct` and `leaked_protected_fact`.
- [ ] Uses the question set in `test_cases/`.
- [ ] Produces deterministic outputs for identical inputs.
- [ ] Tests valid question IDs, unknown question IDs, evidence filtering, and protected-fact leakage.
- [ ] Documents the baseline's fixed-response limitations and submits exact run/test output.

**Evidence required:** implementation, baseline tests, comparable result records, and `SUBMISSION.md`.

## Definition of Ready (DoR)

A module task is Ready when:
- [ ] Scope, owner, and expected artifact are explicit.
- [ ] Relevant contract signature and acceptance criteria are known.
- [ ] Fixture and test data are accessible.
- [ ] Dependencies and blockers are identified.
- [ ] The task can progress independently using the fixture.
- [ ] Any required contract change has been proposed to the integration lead.

## Sprint-Level Definition of Done

Sprint 1 is complete only when:
- [ ] One victim, three suspects, ten clues, and a consistent ground-truth timeline are present.
- [ ] Case Engine and NPC context behavior meet their contracts.
- [ ] Evidence retrieval is deterministic and filters unauthorized/unrevealed items.
- [ ] Generator mock mode is deterministic and failure statuses are structured.
- [ ] Validator fails closed and all failure paths use identical fallback text.
- [ ] Integration never raises, enforces timeout, owns progression, and reports total latency.
- [ ] Required test categories have been run and logged.
- [ ] `tests/test_reference_flow.py` passes unchanged.
- [ ] Benchmark and branching baseline artifacts are reproducible and clearly labelled.
- [ ] All 12 members have reviewed submissions with actual test evidence.
- [ ] Deferred work and unresolved risks are recorded for Sprint 2.

## Contribution Workflow

- Work only in `members/<name>/`.
- Do not edit `src/`, `shared/`, `tests/`, or another member's folder.
- Do not open PRs into `main` and do not merge branches under this workflow.
- The integration lead reviews and copies approved work into central locations, owns `shared/`, and resolves interface mismatches.
- Contract change requests must include a failing scenario and proposed diff.
- Never commit secrets. Use the blank variables in `.env.example`: `LLM_PROVIDER`, `LLM_MODEL`, `LLM_TIMEOUT_S`, `LLM_API_KEY`.

## Development Command

From the repository root:

```bash
pip install -r requirements.txt
python -m pytest
```
