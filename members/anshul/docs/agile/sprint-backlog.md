# Working sprint backlog

Status: Proposed next sprint — confirm at Sprint Planning.
Sprint length: 2 weeks.
Sprint goal: Demonstrate that a real-model interrogation can be measured
without bypassing validation or confusing mock results with model results.

| Candidate | Priority | Estimate | Acceptance evidence |
|---|---|---:|---|
| Real-model validation spike | MUST | Time-box: 2 days | Reproducible run or documented BLOCKED result; model/config recorded |
| D1: Review deterministic validation gaps | MUST | 4 pts | Boundary, schema, timeline test cases; gaps reported honestly |
| E1: Event-log contract design | MUST | 5 pts | Typed events, visibility rules, replay tests agreed before implementation |
| D3: Extend injection regression | SHOULD | 3 pts | Baseline cases, expected codes, measured leakage denominator |
| F1: Player-visible delivery design | SHOULD | 8 pts | Sequence test proves no tokens displayed before validation |

These are candidate items, not a claim that capacity or a 20-point commitment
has been approved. The sprint team selects and owns the final sprint backlog.

Reference release plan from the presentation:
- Semester 5 / MVP1: S1–S5; 112 planned points.
- Semester 6 / MVP2: S6–S10; 47 planned points.
- Semester 7 / MVP3: S11–S15; 41 planned points.
- Total: approximately 200 planned points, subject to refinement.

Before closing a story: link its issue, reviewer, tests, demo, evidence, and
any changed ADR or contract. Mark blocked work BLOCKED, not Done.
