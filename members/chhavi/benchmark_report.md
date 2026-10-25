# Module 8 — Benchmark Report

**Developer:** Chhavi Sharma  
**Branch:** chhavi/benchmarking  
**Date:** 25 October 2026  
**Status:** Mock workflow verified; real performance evaluation pending.

## Purpose

Measure interrogation latency and available backend cost, then compare
dynamic dialogue with the branching baseline under equivalent conditions.

The current run checks the benchmark runner, record conversion, CSV
storage and summary calculations. It does not run an LLM or the actual
validation pipeline.

## Implementation

- `benchmark.py`: record conversion, CSV export, median and p95.
- `test_benchmark.py`: six unit tests.
- `benchmark_questions.json`: twelve provisional scenarios.
- `run_benchmark.py`: explicit mock mode and configurable integration target.

All work is contained under `members/chhavi/`.

## Run configuration

| Setting | Value |
|---|---|
| Run ID | 20261025T141514Z-931f6331 |
| Backend | Mock |
| Model label | MOCK-HARNESS-NO-LLM |
| Python | 3.9.6 |
| pytest | 8.4.2 |
| OS reported by runner | macOS-27.0.1-arm64-arm-64bit |
| Hardware | MacBook Air (Mac14,2), Apple M2, 16 GB RAM |
| Case | case_001 |
| Starting progression | 0 |
| Questions | 12 |
| Repetitions per question | 10 |
| Total records | 120 |
| Concurrency | 1 |
| Startup conditions | Uncontrolled; cold/warm not classified |

## Commands

Run from the repository root:

```bash
python3 -m pytest members/chhavi/test_benchmark.py -v
```

Observed test result:

```text
6 passed in 0.01s
```

Run the mock benchmark:

```bash
python3 -m members.chhavi.run_benchmark --mock --hardware "MacBook - hardware details pending"
```

Each execution creates a new run directory beneath
`members/chhavi/results/`.

## Methodology

Each trial receives a fresh `make_case_001(progression=0)` object.
Questions run sequentially, in the same order, for ten repetitions.

The mock returns a synthetic fallback with reason `GEN_ERROR` for every
question. This is intentional test behavior, not a real generator failure.

CSV columns follow the `BenchmarkRecord` field order. Summary statistics
are grouped by mode and model.

Median uses Python's `statistics.median`. p95 uses linear interpolation
at position `(n - 1) * 0.95` in the sorted measurements.

Unavailable TTFT values are excluded from TTFT statistics. Their sample
count is reported separately. Unavailable values appear as empty CSV
cells and JSON nulls.

## Observed mock results

| Metric | Result |
|---|---|
| Records | 120 |
| Records per question | 10 |
| Median mock total_ms | 0.0024375 ms |
| p95 mock total_ms | 0.0097122 ms |
| Available TTFT samples | 0 |
| Backend-reported cost | Unavailable |
| Synthetic fallbacks | 120 of 120 |

These timings measure construction of a synthetic response in the mock.
They do not measure model inference, retrieval, validation or
player-visible game latency.

Generation and validation fields are default zeros in this mock;
they are not measured stage durations. Correctness and protected-fact
leakage fields remain unscored.

## Evidence files

- `mock-20261025T141514Z-931f6331/benchmark_results.csv`
- `mock-20261025T141514Z-931f6331/summary.json`

The archived files above were uploaded beside this report. The runner
originally generated them beneath its `results/` directory.

## Remaining work


- Connect the reviewed integration implementation.
- Verify the reset hook and collect actual cold/warm model measurements.
- Record model version, backend configuration and available usage.
- Align the final question set and scoring rubric with Ananya.
- Run the branching baseline under matching conditions.
- Evaluate answer correctness and protected-fact leakage.
- Complete SUBMISSION.md and obtain integration-lead review.

## Interpretation and limits

The mock run demonstrates that the benchmark workflow produces records
and consistent summary statistics. It does not establish response quality,
security, latency-target achievement or superiority over branching dialogue.

Real integration results must report model-side TTFT separately from
whole-call total_ms. Cost remains unavailable when the backend does not
report it; no silent estimates are used.

The twelve-question set is provisional. Final comparisons must use the
same questions, NPCs, presented evidence and starting case state.

## Update: Separate cold/warm workflow

Run ID: `mock-20261025T151640Z-05bd5428`

The updated runner completed:
- Cold-labelled mock group: 120 records.
- Warm-labelled mock group: 120 records.
- Six existing helper tests passed.

Evidence:
- `mock-20261025T151640Z-05bd5428/cold/benchmark_results.csv`
- `mock-20261025T151640Z-05bd5428/cold/summary.json`
- `mock-20261025T151640Z-05bd5428/warm/benchmark_results.csv`
- `mock-20261025T151640Z-05bd5428/warm/summary.json`

These groups verify output separation only. The mock has no model
to unload or warm up, so these are not real cold/warm measurements.

For real runs, the runner requires a synchronous reset hook,
a reset description and backend configuration. Each cold sample
follows a reset. Each warm sample follows a reset and warmup calls.
Reset duration is excluded from request timing.

Target exceptions are recorded in summary.json before the run stops.
They are not converted into successful BenchmarkRecords.

Real integration measurements, reset-hook verification, branching
comparison and correctness/leakage scoring remain pending.
