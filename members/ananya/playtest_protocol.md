# Ananya Narula — Branching Baseline & Replayability Protocol

## Purpose

Compare Red Thread's dynamic dialogue mode against a deterministic fixed-dialogue
(branching-tree) baseline without changing the mystery, objectives, clue set, or
starting information.

The baseline is intentionally non-LLM and deterministic. It is a control
condition, not evidence that branching dialogue is better or worse.

## Experimental conditions

### Condition A — Dynamic
Use the integrated Red Thread interrogation path with the selected model/configuration.

### Condition B — Branching
Use `answer_branching(...)` with the same case and the same question IDs.

Keep these constant between conditions:

- case/mystery
- participant instructions
- starting clues/evidence
- NPCs available
- question/task set
- approximate session length
- success criterion
- device/environment where practical

Counterbalance which condition a participant sees first when the sample size allows.

## Suggested task protocol

1. Give the participant the same case introduction and starting evidence.
2. Give the participant the same objective: solve the mystery using interrogation
   and available evidence.
3. Record the condition and participant ID.
4. Start the timer when the first task begins.
5. Allow the participant to interrogate NPCs using the predefined question set.
6. Record:
   - task completion
   - time to solve
   - valid clues discovered
   - repeated dialogue
   - contradiction/spoiler incidents
   - number of turns/questions
7. At the end, collect short 1–5 ratings:
   - perceived agency
   - engagement
   - desire to replay
8. Record technical logs separately from participant ratings.
9. Do not remove failed/security cases from the analysis.

## Metrics

| Metric | Definition | Type |
|---|---|---|
| Task completion | Participant reaches the predefined correct solution | objective |
| Time to solve | Seconds from task start to correct solution | objective |
| Distinct valid clues | Count of unique valid clue/fact IDs discovered | objective |
| Repeated dialogue rate | Repeated/near-identical branch responses divided by total dialogue turns | objective |
| Contradiction/spoiler incidents | Count of responses violating expected case knowledge or exposing protected information | objective |
| Turns to solve | Number of interrogation turns before successful solution | objective |
| Perceived agency | Participant rating, 1–5 | subjective |
| Engagement | Participant rating, 1–5 | subjective |
| Desire to replay | Participant rating, 1–5 | subjective |

## Technical replayability proxy

If participant testing is not possible, do **not** claim higher engagement.

Instead report a technical proxy, such as:

- number of distinct valid conversation paths available,
- number of distinct question → response sequences,
- percentage of question sequences producing distinct valid outputs.

Label this explicitly as a **technical replayability proxy**, not player engagement.

## Analysis

Report at minimum:

- sample size (`n`)
- median and range for time-to-solve
- completion count/rate
- median turns-to-solve
- distinct clues discovered
- repeated-dialogue rate
- security/contradiction incidents
- median ratings for agency, engagement and replay desire
- condition order, if counterbalanced

For small samples, describe results as exploratory. Do not generalize beyond the tested participants.

## Security scoring

For each benchmark question, record:

- `answer_correct`
- `leaked_protected_fact`

These are shared scoring fields and should be applied equally to dynamic and
branching modes. The branching implementation must not be scored by a different
standard merely because its answers are scripted.

## Limitations to report

- A fixed branching tree cannot represent all free-form player wording.
- A small participant sample cannot establish broad engagement superiority.
- Technical path diversity is not equivalent to human replayability.
- Results depend on the exact question set, case state, and model configuration.
- The current repository has an empty `test_cases/` directory; the local question
  fixture exists only to make Ananya's component executable during development.
  The final comparison should use the team's shared question set once populated.
