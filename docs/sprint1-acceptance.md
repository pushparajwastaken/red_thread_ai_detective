# Sprint 1 acceptance record (audit 3: EPAM case-requirement remediation)

Status legend: **PASS** = reproducibly verified · **FAIL** = verified requirement not met · **BLOCKED** = needs
infrastructure/credentials/people that are unavailable · **NOT RUN** = no valid execution evidence.

## 0. Evidence base and its limits (read first)

- Repository state: branch `feature/epam-sprint1-acceptance`, base commit **`36f233bd35a1716050a98a334839ba6b4233d91e`**.
  The changes described here are **uncommitted working-tree changes**; nothing was committed, pushed or merged.
- All runs: Linux sandbox, **Python 3.12.3, pytest 9.2.0**, offline, deterministic mock provider, no credentials.
  They were **not** run in the project's Windows `.venv` (Python 3.13). Re-run `.\.venv\Scripts\python.exe -m pytest -q`
  there before presenting.
- The EPAM project review document itself was **not available** for this audit. Requirement text below is the Sprint 1
  case bullet list as quoted in the remediation brief (one mystery/victim, exactly three suspects, ten clues, ground-truth
  timeline, deterministic "can suspect know fact" queries). Anything beyond those bullets is **NOT RUN**.
- The previous record (audit 2) listed no case-content requirement at all, and its DoD #1 ("canonical case loads, equals
  shared fixture: PASS") was true while the canonical case had two NPCs and empty `clues`/`timeline`. That gap is what this
  audit closes.

## 1. EPAM Sprint 1 case requirement

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | One mystery and one victim | PASS | `case_001`; every timeline event names victim `lord_ashby`; validator rejects a missing or second victim (`test_case_engine.py` cases `timeline_no_victim`, `timeline_two_victims`) |
| 2 | Exactly three suspects | PASS | `gardener`, `cook`, `housekeeper`; validator rejects 2 or 4 (`only_two_suspects`, `four_suspects`) |
| 3 | Ten clues | PASS | `C001-C010`, one fact + one supporting evidence each; rejects 9 or 11 (`drop_clue`, `extra_clue`) |
| 4 | Ground-truth timeline, ordered | PASS | 9 events `T001-T009`, strictly increasing minutes; rejects swapped, equal, non-int, bool, out-of-range times |
| 5 | Deterministic queries: can suspect S know fact F | PASS (as specified; see decision 1) | `fact_access`, `evidence_access`, `can_suspect_know_fact`, `can_suspect_use_evidence`; golden tables; agree with `build_npc_context` on every suspect x item x progression 0-4 for both cases |
| 6 | Deterministic case data, fresh independent objects | PASS | repeated-load and mutation-independence tests (engine and fixture) |
| 7 | Stable IDs; all references validated | PASS | ID-format, duplicate, dangling-fact/evidence/suspect, clue-evidence-supports-fact checks |
| 8 | Authored lies separate from canonical truth | PASS | only `L001` is `cover_story`; no clue or timeline event may reference a lie (validator + tests); the contradicting truth `F005` exists and is not granted to the liar |
| 9 | Explicit per-NPC knowledge and evidence permissions | PASS | `npc_grants` for all three suspects; golden access tables |
| 10 | Unauthorized future facts/evidence not exposed | PASS (mock generator) | `test_nothing_hidden_ever_reaches_the_model` (3 suspects x 5 progressions); unlock-in-order and out-of-order evidence tests; each gate also tested with the upstream filter bypassed |
| 11 | Exact, case-sensitive IDs; unknown/invalid IDs rejected | PASS | `load_case` and all queries raise `ContractError` for 15 invalid case IDs and every inexact suspect/fact/evidence/progression input tried |
| 12 | Malformed data fails safely | PASS | 49 malformed mutations + 7 wrong-type objects -> `ContractError` only, including through `load_case` |
| 13 | `case_001` equals the shared fixture | PASS | engine == `make_case_001()` at every progression |
| 14 | Existing pipeline/validator/security/benchmark behaviour preserved | PASS | section 2: 506 baseline tests all still pass unmodified except one (section 5); security 50/50 identical outcomes; benchmark 1260 rows identical outcome columns, 0 leaks |

Canonical case structure (`case_001`): 1 victim, 3 suspects, 11 facts (`F001-F010` truth + `L001` the cook's authored lie), 11 evidence
items, 10 clues, 9 timeline events. Ground truth: the cook poisoned the decanter; the housekeeper is a red herring with an alibi.
`case_002` (Richa's original, 12 facts / 12 evidence / 3 suspects / 10 clues / 11 events) is preserved unchanged.

## 2. Headline results (sandbox; commands shown with the Windows interpreter you will use)

| Command | Result |
|---|---|
| `python -m pytest -q` | **722 passed, 3 skipped, 0 failed** (262 subtests). Baseline before any edit: 506 passed, 3 skipped, 262 subtests |
| `pytest members/richa` | 189 passed (was 19) |
| `pytest tests/test_case_acceptance.py` | 46 passed (new) |
| `pytest tests/test_npc_knowledge.py` / `tests/test_state_integrity.py` | 19 / 5 passed |
| `pytest tests/test_reference_flow.py` | 105 passed (unmodified) |
| `pytest tests/test_benchmark_questions.py tests/test_benchmark_validator_and_modes.py` | 29 passed, 1 skipped (`jsonschema` not installed) |
| `pytest tests/test_evidence_artifacts.py` | 10 passed (artifacts recomputed; not stale) |
| `python scripts/run_security_suite.py` (scratch copy) | 50 rows, 50 passed; outcomes identical to committed `results/security_test_log.csv` |
| `python scripts/validate_benchmark_questions.py` | valid, 0 errors (30 questions) |
| `python scripts/run_benchmark.py --all --warm-passes 20` + `make_benchmark_report.py` (scratch copy) | 630 rows/mode; outcome columns identical to committed results; 0 leaks |

Skips (3): `jsonschema` not installed (optional), 2 live-Ollama smoke tests (opt-in; BLOCKED, section 3).
Per suite: tests/ 279 (+1 skip) · ananya 11 · anshul 38 (+2 skip) · gagan 35 · harsh 64 · khushi 39 · richa 189 · paras 67.
Test-strength checks (scratch copies, not committed): 19 deliberate defects in the engine and 9 in pipeline gates were each
caught by the tests. The first pass found four survivors: the `load_case` safety net and the inventory gate were real test gaps
(tests added); the integration `reveal_at` check and the retriever spoiler gate are redundant layers masked by an upstream filter,
so they now have independent tests that bypass that filter.
The committed `results/` and `docs/benchmark-report.md` were **not** regenerated (outcomes are unchanged; only timings would move).

## 3. Requirements that cannot be claimed

| Requirement | Status | Note |
|---|---|---|
| Real-model validation (Ollama/other) | **BLOCKED** | no model server or credentials; steps in `docs/real-model-validation.md`; nothing was run against a real model |
| Real-model TTFT, sub-800 ms target | **NOT RUN** | mock does not stream; TTFT cells empty. Mock latencies measure pipeline overhead only |
| Real-model cost | **NOT RUN** | no backend reported usage; cells empty |
| Real-model dialogue quality; dynamic vs branching quality | **NOT RUN** | dynamic uses the canned mock; `answer_correct` is not a quality signal |
| Human playtests | **BLOCKED** | needs participants; protocol and empty template only (`members/ananya/`); no results exist |
| Provider-failure handling | PASS | `tests/test_provider_failure.py` (carried forward, not re-audited) |
| Member deliverables: Preksha, Devansh, Chhavi | **NOT RUN** | Audit 2 recorded FAIL ("not submitted"). That is **withdrawn**: work exists on unmerged remote branches `feature/preksha-qa`, `tests/devansh-adversarial-runs`, `chhavi/benchmarking` (verified to exist; content not evaluated). The integrated tree contains only their READMEs |
| Member branch SHAs in member files | NOT RUN | only HEAD `36f233b` verified; other recorded SHAs unverified |

## 4. Original Definition of Done

| # | Criterion | Status | Note |
|---|---|---|---|
| 1 | Canonical case loads, equals shared fixture, meets the EPAM case requirement | PASS | section 1 (previously met only the first two clauses) |
| 2 | NPC knowledge respects authorization/progression | PASS | exhaustive, now 3 NPCs; engine queries independently agree |
| 3 | Retrieval deterministic, respects reveal | PASS | 35 module tests; reveal gate now also tested on the real case |
| 4 | Generation works with offline mock | PASS | real provider not part of this (section 3) |
| 5 | Validation + fallback obey v2 | PASS, documented lexical limits | `docs/security-residual-risks.md` |
| 6 | Real pipeline works end to end | PASS (mock); real model **BLOCKED** | every suspect x progression validated |
| 7 | Reference-flow acceptance | PASS | 105 passed |
| 8-9 | Security categories and CSV | PASS | 10/10 categories, 50 scenarios, 50 passed |
| 10 | Canonical question set exists and validated | PASS | **protected lists regenerated** (section 5); questions unchanged |
| 11 | Dynamic and branching comparable | PASS | benchmark re-run identical |
| 12 | Benchmark real measurements + limitations | PASS for mock + fixed tree; real model **BLOCKED** | |
| 13 | Playtests recorded or marked pending | **BLOCKED** | marked pending |
| 14 | Docs match implementation | PASS for code-vs-doc claims | corrected here: case structure, test counts, member status |
| 15 | Commands reproduce results | PASS in sandbox; **NOT RUN** on Windows `.venv` | |

## 5. What changed, and every existing test touched

Files: `shared/fixture_case.py` (append-only data), `members/richa/case_engine.py`, `members/richa/test_case_engine.py`,
`test_cases/benchmark_questions.json` (derived lists only), `tests/test_case_acceptance.py` (new), and docs.
Contract change record: `shared/contracts.py` unchanged; `shared/fixture_case.py` extended; Module 1 gained the query functions
(`shared/interfaces.md`). The earlier statement "`shared/` byte-identical to the original ZIP" is **no longer true** and was removed.

- **One existing test rewritten:** `test_case_001_has_canonical_npcs_and_no_private_internals` asserted `{gardener, cook}` and
  `clues == [] and timeline == []`, i.e. that the requirement was *not* met. It is now `..._and_private_internals` and asserts the
  three suspects, 10 clues and 9 events. No test was deleted, skipped or weakened.
- **`benchmark_questions.json`:** `protected_fact_ids` / `protected_evidence_ids` of all 30 questions regenerated (they are derived
  from the case; `test_protected_ids_are_derived_from_fixture` enforces this). Verified: only bare ID entries in those two lists
  changed; every other field of every question and the file metadata are identical.
- **Name choice:** the third suspect is `housekeeper`, not `butler`, because `butler` is the canonical nonexistent NPC in
  `members/khushi` (AUTH-01, integration test, demo) and the novel-claim word in UNSUP-03. A first attempt using `butler` broke AUTH-01.
- **Gardener/cook untouched:** their grants, texts, reveal levels and the items they can see are unchanged, so the benchmark and
  security scenarios keep their meaning. New items were appended so iteration order (and reason-code order) is unchanged.

## 6. Reproduce (Windows)

    .\.venv\Scripts\python.exe -m pytest -q                                   # 722 passed, 3 skipped (sandbox)
    .\.venv\Scripts\python.exe -m pytest members/richa tests/test_case_acceptance.py -q
    .\.venv\Scripts\python.exe -m pytest tests/test_npc_knowledge.py tests/test_state_integrity.py tests/test_reference_flow.py -q
    .\.venv\Scripts\python.exe scripts/validate_benchmark_questions.py
    .\.venv\Scripts\python.exe scripts/run_security_suite.py                  # rewrites results/security_test_log.csv

## 7. Decisions still needed from the lead

1. **Meaning of "can know".** Implemented as *authorized* (granted and revealed). The guilty cook is therefore not granted her own
   crime (`F010`), so no prompt can contain it. If EPAM means ground-truth presence (who could have known from the timeline), a
   second query is needed; it would not change what models may see.
2. **Unmerged member branches** (section 3): decide whether to review/merge them before the review; the old "not submitted" claim is withdrawn.
3. `SUPPORT_SCOPE`, `UNCITED_ASSERTION` reuse, stub-backed `default_deps()`, and the `src/` relocation remain open from audit 2.
4. The 30 benchmark questions cover only gardener and cook; the housekeeper has none (Sprint 2).
