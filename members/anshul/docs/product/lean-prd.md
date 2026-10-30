# Lean PRD — Red Thread

Status: Proposed product scope; not a shipped-feature inventory
Product owner: Student team / faculty, to confirm
Audience: Players who enjoy deduction and questioning characters; secondarily,
researchers evaluating trustworthy open-ended game dialogue.

## Problem

Scripted interrogation limits the questions players can ask. Unbounded
generation risks spoilers, unsupported clues, and contradictions. Players
need freedom to question characters while the mystery remains fair and solvable.

## Outcome

A player can explore evidence, question an NPC in their own words, connect
clues, and make an evidence-supported accusation. The game, not the model,
determines whether that accusation is correct.

## MVP1 scope

One authored case; bounded NPC knowledge; free-text interrogation;
validated responses and safe fallback; discovered-evidence interaction;
evidence board and formal accusation; reproducible evaluation.

Out of scope for MVP1: autonomous NPC truth changes, cross-case killer reveal,
production-scale multiplayer, and claims of proven live-model safety.

## User needs

- Ask an unanticipated question without automatically seeing a spoiler.
- Understand an NPC's answer well enough to continue investigating.
- Discover, present, and connect evidence.
- Receive non-spoiling feedback on an accusation.
- Resume investigation without NPCs gaining knowledge they should not have.

## Success measures — targets, not results

Pre-register numerator, denominator, test set, model, and run conditions:
- Unauthorized disclosure rate: target <5% for MVP1; <1% in a defined
  adversarial suite for MVP3.
- Unsupported-claim rate: target <5% on a human-reviewed sample.
- Fallback rate: target <15%, alongside a player-rated usefulness measure.
- Player-visible median turn latency: target <4 s on a named live backend.
- Correct, evidence-supported accusation: target >=70% of playtesters.

A mock-only benchmark cannot establish live-model latency or dialogue quality.

## Release acceptance

The case is solvable without guessing; every required clue can be found;
NPC permissions are enforced; no unvalidated text reaches the player;
a replayable test set and a limitations report accompany the demo.
