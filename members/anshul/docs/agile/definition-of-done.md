# Definition of Done

A story is Done only if every applicable item is checked:

- [ ] Acceptance criteria and affected trust boundaries are explicit.
- [ ] Changes follow the repository contribution/integration workflow.
- [ ] Integration lead reviews shared-contract or src/ changes.
- [ ] `python -m pytest` passes; changed behavior has focused tests.
- [ ] Authorization, future-reveal, unsupported-claim, timeout, and fallback
      regressions are considered where relevant.
- [ ] Model drafts are validated before player-visible delivery.
- [ ] Only deterministic, authorized integration actions change case state.
- [ ] Metrics and failure reasons are logged without exposing hidden facts
      or secrets to players; sensitive logs have an access/retention decision.
- [ ] Documentation, diagrams, ADRs, and API/schema contracts are updated.
- [ ] A working increment is demonstrated and accepted by the product owner;
      mentor feedback is recorded.
- [ ] Evidence is labeled mock, real model, human playtest, or NOT RUN.
- [ ] Remaining limitations and follow-up issues are linked.

Release-only additions: replay/security suite passes; human playtest approval
and consent are recorded where applicable; SLOs are measured on the named
deployment, not inferred from the offline mock.

No blanket 80% coverage or <4 s live-latency PASS may be checked without
actual measurement. A story can meet its code DoD while the release remains
blocked on a real-model or human-study gate.
