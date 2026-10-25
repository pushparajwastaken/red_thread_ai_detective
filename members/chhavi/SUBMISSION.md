# Module 8 — Benchmarking Submission

**Member:** Chhavi Sharma  
**Branch:** chhavi/benchmarking  
**Status:** Benchmark tool implemented; separate mock cold/warm groups verified. Real evaluation and integration-lead review pending.

## Reference commit

Implementation and evidence snapshot before adding this submission:

`fdb4bbd5a7d85520f07a5037ed5d1b02ef9f8665`

## Files

All paths below are relative to `members/chhavi/`.

- `benchmark.py`
- `test_benchmark.py`
- `benchmark_questions.json`
- `run_benchmark.py`
- `benchmark_report.md`
- `mock-20261025T141514Z-931f6331/benchmark_results.csv`
- `mock-20261025T141514Z-931f6331/summary.json`
- `SUBMISSION.md`
- `mock-20261025T151640Z-05bd5428/cold/benchmark_results.csv`
- `mock-20261025T151640Z-05bd5428/cold/summary.json`
- `mock-20261025T151640Z-05bd5428/warm/benchmark_results.csv`
- `mock-20261025T151640Z-05bd5428/warm/summary.json`

## Environment and dependencies

| Component | Verified version/details | In requirements.txt? |
|---|---|---|
| Python | 3.9.6 | Runtime; not a pip dependency |
| pytest | 8.4.2 | Yes, listed as `pytest` without a version pin |
| Hardware | MacBook Air, Mac14,2, Apple M2, 16 GB RAM | Not applicable |

The benchmark implementation uses Python standard-library modules and
the project's shared contracts and fixture. No additional runtime
packages were introduced.

Mock mode requires no API key or network access.

## Setup and test commands

Run from the repository root:

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest members/chhavi/test_benchmark.py -v
```

Observed focused test result:

```text
6 passed in 0.01s
```

Tests cover median, p95, empty inputs, result conversion, missing metrics,
summary grouping and unavailable TTFT.

The full repository test suite has not been verified for this submission.

## Benchmark command

Command used for the archived run:

```bash
python3 -m members.chhavi.run_benchmark --mock --hardware "MacBook - hardware details pending"
```

Hardware was subsequently verified as Apple M2 with 16 GB RAM.
The archived files retain the original hardware label.

For future mock runs, use:

```bash
python3 -m members.chhavi.run_benchmark --mock --hardware "MacBook Air (Mac14,2), Apple M2, 16 GB RAM"
```

Each execution writes a new directory beneath `members/chhavi/results/`.

## Verified evidence

- 12 provisional questions, repeated 10 times each.
- 120 CSV records.
- Median mock total_ms: 0.0024375 ms.
- p95 mock total_ms: 0.0097122 ms.
- 120 intentional synthetic fallbacks.
- TTFT, token counts and cost unavailable.
- Correctness and protected-fact leakage unscored.

These are mock response-construction measurements. They do not establish
real model latency, game performance or security.

## Known limits and remaining work

- Separate cold/warm output groups are implemented and exercised in mock
  mode. Actual cold/warm model measurements remain pending.
- Real runs require a synchronous reset hook, reset description and
  backend configuration. Reset behavior needs integration-lead review.
- Reset duration is excluded from request latency. Model loading is
  included only when it occurs inside the measured target call.
- Runner-specific tests for reset/warmup order, output separation and
  failure logging remain to be added. The six existing tests cover
  benchmark helper functions.
- Real integration measurements and branching comparison remain pending.
- Final questions and scoring rubric need alignment with Ananya.
- Answer correctness and protected-fact leakage remain unscored.
- Target exceptions are recorded in summary.json before the run stops.
  Failed attempts are not converted into BenchmarkRecords.
- Warmup calls are excluded from measured records and reported costs.
- Integration-lead review is pending.

Module 8 is not yet fully Done. No real-model latency or security
target is claimed as achieved.

## Contribution workflow

Work is contained under `members/chhavi/`.
No PR or merge is required under the current workflow.
The integration lead reviews and copies approved artifacts into
central locations.

## Latest mock workflow verification

Run ID: `mock-20261025T151640Z-05bd5428`

Hardware: MacBook Air (Mac14,2), Apple M2, 16 GB RAM.

Command:

```bash
python3 -m members.chhavi.run_benchmark --mock --hardware "MacBook Air (Mac14,2), Apple M2, 16 GB RAM"
```

Observed output:

```text
cold: 120 records
warm: 120 records
```

The existing helper test suite also passed:

```text
6 passed in 0.01s
```

The 240 measured mock records verify the runner's output workflow.
They do not establish real cold/warm model performance or security.
The mock intentionally returns synthetic fallbacks.

The earlier reference commit identifies the initial implementation
snapshot; it does not include this later runner update. The updated
submission commit can be identified through this file's Git history.
