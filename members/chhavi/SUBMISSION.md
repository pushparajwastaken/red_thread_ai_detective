# Module 8 — Benchmarking Submission

**Member:** Chhavi Sharma  
**Branch:** chhavi/benchmarking  
**Updated:** 30 October 2026  
**Status:** Benchmark implementation and real comparison evidence submitted for review. Verified model-cold measurements remain unresolved.

## Scope and contribution

My Module 8 implementation provides:

- DialogueResult-to-BenchmarkRecord conversion.
- CSV export using the shared contract field order.
- Median and linearly interpolated p95 calculations.
- Sample counts and separate summaries.
- Focused tests for helper functions and the development runner.
- Benchmark evidence, methodology and limitations.

The real-model comparison used the integration lead's
`scripts/run_benchmark.py` with the integrated module set and shared
thirty-question set. That central runner is team integration code,
not my individual implementation.

No generator, validator, shared contract or central implementation
changes are included in this submission.

## Reference snapshots

Integrated code used for the real comparison and final offline checks:

`36f233bd35a1716050a98a334839ba6b4233d91e`

Earlier personal implementation and mock-evidence snapshot:

`3cd3cabe7162ad729ce0a83d06b551400ef471da`

These identify historical snapshots. The final uploaded evidence and
documentation are available on `chhavi/benchmarking`; their commits
are recorded in GitHub history.

Reproduction requires the integrated snapshot, not only the older
personal branch's dependency versions.

## Files

Paths below are relative to `members/chhavi/`.

### Implementation and tests

- `benchmark.py`
- `run_benchmark.py`
- `test_benchmark.py`
- `test_run_benchmark.py`
- `benchmark_questions.json` — earlier provisional development questions.

### Final evidence and documentation

- `benchmark_results.csv` — 120 combined records.
- `dynamic_real_retry.csv` — 60 dynamic records.
- `branching_real_test.csv` — 60 branching records.
- `final_test_output.txt`
- `benchmark_report.md`
- `README.md`
- `SUBMISSION.md`

### Preserved development evidence

- `mock-20261025T141514Z-931f6331/`
- `mock-20261025T151640Z-05bd5428/`

Mock measurements are not included in the final real comparison.

The real comparison uses the shared questions at
`test_cases/benchmark_questions.json`, BQ001–BQ030.

## Environment and dependencies

| Component | Observed version/details | Dependency status |
|---|---|---|
| Python | 3.9.6 | Runtime |
| pytest | 8.4.2 | Listed in the earlier inspected requirements.txt without a version pin |
| Ollama | 0.40.12 observed during setup | Separate local application |
| Dynamic model | qwen2.5:3b-instruct | Local Ollama model |
| Model ID | 357c53fb659c observed during setup | Model identifier |
| Hardware | MacBook Air, Mac14,2, Apple M2, 16 GB RAM | Execution machine |
| requests | Used by Anshul's Ollama adapter | Installed version and current requirements.txt membership require verification |
| jsonschema | Optional test dependency | JSON-schema check skipped in the final offline run |

My helper implementation uses Python standard-library modules and
the project's shared contracts.

Real inference additionally depends on the integrated generator's
backend requirements. Unverified package versions are not invented.

Local Ollama inference does not require an API key for this setup.

## Test commands and observed results

Run commands from the repository root.

### Earlier focused Module 8 tests

```bash
python3 -m pytest members/chhavi/test_benchmark.py members/chhavi/test_run_benchmark.py -v
```

Observed result:

```text
9 passed
```

Coverage includes calculations, empty inputs, record conversion,
missing metrics, grouping, reset order, warmup exclusion,
output separation and failure logging.

This was verified on the personal implementation at that stage.

### Final integrated offline checks

```bash
LLM_PROVIDER=mock python3 -m pytest tests/test_benchmark_questions.py tests/test_reference_flow.py -v > members/chhavi/final_test_output.txt 2>&1
```

Observed result:

```text
123 passed, 1 skipped in 3.48s
```

The optional JSON-schema check was skipped.

These commands verify the selected test files, not the entire repository
test suite. Offline mock tests do not establish real-model answer quality.

## Real benchmark evidence

| Setting | Completed work |
|---|---|
| Shared scenarios | 30 |
| Dynamic passes | One first pass and one subsequent pass |
| Branching passes | One first pass and one subsequent pass |
| Records per mode | 60 |
| Combined records | 120 |
| Cost | Unavailable; empty CSV cells represent None |

`benchmark_results.csv` is an exact concatenation of
`dynamic_real_retry.csv` and `branching_real_test.csv`.
Original records and run IDs are preserved.

Twenty warm passes were planned but were not completed.
The interrupted empty `final_real_benchmark.csv` is not evidence
and is excluded from the submission.

## Reproduction commands

The following reproduce the inspected runner's two-pass scenario structure.
They are reproduction instructions, not a claim that every historical
environment variable and timeout setting has been recovered.

Use a checkout of the integrated snapshot, its dependencies,
the shared question set and a running Ollama service with the model
already downloaded.

Use new output names to preserve archived evidence:

```bash
python3 scripts/run_benchmark.py --mode dynamic --provider ollama --model qwen2.5:3b-instruct --warm-passes 1 --out members/chhavi/dynamic_reproduction.csv
```

```bash
python3 scripts/run_benchmark.py --mode branching --warm-passes 1 --out members/chhavi/branching_reproduction.csv
```

## Results summary

Whole-call latency, in milliseconds:

| Mode | Condition | n | Median | p95 |
|---|---|---:|---:|---:|
| Dynamic | First pass; labelled cold | 30 | 1646.356 | 2333.508 |
| Dynamic | warm-01 | 30 | 1543.093 | 2253.933 |
| Branching | First pass; labelled cold | 30 | 0.1263125 | 0.1384144 |
| Branching | warm-01 | 30 | 0.1228335 | 0.1284811 |

Statistics include fallback-returning calls. p95 uses linear interpolation.

Dynamic model-side TTFT:

| Condition | n | Median ttft_ms | p95 ttft_ms |
|---|---:|---:|---:|
| First pass | 30 | 391.385 | 495.643 |
| warm-01 | 30 | 214.256 | 485.284 |

TTFT is not validated player-visible response time.
The whole-call measure is total_ms.

Branching TTFT is unavailable.

## Recorded outcomes

| Outcome | Dynamic | Branching |
|---|---:|---:|
| Valid non-fallback responses | 4 | 54 |
| Fallbacks | 56 | 6 |
| Marked correct by shared scorer | 38 | 60 |
| Final-response leak flags | 0 | 0 |

The shared scorer accepts safe refusals for some questions.
Dynamic's 38 scored-correct outcomes include 34 safe fallbacks;
22 other fallbacks occurred where an answer was required.

Dynamic reasons:

- GEN_MALFORMED: 26.
- UNCITED_ASSERTION: 24.
- PROTECTED_TERM_LEAK: 6.
- OK: 4.

Branching reasons:

- OK: 54.
- UNAUTHORIZED_EVIDENCE: 6.

Protected-term rejection reasons describe rejected drafts.
Final-response leak flags describe delivered responses.
Zero flags are not proof of complete security.

## Known limitations and handover

- The runner labels the first pass cold but does not explicitly unload
  or reset the Ollama model. True model-cold measurements are unverified.
- The subsequent pass follows the first pass; there is no separately
  established dedicated warmup sequence in this integrated runner.
- Only two passes per mode were completed.
- Dynamic timings predominantly describe fallback-returning calls.
- Automated scoring is lexical and citation-based.
- Six scenarios explicitly require human review; completed human review
  is not established by these CSVs.
- Exact historical timeout/environment settings and the requests version
  still require verification.
- Model and validator issues are reported for their owners to review;
  they were not hidden or fixed by weakening validation.
- No latency target, complete spoiler prevention or player-engagement
  advantage is claimed.
- Integration-lead review remains pending.

The model-cold requirement must not be marked fully achieved without
further evidence or an explicit scope decision from the integration lead.

## Contribution workflow

Changes and submitted evidence are confined to `members/chhavi/`.

No PR into main or merge is performed by me under the current workflow.
The integration lead reviews and copies approved artifacts into the
central locations.
