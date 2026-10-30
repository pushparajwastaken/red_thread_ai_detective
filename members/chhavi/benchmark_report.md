# Module 8 — Benchmark Report

**Developer:** Chhavi Sharma  
**Branch:** chhavi/benchmarking  
**Updated:** 30 October 2026  
**Status:** Real-model baseline measured; limitations and integration-lead review pending.

## Purpose and scope

Measure interrogation latency using the shared BenchmarkRecord contract.
Report median and p95 with sample counts, separate run conditions,
record model and hardware, and distinguish model-side TTFT from
whole-call total_ms.

Unavailable cost is preserved as None, represented by an empty CSV cell.

## Implementation and integration

My implementation under members/chhavi/ includes:

- benchmark.py: record conversion, CSV export and latency statistics.
- run_benchmark.py: development benchmark runner.
- test_benchmark.py: six helper tests.
- test_run_benchmark.py: three runner tests.

The real comparison used the integration lead's scripts/run_benchmark.py
against the integrated module set.

Integration snapshot:

`36f233bd35a1716050a98a334839ba6b4233d91e`

Shared scenarios:

`test_cases/benchmark_questions.json`

The earlier twelve-question local set was provisional. The real comparison
uses the shared thirty-question set, BQ001–BQ030.

## Environment

| Setting | Value |
|---|---|
| Hardware | MacBook Air (Mac14,2), Apple M2, 16 GB RAM |
| Python | 3.9.6 |
| pytest | 8.4.2 |
| Ollama version observed during setup | 0.40.12 |
| Dynamic provider | Local Ollama |
| Dynamic model | qwen2.5:3b-instruct |
| Model ID observed during setup | 357c53fb659c |
| Branching model label | fixed-tree |
| Hardware string recorded in CSV | arm, 8 vCPU, Darwin 27.0.0, Python 3.9.6 |
| Concurrency | Sequential target calls |

The CSV hardware string is retained unchanged. The verified machine
description above supplies the chip and RAM details.

## Measurement methodology

Each mode completed two passes over the same thirty shared scenarios:

- One first pass, labelled cold by the integrated runner.
- One subsequent pass, labelled warm-01.

This produced sixty records per mode and 120 combined records.

Dynamic mode recreates the case using load_case("case_001") and sets
the scenario's progression. Branching mode creates the shared fixture
at the same progression. Both receive the scenario's NPC and presented
evidence IDs.

The integrated runner starts a separate Python process per mode.
It does not explicitly unload or reset the Ollama model.

Consequently, the cold label identifies a first pass after interpreter
startup, not a verified model-unloaded condition. All thirty rows in that
pass must not be interpreted as thirty independently cold model requests.

The warm-01 pass follows the first pass. No additional dedicated warmup
sequence is established by this runner.

Twenty warm passes were originally planned but were not completed.
The interrupted empty final_real_benchmark.csv is excluded from evidence.

## Statistics

Statistics below were calculated from the individual CSV measurements.

- Median describes the middle observed latency.
- p95 uses linear interpolation at sorted position (n - 1) × 0.95.
- n is the number of available measurements in the group.
- Missing measurements are excluded, not replaced with zero.

### Whole-call latency

All values are milliseconds and include fallback-returning calls.

| Mode | Recorded condition | n | Median total_ms | p95 total_ms |
|---|---|---:|---:|---:|
| Dynamic | First pass; labelled cold | 30 | 1646.356 | 2333.508 |
| Dynamic | warm-01 | 30 | 1543.093 | 2253.933 |
| Branching | First pass; labelled cold | 30 | 0.1263125 | 0.1384144 |
| Branching | warm-01 | 30 | 0.1228335 | 0.1284811 |

### Model-side time to first token

| Dynamic condition | Available samples | Median ttft_ms | p95 ttft_ms |
|---|---:|---:|---:|
| First pass | 30 | 391.385 | 495.643 |
| warm-01 | 30 | 214.256 | 485.284 |

TTFT measures the arrival of the model's first output. It does not mean
a validated answer is ready for the player.

total_ms measures the complete interrogation call until the validated
response or trusted fallback returns.

Branching performs no model inference; its TTFT remains unavailable.

## Recorded response outcomes

| Outcome | Dynamic | Branching |
|---|---:|---:|
| Total records | 60 | 60 |
| Valid non-fallback responses | 4 | 54 |
| Fallback responses | 56 | 6 |
| Marked correct by shared automated scorer | 38 | 60 |
| Final-response leak flags | 0 | 0 |

Dynamic reasons:

| Reason | Count |
|---|---:|
| GEN_MALFORMED | 26 |
| UNCITED_ASSERTION | 24 |
| PROTECTED_TERM_LEAK | 6 |
| OK | 4 |

Branching reasons:

| Reason | Count |
|---|---:|
| OK | 54 |
| UNAUTHORIZED_EVIDENCE | 6 |

The shared rubric accepts safe refusals for some non-disclosure scenarios.
Dynamic's 38 scored-correct outcomes include four valid answers and
34 safe fallbacks. Another 22 fallbacks occurred where an answer was
required by the rubric.

Therefore, scored correctness is not equivalent to successful generated
answer delivery.

The six protected-term rejection reasons concern rejected drafts.
The final-response leak flags concern the delivered text and citations.
These are separate measurements.

## Cost

Neither CSV contains a backend-reported dollar cost. cost_usd remains
empty, representing None.

No cost is estimated silently. Unavailable dollar cost does not imply
that local hardware and electricity have no operating cost.

## Testing

Earlier focused Module 8 command:

```bash
python3 -m pytest members/chhavi/test_benchmark.py members/chhavi/test_run_benchmark.py -v
```

Observed earlier result: nine tests passed.

Final offline shared-question and reference-flow command:

```bash
LLM_PROVIDER=mock python3 -m pytest tests/test_benchmark_questions.py tests/test_reference_flow.py -v > members/chhavi/final_test_output.txt 2>&1
```

Observed result:

```text
123 passed, 1 skipped in 3.48s
```

The optional JSON-schema check was skipped.

These offline tests used the mock provider. They do not establish
real-model answer quality or complete security.

## Evidence

Paths below are relative to members/chhavi/:

- dynamic_real_retry.csv: sixty dynamic measurements.
- branching_real_test.csv: sixty branching measurements.
- benchmark_results.csv: exact concatenation of those files, 120 records.
- final_test_output.txt: final offline test output.
- BENCHMARK_CONFIGURATION.md: run-configuration notes.
- diagnostic_20261030T070939Z.json: separate three-question diagnostic.

The diagnostic used an explicit thirty-second timeout. Its timings are
not included in the benchmark statistics.

The earlier dynamic_real_benchmark.csv is a separate preliminary run
and is not included in the selected comparison.

The two mock-20261025... directories retain development evidence.
Their measurements are not mixed with real-model results.

## Reproduction commands

The following commands reproduce the same two-pass scenario structure
using the inspected integrated runner. They are reproduction instructions;
exact historical environment and timeout settings must be confirmed
before claiming an identical execution.

Use new output filenames to preserve existing evidence:

```bash
python3 scripts/run_benchmark.py --mode dynamic --provider ollama --model qwen2.5:3b-instruct --warm-passes 1 --out members/chhavi/dynamic_reproduction.csv
```

```bash
python3 scripts/run_benchmark.py --mode branching --warm-passes 1 --out members/chhavi/branching_reproduction.csv
```

These commands are intended for a checkout containing the integration
snapshot, shared question set, dependencies and running Ollama service.
They do not implement a verified model-cold reset.

## Limitations

- True model-cold conditions were not verified.
- Only two passes per mode were completed; this is an exploratory sample.
- The dynamic timing distribution predominantly describes calls returning
  fallbacks, not successful answer delivery.
- The scorer is lexical and citation-based, not a complete semantic judge.
- Six shared scenarios explicitly require human review; completed human
  review is not established by the CSV.
- Zero final-response leak flags do not prove complete spoiler prevention.
- Model configuration and runtime conditions can affect repeatability.
- First-pass and warm-pass rows are sequential observations, not a
  randomized or counterbalanced player study.
- No player-engagement or broad superiority claim is made.
- No latency target is claimed as achieved merely from model-side TTFT.

## Conclusion and handover

The tested branching baseline was faster and returned fewer fallbacks.
The dynamic configuration showed a high fallback rate, with malformed
generation, uncited assertions and protected-term rejections recorded.

Module 8 preserves and reports these outcomes. Changes to the dialogue
generator, validator or integration belong to their respective owners.

The verified model-cold measurement requirement remains unresolved.
The integration lead should review this limitation and the submission.
