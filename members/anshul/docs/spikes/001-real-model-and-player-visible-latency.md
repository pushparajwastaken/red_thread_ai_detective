# Spike 001 — Real-model validation and safe delivery

Status: Proposed; NOT RUN
Time box: 2 working days
Owner: Assign at planning
Decision needed: Can the selected provider produce usable, validated
interrogation at an acceptable player-visible latency and fallback rate?

## Questions

1. What are median and p95 total turn times, separately from model TTFT?
2. How often does generation fail schema, authorization, or claim checks?
3. Can the client show a response incrementally without showing unvalidated
   text? If not, what player-visible waiting treatment is acceptable?
4. What happens on timeout, malformed output, and provider outage?

## Method

Use the existing shared benchmark questions and real production entry point.
Record provider/model/version, hardware, configuration, cold/warm runs, sample
counts, and raw results. Run the security scenarios as well. Do not relax
validation to improve latency or answer rate. Have a human inspect a sample
of accepted answers and fallbacks.

## Current evidence

The offline mock verifies integration behavior but cannot answer the
real-model latency or quality questions. Existing documentation records
real-model validation as blocked in its audited environment.

## Deliverable

A one-page readout with measurements, reproducible commands, failure samples,
limitations, and one recommendation: adopt, revise, or defer. If no provider
is available, record BLOCKED and the prerequisite; do not invent results.
