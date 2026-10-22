# Module 6 submission: Khushi

- Branch: `khushi/integration-v2`
- Tested implementation commit SHA: `17ca20a8b8bb924a0cd9f76b15a14efbaa7a98bc`
- Base main commit: `dd1ecf4a0fa7ee60c522143a608cdaab0496098a` 
- This handoff file is a subsequent documentation-only commit. The implementation SHA above identifies the exact code, tests and captured outputs being submitted; it is intentionally not a self-referential hash of this file.
- Test date: 22 October 2026
- Scope: only `members/khushi/`. Lead reviews/copies approved code into `src/` and owns shared interfaces. No PR into main and no merge.
- Push status: pushed to origin/khushi/integration-v2

## Files

| File | Purpose |
| --- | --- |
| `integration.py` | `interrogate`, `interrogate_traced`, `Deps`/`default_deps`, `TurnTrace`, `advance_progression`, `discover_evidence`, `summarize_traces`, `looks_like_injection` |
| `stubs.py` | Offline stand-ins for Modules 2-4 (NPC context, evidence retrieval, mock generator with 24 behaviour modes) |
| `scenarios.py` | 42-scenario table shared by the tests and the log runner |
| `test_integration.py` | 39 offline tests (plus 165 subtests under pytest) |
| `run_checks.py` | Writes `results/integration_test_log.csv` and `results/integration_summary.json` |
| `demo.py` | Five deterministic developer scenarios |
| `results/integration_test_log.csv` | 98 `TestRecord` rows (header = `TestRecord` field order) |
| `results/integration_summary.json` | Leak counts, heuristic accuracy, latency/timeout probe, environment |
| `test-output.txt` | Actual verbose test output |
| `demo-output.jsonl` | Actual demo output |
| `README.md` | Usage, guarantees, mapping to the EPAM review issues, known limits, branch-only workflow |
| `LEAD_NOTES.md` | Contract decisions, validator findings, change request, scope |
| `SUBMISSION.md` | This handoff record |

## Dependencies and environment

| Dependency | Exact tested version | Already in root requirements.txt? |
| --- | --- | --- |
| Python (CPython runtime) | `Python == 3.11.9` | No; runtime. Root README requires Python 3.11+. |
| Standard library (`unittest`, `dataclasses`, `concurrent.futures`, `re`, `unicodedata`, `csv`, `json`, `math`, `time`, `uuid`) | Bundled with Python | No external packages required. |
| `pytest` (optional) | `pytest == 9.1.1` | Yes, unpinned. The suite is plain `unittest` and also collects under pytest. |
| `shared.contracts`, `shared.fixture_case`, `members.harsh.validator` | Base commit above | Local project modules, not pip dependencies. |

No new third-party dependency. Tests are offline, use no API key and make no LLM or network calls.

Measured execution environment for the numbers below: Windows 10, AMD64, 4 CPUs, CPython 3.11.9 (the author's own machine).

## Exact commands

From the repository root:

```bash
python -B -m unittest discover -s members/khushi -p test_integration.py -v
python -B members/khushi/run_checks.py
python -B -m members.khushi.demo
```

To regenerate the submitted evidence files:

```bash
python -B -m unittest discover -s members/khushi -p test_integration.py -v > members/khushi/test-output.txt 2>&1
python -B -m members.khushi.demo > members/khushi/demo-output.jsonl
python -B members/khushi/run_checks.py --quiet
```

## Actual test output

Exit code `0`. Full output: `test-output.txt`.

```text
----------------------------------------------------------------------
Ran 39 tests in 0.627s

OK
```

The elapsed time is an observed unit-test duration, not an application latency benchmark. Root suite
(`python -m pytest tests`): 5 passed.

## Evidence for the three EPAM review issues (`results/`)

All runs use a MOCK model. They measure the integration layer plus Harsh's real validator, not a real LLM.

| Issue | Measurement | Result |
| --- | --- | --- |
| Latency | Integration + validator overhead with an instant mock model, warm n = 200 | median 0.89 ms, p95 1.12 ms (cold single call 1.08 ms); values vary slightly per run. The model dominates real latency. |
| Latency | Deadline enforcement, n = 10, budget 100 ms, model delay 500 ms | 10 of 10 timed out; total_ms median 108.9, max 110.1 |
| Cost | Mock reports no usage | `cost_usd = None` everywhere; not estimated. Needs a real backend. |
| Injection | 42 scenarios (authorization, spoiler, unsupported claim, direct/indirect injection, malformed output, validator failure, timeout, fallback, e2e) | 0 unexpected failures; 8 known limits confirmed |
| Injection | Adversarial suite, 50 distinct units + 4 controls | Plain/structural attacks: 0 of 18 leaked (95% upper bound 17.6%). Obfuscation/paraphrase attacks: 32 of 32 leaked. Controls: 0 false blocks. |
| Injection | Heuristic flag on hostile text | 18 of 21 hostile samples flagged, 0 of 6 benign flagged (small hand-written sets; logging only) |

Demo outcomes:

| Scenario | valid | used_fallback | Reason |
| --- | --- | --- | --- |
| Honest answer | true | false | `OK` |
| Jailbreak, model complies | false | true | `PROTECTED_TERM_LEAK` |
| Hostile note inside evidence | false | true | `PROTECTED_TERM_LEAK` |
| Slow model | false | true | `GEN_TIMEOUT` |
| Unknown NPC | false | true | `SETUP_ERROR` |

## Known limits

* Mock-model suites cannot show how a real LLM behaves. Real-model red-teaming and measurement are still needed.
* The validator is lexical: leet-speak, homoglyphs, separated letters, zero-width characters, reversed text,
  unlisted inflections and paraphrase are not caught (rows `DINJ-05..12`, `ADV-B-*`). Details and suggested
  fixes are in `LEAD_NOTES.md`.
* A timed-out generator thread cannot be killed; a real generator must honour `timeout_s`.
* The injection heuristic is informational only and small; it is not a classifier.
* Progression/discovery rules are not defined in `interfaces.md`; helpers are provided but the rule table
  needs a decision (see `LEAD_NOTES.md`).