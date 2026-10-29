# Module 5 submission: Harsh Gupta

- Branch: `harsh/validator-fallback-v2`
- Tested implementation commit SHA: `166864a4b351dbea51e95df419ec92c07d425d35`
- Base main commit: `720634d26b5c41c3427ebea6f10f59712d5d0666`
- This handoff file is a subsequent documentation-only commit. The implementation SHA above identifies the exact code, tests and captured outputs being submitted; it is intentionally not a self-referential hash of this file.
- Test date: 20 October 2026.
- Scope: only `members/harsh/`. Lead reviews/copies approved code into `src/` and owns shared interfaces. No PR into main and no merge.
- Push status: pending authentication. The attempted `git push -u origin harsh/validator-fallback-v2` failed because this execution environment could not authenticate to GitHub. No remote branch creation or push is claimed.

## Files

| File | Purpose |
| --- | --- |
| `validator.py` | `validate_dialogue` and `make_fallback`, imported shared v2 contracts |
| `test_validator.py` | 64 offline tests with additional parameterized subcases |
| `demo.py` | Four deterministic developer scenarios |
| `test-output.txt` | Actual verbose test output |
| `demo-output.jsonl` | Actual accepted/fallback demo results |
| `README.md` | Usage, policy choices, limitations and correct branch-only workflow |
| `LEAD_NOTES.md` | Proposed root README/environment-template fixes and integration notes |
| `SUBMISSION.md` | This handoff record |

## Dependencies and environment

| Dependency | Exact tested version | Already in root requirements.txt? |
| --- | --- | --- |
| Python (CPython runtime) | `Python == 3.12.14` | No; runtime, not a pip dependency. Root README requires Python 3.11+. |
| Standard library (`unittest`, `dataclasses`, `re`, `unicodedata`, `math`, `time`, `json`, `copy`) | Bundled with `Python == 3.12.14` | No external packages required. |
| `shared.contracts`, `shared.fixture_case` | Repository base commit above, v2 contracts | Local project modules; not pip dependencies. |

No new third-party dependency. Root `requirements.txt` contains unpinned `pytest`; pytest was not installed or used for the submitted test run. The suite is implemented with standard-library unittest and can also be collected by pytest when the lead's environment provides it.

Measured execution environment: assistant execution environment, Linux `6.18.55`, `x86_64`, CPython `3.12.14`. These are not measurements from Harsh's laptop. Tests are offline, use no API keys and make no LLM/network calls.

## Exact commands

From the repository root:

```bash
python -B -m unittest discover -s members/harsh -p test_validator.py -v
python -B -m members.harsh.demo
```

To regenerate the submitted evidence files:

```bash
python -B -m unittest discover -s members/harsh -p test_validator.py -v > members/harsh/test-output.txt 2>&1
python -B -m members.harsh.demo > members/harsh/demo-output.jsonl
```

## Actual test output

Exit code: `0`. Full output: `test-output.txt`.

```text
----------------------------------------------------------------------
Ran 64 tests in 0.012s

OK
```

The elapsed time is an observed unit-test duration, not an application latency benchmark.

Demo outcomes:

| Scenario | valid | used_fallback | Reason |
| --- | --- | --- | --- |
| Authorized fact | true | false | `OK` |
| Missing citation | false | true | `UNCITED_ASSERTION` |
| Protected term | false | true | `PROTECTED_TERM_LEAK` |
| Generator timeout | false | true | `GEN_TIMEOUT` |

The tests cover authorization mismatches, future grants, exact ID matching, unknown/unauthorized citations, fact/evidence term ownership, uncited statements, denials containing secrets, direct/indirect injection scenarios, allowed cover stories, reveal boundaries, malformed inputs, schema length boundaries, fixed fallback text, metrics copying, no state mutation and internal exception handling. Assertions use reason codes and flags rather than model prose.

## Known limits and untested integration

- Lexical only. This does not establish hallucination prevention. The suite deliberately includes a false-combination example that passes because its individual terms are authorized and cited.
- Term coverage is authored. Missing aliases, inflections, paraphrases, translations and obfuscated text can evade detection. Homonyms and overlapping phrases can be over-rejected.
- Missing fact metadata follows the shared v1 default of reveal stage zero and supplies no terms. Empty case grants and request payloads retain compatibility with the shared dataclass defaults. See README for exact policy choices.
- No semantic judge, timeline-algebra validation, regeneration, persona scoring, API calls or timeout enforcement is implemented here. Integration owns whole-turn timing and must withhold draft tokens until validation succeeds.
- `tests/test_reference_flow.py` is referenced by the shared interface documentation but absent from the reviewed repository. End-to-end game acceptance and live-provider evaluation were not run or claimed.
- Root README has outdated PR/merge instructions and `.env.example` is empty at the reviewed base. The proposed lead-owned corrections are in `LEAD_NOTES.md`; those root files were not edited.

Implementation, tests and documentation were prepared with AI assistance. The lead should review the implementation and run integration acceptance before copying it into the application.

## Lead integration update (claim-support audit)

Audit finding UNSUP-03: an unsupported claim next to a valid citation passed. `validate_dialogue` now also runs a deterministic
claim-support check (`_support_check`, see `docs/security-residual-risks.md`). The shared contract, `Reason` codes, fallback text
and `used_fallback` semantics are unchanged; unsupported content is reported as `UNCITED_ASSERTION`. Default scope keeps the v2
rule "text with no case terms needs no citation" (`SUPPORT_SCOPE="grounded"`); `"all"` is implemented but off pending approval.
One existing test was edited and flagged in-file: `test_known_limit_false_combination_of_visible_terms_can_pass` (its example
sentence is now rejected; the documented limitation is preserved with a sentence built only from cited words).
Tests: `python -m pytest members/harsh tests/test_validator_claim_support.py -q`.
