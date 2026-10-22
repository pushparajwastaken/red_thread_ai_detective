# Module 6: Integration (`interrogate`)

Owner: Khushi, with Pushparaj (integration lead). Implements the v2 signature in
`shared/interfaces.md`:

```python
from members.khushi.integration import interrogate, interrogate_traced

result = interrogate(case, "gardener", "Where were you at nine?", presented_evidence_ids=["E001"])
result, trace = interrogate_traced(case, "gardener", "Where were you at nine?")   # + telemetry
```

Run from the repository root (Python 3.11+). No API key, network call or third-party package is
needed:

```bash
python -B -m unittest discover -s members/khushi -p test_integration.py -v   # 39 tests
python -B members/khushi/run_checks.py                                       # evidence logs
python -B -m members.khushi.demo                                             # five demo turns
```

A player UI must show only `DialogueResult.text`. `reasons` and `TurnTrace` are developer diagnostics.

## What it does

```
build_npc_context -> filter presented evidence -> retrieve_evidence -> DialogueRequest
-> generate_dialogue (one call, hard deadline) -> validate_dialogue -> DialogueResult
```

1. Never raises. Any failure ends in `make_fallback` with a reason code (`SETUP_ERROR`,
   `GEN_ERROR`, `GEN_TIMEOUT`, `VALIDATOR_ERROR`, or the validator's own code).
2. `facts` are resolved only from `npc.authorized_fact_ids`. The full `CaseState` never reaches the model.
3. Presented evidence must be discovered, revealed (`reveal_at <= progression`) AND permitted for that
   NPC. Anything else is dropped silently (counted in `trace.presented_dropped`).
4. `request.evidence` = presented evidence first, then retrieved evidence, de-duplicated. Content is
   always re-read from the case by ID; whatever the retriever returned is never trusted.
5. IDs are exact strings: no trimming and no case folding.
6. Exactly one generator call per turn. No retries, no regeneration loop.
7. `metrics.total_ms == result.latency_ms` is the whole call, measured here. `ttft_ms` is model-side only.
8. `cost_usd` is passed through from the generator and is never estimated (`None` stays `None`).
9. `interrogate()` does not mutate the case. `advance_progression()` (monotonic) and
   `discover_evidence()` are the only state changes and are driven by deterministic game rules, never by
   model text.

## How this module supports the three issues raised in the EPAM review

| Issue | What this module provides | What it does NOT do |
| --- | --- | --- |
| Latency (<800 ms proposal) | Per-stage timings (`setup/retrieval/generation/validation/total`), model-side `ttft_ms` vs player-visible `total_ms`, a wall-clock deadline that also protects against a generator that ignores `timeout_s`, a single generator call per turn, and tokens withheld until validated. Measured overhead of everything except the model: see `results/integration_summary.json`. | It does not run a local model and cannot make a model faster. A local quantized model plugs in behind `Deps.generate_dialogue` (Module 4). The 800 ms figure remains a proposal until measured with a real model. |
| Cost | `cost_usd` passthrough, `summarize_traces()` (total is `None` if any turn is unknown), question capped at 500 chars, retrieval `top_k=3`, only authorized facts in the prompt, no retries. | It does not estimate price. Per-session cost must be measured with a real backend (tokens x price). |
| Prompt injection | Exclusion by construction (the model never sees unauthorized facts or future evidence), authoritative evidence resolution, a fail-closed pipeline, a 42-scenario red-team table plus a 50-unit adversarial suite logged in `results/`, and informational heuristic flags for hostile player text and hostile evidence text. | It does not block on the heuristic (the validator is the control). It cannot protect a secret the NPC legitimately holds beyond what the validator catches. See Known limits. |

## Swapping in the real modules

`default_deps()` in `integration.py` wires Harsh's real validator plus stubs (`stubs.py`) for Modules
2-4. When the lead copies the real modules into `src/`, change only the imports inside `default_deps()`.
`interrogate()` itself does not change.

## Known limits

* The adversarial suites use a MOCK model. They test the integration layer and the validator, not a real
  LLM's resistance to jailbreaks. Real-model red-teaming (Devansh) is still required.
* The current validator is lexical. In the 50-unit suite, plain and structural attacks (18 units) produced
  0 leaks, but all 32 obfuscated or paraphrased spoilers (leet-speak, Cyrillic homoglyphs, separated
  letters, zero-width characters, reversed text, unlisted inflections, paraphrase) passed through. These are
  logged as `KNOWN LIMIT` rows and reported to the lead (`LEAD_NOTES.md`). Do not describe the system as
  preventing hallucination or guaranteeing zero spoilers.
* A Python thread cannot be killed. After a timeout the abandoned generator call may keep running in the
  background, so a real generator must honour `request.timeout_s` itself (as the contract requires).
* The injection heuristic is a small hand-written pattern list (18 of 21 hostile samples flagged, 0 of 6
  benign false positives). It is a logging aid, not a classifier.
* Latency numbers in `results/` use an instant mock model on the machine named in the summary file.

## Workflow (replaces the wrong "open a pull request / merge into main" text in the root README)

Work only in `members/khushi/`. Push your own branch (`khushi/integration-v2`). Do not open a pull
request into `main` and do not merge. The lead reviews and copies approved code into `src/`.