# Real-model validation (Phase 4) - STATUS: BLOCKED / NOT RUN

**No real-model result exists in this repository.** In the audit environment: no `ollama` binary, nothing listening on
`localhost:11434`, no provider credentials, `ollama.com` unreachable through the sandbox egress policy, and
`members/anshul/dialogue_generator.py` implements only `mock` and `ollama`. Nothing below was executed against a model.

What WAS verified (offline, `tests/test_provider_failure.py`): the shipped Ollama HTTP code path degrades to the standard
fallback with `GEN_ERROR` when the endpoint is dead, the provider name is unknown, or `requests` is missing - no exception,
about 0.2 s.

## Run it yourself (exact steps)

    # 1. Install and start Ollama (https://ollama.com), then pull the generator's default model
    ollama serve &                       # or the desktop app
    ollama pull qwen2.5:3b-instruct      # default in dialogue_generator.py (DEFAULT_MODEL); or choose your own
    python -m pip install requests       # optional dependency used only by the ollama backend

    # 2. Optional live smoke tests (skipped by default)
    RUN_LLM_SMOKE=1 python -m pytest members/anshul -q

    # 3. Same 30 questions, dynamic (real model) vs branching. Writes SEPARATE files; mock evidence is untouched.
    python scripts/run_benchmark.py --all --provider ollama --model qwen2.5:3b-instruct --warm-passes 3 --timeout-s 20
    python scripts/make_benchmark_report.py results/benchmark_results_ollama.csv docs/benchmark-report-ollama.md

Windows PowerShell: set `$env:RUN_LLM_SMOKE="1"` instead of the inline variable.

## What to expect and how to read it

- The validator rejects replies whose wording is not supported by their citations (see `docs/security-residual-risks.md`),
  so a real model will fall back more often than the mock. Report the fallback rate; do not hide it.
- TTFT and token counts appear only if the backend returns them; otherwise the CSV cells stay empty.
- `cost_usd` is empty for local Ollama. The sub-800 ms first-token target can only be judged from a real run's `ttft_ms`.
- Also record: model name/tag, quantization, hardware, Ollama version, and `RUN_LLM_SMOKE` output. Do not commit credentials.
