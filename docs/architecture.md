# Red Thread architecture

Status: Current-state description plus explicitly marked target design
Owner: Integration lead
Review trigger: Any change to shared contracts, trust boundaries, persistence,
or player-visible dialogue delivery.

## Purpose

Let a player interrogate characters freely without letting generated dialogue
rewrite case truth, disclose unauthorized facts, or become a trusted state update.

## Non-negotiable trust boundary

- The case engine owns canonical facts and progression.
- NPC context contains only facts and evidence authorized for that NPC at
  the current progression.
- Player questions, evidence content, and model drafts are untrusted data.
- Only integration may advance trusted case state, through deterministic rules.
- The generator receives an authorized request, not the complete CaseState.
- A draft is never displayed before validation. On failure, display the
  approved fallback; do not expose internal reason codes to the player.

The authoritative type and behavioral contracts are shared/contracts.py and
shared/interfaces.md. This document explains them; it does not override them.

## Current implementation

Production-facing Python entry point: src.pipeline.interrogate().
src/pipeline.py wires member case-knowledge, retrieval, generation, and
validation implementations. Tests use a deterministic offline mock by default.
The branching baseline, security suite, and benchmark are evaluation tools.

Do not infer a deployed web API, client, SQL database, or production LLM
service from this architecture diagram.

## Target extensions — not yet asserted as implemented

MVP1: durable case/event persistence, a player UI, evidence board, formal
accusation flow, improved claim validation, and measured real-model behavior.
MVP2: cross-case graph, bounded memory, and typed agent actions.
MVP3: adversarial evaluation, observability, and release SLOs.

Each extension requires an ADR, contract review, migration plan, and tests
before it becomes part of the current-state diagram.
