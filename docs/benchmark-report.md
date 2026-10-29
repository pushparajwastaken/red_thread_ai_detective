# Benchmark report - Sprint 1 (dynamic vs branching)

> Every number below is generated from `results/benchmark_results.csv` by `scripts/make_benchmark_report.py`. Regenerate with:
> `python scripts/run_benchmark.py --all --warm-passes 20 && python scripts/make_benchmark_report.py`

## Read this first - what these numbers are and are not

- **Dynamic mode here = the real pipeline with the OFFLINE DETERMINISTIC MOCK generator.** No LLM was called (no network, no credentials, no local model server in this environment). Its latencies measure *pipeline overhead* (context build, retrieval, prompt build, validation) only; they say **nothing** about real-model latency, and the mock's answers are canned.
- **The dynamic `answer_correct` rate is therefore NOT a quality result.** The mock quotes the alphabetically-first authorized fact verbatim and cites only that fact (plus at most one evidence term), so it fails the rubric on any question that needs a different fact (e.g. cover stories). Dynamic-vs-branching *quality* is **unmeasured** until a real model is run on this same question set (blocked: no model/credentials here).
- **Branching** = Ananya's deterministic fixed-tree baseline (`model=fixed-tree`); its answers are authored per question from the same set, so a high correct rate mostly reflects authoring, not generalisation.
- **TTFT: unavailable** (empty in the CSV) for both modes: the mock is not streaming and the baseline has no model. Player-visible latency is `total_ms`. The project's sub-800 ms first-token target is **not evaluated**.
- **Cost: unavailable** (empty). No backend reported usage; nothing was estimated.
- Lexical rubric limits apply: paraphrased leaks and false combinations of authorized terms are not detected; rows flagged `requires_human_review` in the question set need a person.

## Setup

- Questions: **30** (`test_cases/benchmark_questions.json`, 10 categories x 3, case_001, NPCs gardener/cook).
- Hardware/environment: AMD64 Family 25 Model 68 Stepping 1, AuthenticAMD, 16 vCPU, Windows 11, Python 3.13.15
- Runs: each mode in its own fresh process. **Cold** = first pass after interpreter start (30 samples/mode). **Warm** = 20 subsequent passes (600 samples/mode). Cold/warm are separated via `run_id` suffix (`-cold`, `-warm-NN`).
- Models: dynamic: ['mock'], branching: ['fixed-tree'].
- Percentiles: median and nearest-rank p95 of `total_ms`, with n.
- Dynamic latency includes a daemon worker thread per call (whole-call deadline enforcement). Cold and warm medians differ by less than run-to-run noise at this scale; no cold-vs-warm effect is claimed.

## Latency (ms, player-visible `total_ms`)

| Mode | Run | median | p95 | n |
|---|---|---:|---:|---:|
| dynamic | cold | 0.913 | 1.177 | 30 |
| dynamic | warm | 0.917 | 1.157 | 600 |
| branching | cold | 0.488 | 0.635 | 30 |
| branching | warm | 0.506 | 0.605 | 600 |

Component medians (warm, ms; branching has no generation or validation stage, so those components are recorded as 0.0 by the baseline, not measured): dynamic: generation 0.058, validation 0.271; branching: generation 0.000, validation 0.000.

## Outcomes under the shared rubric (cold pass, one sample per question; warm passes are identical because both modes are deterministic here)

| Mode | questions | answer_correct | leaked_protected_fact | fallback | valid |
|---|---:|---:|---:|---:|---:|
| dynamic | 30 | 26/30 | 0/30 | 0/30 | 30/30 |
| branching | 30 | 30/30 | 0/30 | 3/30 | 27/30 |

Determinism check across all passes: **identical outcomes for every question**.

### Correctness by category (cold pass)

| category | dynamic (mock) correct | branching correct |
|---|---:|---:|
| authorized_fact | 2/3 | 3/3 |
| cover_story | 0/3 | 3/3 |
| direct_injection | 3/3 | 3/3 |
| evidence_grounded | 3/3 | 3/3 |
| fallback | 3/3 | 3/3 |
| future_fact | 3/3 | 3/3 |
| general_interrogation | 3/3 | 3/3 |
| indirect_injection | 3/3 | 3/3 |
| unauthorized_fact | 3/3 | 3/3 |
| unsupported_claim | 3/3 | 3/3 |

### Fallback reasons (cold pass)

- dynamic: OK=30
- branching: OK=27, UNAUTHORIZED_EVIDENCE=3

The two modes intentionally differ on questions BQ025-BQ027 (presented evidence the NPC may not see): the baseline falls back with `UNAUTHORIZED_EVIDENCE`; `interrogate()` silently drops such IDs and answers on the remaining evidence (documented in the question set's `mode_expectations`).

## Not measured / pending

- Real-model (e.g. Ollama) dynamic latency, TTFT, token counts and quality: **not run** (no model/credentials/network); see docs/real-model-validation.md.
- Human playtests of the branching baseline: **pending** - protocol in `members/ananya/playtest_protocol.md`, results template `members/ananya/playtest_results_template.csv` (empty of data).
- Cost: unavailable. Sub-800 ms TTFT target: not evaluated.
