# PoC readout — offline bounded interrogation

Status: Existing repository capability; reproduce locally before signing off
Purpose: Show that real integrated Python modules can answer through a
bounded, validated pipeline without credentials or a model server.

## Run

From repository root with Python 3.11+:

    python -m venv .venv
    python -m pip install -r requirements.txt
    python -m pytest tests/test_reference_flow.py -q
    python scripts/run_security_suite.py
    python scripts/validate_benchmark_questions.py

For the complete test suite:

    python -m pytest

## Inputs and outputs

Golden authored case: shared/fixture_case.py.
Production-facing function: src.pipeline.interrogate().
Contracts: shared/contracts.py and shared/interfaces.md.
Security artifact: results/security_test_log.csv.

## What this PoC demonstrates

- Authorized NPC context and permitted evidence reach generation.
- Untrusted drafts pass through validation or an approved fallback.
- The offline mock allows deterministic acceptance and regression tests.

## What it does NOT demonstrate

Live-model narrative quality, resistance to every paraphrased leak,
production hosting, a persistent game session, human enjoyment, or a
player-visible streaming latency target.

## Next decision

Run Spike 001. Do not replace this README with a claim that the
presentation's entire MVP1 has shipped.
