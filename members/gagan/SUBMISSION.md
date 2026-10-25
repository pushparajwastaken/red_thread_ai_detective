# Module 3 submission: Gagan

- Branch: `gagan/evidence-retrieval`  <!-- FILL IN: your actual branch name -->
- Tested implementation commit SHA: `<FILL IN after you commit: git rev-parse HEAD>`
- Base main commit: `<FILL IN: git merge-base HEAD origin/main>`
- Test date: 22 October 2026.
- Scope: only `members/gagan/`. Lead reviews/copies approved code into `src/` and owns shared interfaces. No PR into main and no merge.
- Push status: `<FILL IN: pushed / pending>`. Do not claim a push that has not happened.

## Files

| File | Purpose |
| --- | --- |
| `retriever.py` | `retrieve_evidence`, imports shared v2 contracts |
| `test_retriever.py` | 35 offline unit tests |
| `demo.py` | Six deterministic developer scenarios |
| `test-output.txt` | Actual verbose test output |
| `demo-output.jsonl` | Actual demo results |
| `README.md` | Usage, policy choices, limitations and branch-only workflow |
| `LEAD_NOTES.md` | Integration notes and questions for the lead |
| `SUBMISSION.md` | This handoff record |

## Dependencies and environment

| Dependency | Exact tested version | Already in root requirements.txt? |
| --- | --- | --- |
| Python (CPython runtime) | `Python == 3.12.3` | No; runtime, not a pip dependency. Root README requires Python 3.11+. |
| Standard library (`re`, `unicodedata`, `unittest`, `copy`, `json`) | Bundled with Python 3.12.3 | No external packages required. |
| `shared.contracts`, `shared.fixture_case` | Repository main at time of work | Local project modules. |

No new third-party dependency. Tests use standard-library `unittest` (also collectable by pytest). They are offline, use no API keys and make no LLM/network calls.

Measured in the assistant's Linux execution environment, not on Gagan's machine. Re-run locally and update this file with your own results before submitting.

## Exact commands

From the repository root:

```bash
python -B -m unittest discover -s members/gagan -p test_retriever.py -v
python -B -m members.gagan.demo
```

To regenerate the evidence files:

```bash
python -B -m unittest discover -s members/gagan -p test_retriever.py -v > members/gagan/test-output.txt 2>&1
python -B -m members.gagan.demo > members/gagan/demo-output.jsonl
```

## Actual test output

Exit code `0`. Full output: `test-output.txt`.

```text
Ran 35 tests in 0.003s

OK
```

The elapsed time is an observed unit-test duration, not an application latency benchmark.

Demo outcomes (`progression` is set per scenario):

| Scenario | Returned IDs |
| --- | --- |
| term_match | `E001` |
| content_match | `E003` |
| no_match | none |
| future_gated (progression 0) | none |
| future_revealed (progression 2) | `E009` |
| injection_in_question | `E003` (matched on the word "instructions"; see README Known limits) |

The tests cover matching (terms, content words, case, NFKC, whole-word), permission and spoiler gating, exact case-sensitive IDs, question-cannot-grant-permission, ordering and tie-breaks, `top_k`, determinism, copies instead of aliases, no input mutation, fail-closed bad input, bounded question length, and building a valid `DialogueRequest` from the output.

## Known limits and untested integration

- Lexical only; no stemming, synonyms or semantic matching. Ranking quality was checked only on the golden fixture.
- Not tested together with the real `load_case`, `build_npc_context`, generator or `interrogate` flow; those modules are owned by others. Compatibility was checked only against the shared dataclasses.
- `tests/test_reference_flow.py` is referenced by `shared/interfaces.md` but was not present, so no end-to-end acceptance is claimed.

Implementation, tests and documentation were prepared with AI assistance. The lead should review the implementation before copying it into the application.
