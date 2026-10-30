# Module 8: Performance Benchmarking

**Owner:** Chhavi Sharma  
**Project:** Red Thread AI Detective  
**Team:** Quantum  
**Module:** Performance Engineering, Latency Analysis & Runtime Cost Evaluation

## Overview

This module is responsible for evaluating the runtime performance of the Red Thread interrogation pipeline.

The primary objective is to measure the time required to generate, validate, and deliver a safe dialogue response to the player. Since the system uses an AI-based dialogue generator with a validation layer, model generation speed alone is not sufficient to evaluate performance.

The benchmark focuses on **end-to-end validated response latency**, while recording model-level timing, validation overhead, fallback behavior, and runtime cost separately.

The implementation follows the shared v2 contracts defined in `shared/contracts.py` and the behavioral requirements in `shared/interfaces.md`.

## 1. Benchmarking Scope

The benchmarking module is designed to evaluate:

1. **Model responsiveness** — Measure time to first token (TTFT), when available.
2. **Generation latency** — Measure the time spent generating dialogue.
3. **Validation overhead** — Record the time required to validate generated output.
4. **End-to-end latency** — Measure the complete interrogation call until a safe response is ready.
5. **Latency distribution** — Calculate median and p95 across repeated trials.
6. **Fallback behavior** — Track the frequency of fallback responses and associated delays.
7. **Runtime cost** — Record token usage and backend-reported cost where supported.
8. **Baseline comparison** — Compare dynamic AI dialogue with the deterministic branching implementation.

The module is intended to provide reproducible measurements, not assumed performance claims.

## 2. Benchmarking Architecture

The benchmark operates on the existing interrogation pipeline without modifying game state or bypassing validation.

```text
                  Benchmark Runner
                         |
                         v
                Interrogation Request
                         |
                         v
                NPC Context Builder
                         |
                         v
                 Evidence Retrieval
                         |
                         v
                 Dialogue Generator
                         |
                         v
                 Dialogue Validator
                         |
                         v
             Validated Result / Fallback
                         |
                         v
                  Metrics Collection
                         |
                         v
                  BenchmarkRecord
                         |
                         v
                CSV + Statistical Report
```

The runner consumes the trusted `DialogueResult` returned by Integration. It does not directly inspect protected case information, modify NPC permissions, or treat model-generated output as authoritative.

**Timing ownership:**

- Model adapter reports TTFT and generation metrics.
- Validator reports validation duration.
- Integration reports whole-turn `total_ms`.
- Benchmarking collects these measurements and analyzes their distributions.

The player-visible latency is `total_ms`, not TTFT.

## 3. Shared Contracts

The module uses the existing shared data structures.

```python
from shared.contracts import (
    BenchmarkRecord,
    DialogueResult,
    TurnMetrics,
)
```

### TurnMetrics

The following fields are relevant to performance analysis:

| Field | Purpose |
|---|---|
| `mode` | Dynamic or branching dialogue |
| `model` | Model identifier |
| `ttft_ms` | Time to first generated token |
| `generation_ms` | Dialogue generation duration |
| `validation_ms` | Validation duration |
| `total_ms` | Complete interrogation latency |
| `prompt_tokens` | Input token count |
| `completion_tokens` | Output token count |
| `cost_usd` | Backend-reported monetary cost |
| `prompt_chars` | Prompt character count |

Missing measurements are preserved as `None` where supported by the contract.

### BenchmarkRecord

Each record represents one question evaluated in one dialogue mode during a specific run.

The CSV schema follows the field order defined by the shared `BenchmarkRecord` dataclass.

Recorded information includes:

- Run ID and execution mode
- Model and hardware information
- Question ID and NPC ID
- Timing measurements
- Token usage and reported cost
- Validation status
- Fallback usage
- Reason codes
- Answer correctness and protected-fact leakage, when independently evaluated

The runner will not introduce incompatible changes to the shared record format.

## 4. Benchmark Methodology

### Test Configuration

The benchmark uses a fixed question set and the shared case fixture:

```python
from shared.fixture_case import make_case_001
```

All repeated trials should use consistent case state, questions, and model configuration.

Dynamic and branching dialogue must be evaluated against the same questions and case conditions wherever the implementations support equivalent inputs.

### Cold and Warm Runs

Cold and warm measurements are recorded separately.

- **Cold runs:** Trials that include defined initialization or model-loading conditions.
- **Warm runs:** Trials executed after the model and relevant components are initialized.

The classification must be documented for each run group. Cold and warm measurements must not be combined into a single performance claim without disclosure.

### Repeated Execution

Each question will be executed across multiple trials.

For each trial, the benchmark will record available timing metrics, validation outcome, fallback usage, and execution context.

Failures and timeouts will remain part of the recorded results.

### Statistical Analysis

The benchmark report will calculate:

- Sample count (`n`)
- Median latency (p50)
- 95th-percentile latency (p95)
- Minimum and maximum latency, where useful
- Fallback rate
- Validation rejection rate, when sufficient data is available
- Timeout rate
- Cost per turn, when reported

Percentile calculation methods and excluded or missing values will be documented.

A small sample size will be reported as a limitation rather than treated as conclusive evidence of tail latency.

## 5. Dynamic vs Branching Baseline

The benchmark is intended to compare two interrogation modes.

**Dynamic mode**

Uses the AI-based interrogation pipeline:

```python
interrogate(
    case,
    npc_id,
    question,
    presented_evidence_ids=()
)
```

**Branching mode**

Uses the deterministic dialogue baseline:

```python
answer_branching(
    case,
    npc_id,
    question_id,
    presented_evidence_ids=()
)
```

The branching baseline is owned by Ananya. Both modes return `DialogueResult`, allowing comparison through the shared `BenchmarkRecord` structure.

The comparison will consider latency, correctness, fallback behavior, and protected-fact leakage where the shared evaluation rubric provides those results.

A faster response does not automatically indicate better gameplay or greater security.

## 6. Result Storage and Reporting

The planned contribution files are:

```text
members/chhavi/
├── README.md
├── benchmark.py
├── test_benchmark.py
├── benchmark_results.csv
├── benchmark_report.md
└── SUBMISSION.md
```

### Raw Results

`benchmark_results.csv` will contain individual benchmark records rather than only summary statistics.

The final integrated output is expected at:

`results/benchmark_results.csv`

The integration lead is responsible for copying approved output into the shared results directory.

### Performance Report

`benchmark_report.md` will document:

- Benchmark objectives and execution methodology
- Hardware, OS, model and provider configuration
- Cold and warm trial counts
- Median and p95 measurements
- Dynamic versus branching comparison
- Validation and fallback statistics
- Runtime cost observations
- Failed trials and measurement limitations
- Evidence-based optimization recommendations

Raw results will be retained to support independent verification.

## 7. Reproducibility and Testing

The repository provides the following setup and test commands:

```bash
pip install -r requirements.txt
python -m pytest
```

Benchmark-specific execution and test commands will be added after the runner is implemented and verified.

Tests for the benchmarking module should cover:

- Correct mapping of `TurnMetrics` into `BenchmarkRecord`
- CSV header and field ordering
- Handling unavailable TTFT, token counts, and cost
- Median and p95 calculations
- Separation of cold and warm results
- Fallback and invalid-response recording
- Empty datasets and incomplete measurements
- Repeatable execution with a deterministic mock

Mock results are useful for verifying the runner, but they must not be reported as real LLM inference performance.

## 8. Performance and Security Boundaries

The benchmark is an observer of the interrogation pipeline, not a replacement for its security controls.

The following constraints apply:

1. Never bypass validation to obtain faster response times.
2. Never expose unvalidated model tokens as player-visible output.
3. Never modify `CaseState` or advance game progression from benchmark logic.
4. Never use protected facts to construct unauthorized model prompts.
5. Never convert missing timing or cost data into fabricated values.
6. Never remove failed runs to improve reported statistics.
7. Never claim sub-800 ms latency without supporting measurements.

The benchmark will distinguish model-side TTFT from the time required to deliver a validated response.

## 9. Known Dependencies and Limitations

Accurate end-to-end benchmarking depends on the availability of:

- Integrated interrogation pipeline — Pushparaj / Khushi
- Model adapter and generation instrumentation — Anshul
- Shared case fixture and contracts — Team-owned interfaces
- Branching baseline — Ananya

If integration is incomplete, benchmarking infrastructure can be tested using deterministic mocks.

However, mock measurements cannot establish real model latency, model throughput, or production runtime cost.

Additional measurement limitations may include unavailable streaming metrics, provider-specific token reporting, hardware variability, startup overhead, and insufficient trial counts.

These limitations will be documented alongside actual results.

## 10. Contribution and Integration

All implementation, tests, reports, and supporting files are maintained under:

`members/chhavi/`

The contribution follows the team's agreed workflow:

- Develop on the `chhavi/benchmarking` branch.
- Do not modify `shared/`, `src/`, `tests/`, or other members' folders.
- Do not open a pull request into `main` or merge branches.
- Preserve the shared interface contracts.
- Submit tested code and reproducible evidence to the integration lead.
- Document dependencies, execution commands, commit SHA, results, and known limitations in `SUBMISSION.md`.

Contract mismatches or integration blockers will be reported to the team lead rather than resolved through unauthorized changes to shared files.

## 11. Implementation Status

**Status: In progress**

Current focus:

- Benchmark runner development
- Shared contract compatibility
- Metric collection and CSV export
- Statistical reporting
- Integration testing

Verified benchmark results, exact execution commands, and completed test evidence will be added as implementation progresses.

## 12. Expected Deliverable

The completed module should provide a repeatable way to answer:

1. How much time does the interrogation system take to return a validated response?
2. How much latency is introduced by generation and validation?
3. How consistent is response time across repeated trials?
4. How frequently does the system require fallback behavior?
5. How does dynamic dialogue performance compare with the branching baseline?
6. Which measured bottlenecks should be prioritized for optimization?

The objective is to provide measurable performance evidence that the team can use during integration, technical review, and future optimization.

---

**Chhavi Sharma**  
Module 8 — Performance Engineering & Benchmarking  
Team Quantum | Red Thread AI Detective
