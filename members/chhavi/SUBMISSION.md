# Module 8 — Benchmarking Submission

**Member:** Chhavi Sharma  
**Branch:** chhavi/benchmarking  
**Status:** Mock workflow verified; final benchmarking pending.

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

- Cold and warm runs are not yet separated.
- Real integration measurements remain pending.
- Branching baseline comparison remains pending.
- Final questions and scoring rubric need alignment with Ananya.
- Model/backend configuration must be recorded for real runs.
- The current runner stops on target exceptions or missing metrics;
  those failures do not become completed benchmark records.
- The integration lead's review is pending.

No claim is made that Module 8 is fully Done or that any real-model
latency target has been achieved.

## Contribution workflow

Work is contained under `members/chhavi/`.
No PR or merge is required under the current workflow.
The integration lead reviews and copies approved artifacts into
central locations.
