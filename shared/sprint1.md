# Red Thread AI Detective
# Sprint 1 — Agile Sprint Planning & Execution Plan

**Sprint Name:** Case Engine & Epistemic Schema  
**Methodology:** Scrum-inspired Agile  
**Repository:** https://github.com/pushparajwastaken/red_thread_ai_detective  
**Team Size:** 12 members  
**Sprint Duration:** To be agreed during Sprint Planning  
**Sprint Goal:** Deliver a deterministic mystery-case specification and executable case engine with explicit suspect knowledge boundaries, validated evidence, and reproducible acceptance tests.

---

## 1. Product Vision

Red Thread is an AI detective game in which players investigate a mystery by interrogating suspects and examining evidence. Suspects must operate within explicit knowledge boundaries: they must not reveal information they have not been authorized to know.

The system separates canonical truth, suspect-authorized statements, evidence, and generated dialogue. The validator enforces the authorization boundary before any generated response is shown to the player.

### Sprint 1 deliverables

1. One mystery case containing exactly one victim and three suspects.
2. Ten clues and a consistent ground-truth timeline.
3. A deterministic Case Engine compatible with `shared/contracts.py`.
4. An explicit epistemic model defining what each suspect can know.
5. Deterministic evidence-reveal and progression rules.
6. A testable fact-knowledge query.
7. Integrity, security, regression, and reproducibility tests.
8. A documented integration path and measurable acceptance evidence.

## 2. Scrum Roles and Responsibilities

| Role | Owner | Responsibility |
|---|---|---|
| Sprint Lead / Integration Lead | Pushparaj Singh Parmar | Sprint coordination, integration, shared contracts, acceptance gate |
| Development Team | All 12 members | Deliver assigned work, test it, document results and raise blockers |
| Quality Assurance Contributors | Preksha Wani, Paras Gupta, Devansh Vinayak | Property testing, regression testing and adversarial validation |
| Sprint Review Participants | Team and mentor | Inspect completed work and verify acceptance evidence |

The integration lead is responsible for coordinating the team, but every member remains accountable for their own deliverables.

---

## 3. Product Backlog

The backlog is prioritized by dependency and risk.

| ID | Backlog item | Priority | Estimate |
|---|---|---|---:|
| PB-01 | Define the mystery case and ground-truth timeline | P0 | 5 SP |
| PB-02 | Validate case structure and references | P0 | 3 SP |
| PB-03 | Define the suspect knowledge matrix | P0 | 5 SP |
| PB-04 | Specify epistemic rules and query semantics | P0 | 3 SP |
| PB-05 | Define clue dependencies and reveal progression | P0 | 5 SP |
| PB-06 | Audit interface-contract compatibility | P0 | 3 SP |
| PB-07 | Implement integration acceptance planning | P0 | 3 SP |
| PB-08 | Add knowledge-boundary property tests | P0 | 5 SP |
| PB-09 | Add adversarial security scenarios | P1 | 5 SP |
| PB-10 | Audit deterministic behavior and reproducibility | P1 | 3 SP |
| PB-11 | Define the branching baseline and comparison criteria | P1 | 3 SP |
| PB-12 | Prepare sprint evidence and submission documentation | P1 | 2 SP |

**Total initial estimate: 48 story points.**

Story points are provisional estimates, not hours or a guaranteed commitment. The team should refine them during Sprint Planning based on the actual repository state and its historical capacity. P0 items are required for the core Sprint Goal; P1 items support validation and future comparison.

## 4. Randomized Member Assignments

The following responsibilities differ from the previous primary module assignments. The assignment order is shuffled; the underlying interface contracts and shared-file ownership remain unchanged.

| No. | Member | New assignment | Deliverable |
|---:|---|---|---|
| 1 | Paras Gupta | Case consistency and referential integrity | `members/paras/case_integrity.py` |
| 2 | Ananya Narula | Mystery narrative and ground-truth timeline | `members/ananya/case_timeline.md` |
| 3 | Harsh Gupta | Epistemic policy specification | `members/harsh/epistemic_policy.md` |
| 4 | Gagan Chaurasia | Clue dependency and reveal graph | `members/gagan/clue_dependency_graph.md` |
| 5 | Preksha Wani | Knowledge-boundary property testing | `members/preksha/test_epistemic_properties.py` |
| 6 | Pushparaj Singh Parmar | Sprint integration plan and acceptance gate | `members/pushparaj/integration_plan.md` |
| 7 | Richa Bharti | Mystery case content design | `members/richa/case_content.md` |
| 8 | Chhavi Sharma | Determinism and reproducibility audit | `members/chhavi/determinism_audit.md` |
| 9 | Devansh Vinayak | Epistemic threat model and attack scenarios | `members/devansh/threat_model.md` |
| 10 | Khushi Kumari | Case progression state-machine specification | `members/khushi/progression_state_machine.md` |
| 11 | Anand Kumar Sahni | Suspect knowledge matrix | `members/anand/suspect_knowledge_matrix.csv` |
| 12 | Anshul Prajapati | Interface-contract compatibility audit | `members/anshul/contract_compatibility.md` |

### Assignment rules

- Each member owns their assigned deliverable.
- Members may collaborate on interfaces and review one another's work.
- Collaboration does not authorize editing another member's directory.
- These work packages do not replace the original module owners' responsibilities in the shared contract.
- If a new deliverable conflicts with an existing module contract, submit a change proposal to the integration lead.

---

## 5. User Stories and Acceptance Criteria

### US-01: Deterministic Mystery Case

**As a game engine,** I need a validated mystery case so that every interrogation refers to the same authoritative events and facts.

Acceptance criteria:

- Exactly one victim, three suspects and ten distinct clues.
- A complete, internally consistent ground-truth timeline.
- Stable identifiers and valid references.
- Explicit distinction between canonical facts and authored in-world lies.
- Invalid cases fail with the contract-defined error.
- Identical case loads produce equivalent case state.

### US-02: Suspect Knowledge Boundaries

**As a game designer,** I need each suspect's authorized knowledge to be explicit so that the game does not reveal protected information.

Acceptance criteria:

- Each suspect has an explicit set of authorized facts and evidence.
- Future information is excluded until its reveal condition is satisfied.
- Unknown suspect IDs are rejected as specified by the contract.
- Returned NPC contexts do not alias mutable collections in the case.
- Canonical truth does not automatically become suspect knowledge.

### US-03: Epistemic Query

**As an integration developer,** I need to query whether a suspect can know a fact so that authorization behavior can be tested independently.

Proposed interface, subject to approval by the integration lead:

`can_suspect_know(case, npc_id, fact_id)`

Acceptance criteria:

- Identical input and case state produce identical output.
- Authorization and reveal progression are both respected.
- Unknown facts and suspects have explicit, documented behavior.
- Exact, case-sensitive IDs are preserved.
- The query does not reveal protected fact contents through error messages.

### US-04: Deterministic Evidence Progression

**As an investigator,** I need evidence to become available only when its conditions are satisfied.

Acceptance criteria:

- Each clue has a defined reveal condition.
- Dependencies do not contain impossible cycles.
- Evidence retrieval skips unknown, unauthorized and unrevealed IDs.
- Results are ordered deterministically by score descending and ID ascending.
- Only Integration changes progression or discovered evidence.

### US-05: Verifiable Security Boundaries

**As a system maintainer,** I need repeatable tests to verify that player questions and hostile evidence cannot override trusted state.

Acceptance criteria:

- Direct and indirect prompt-injection scenarios are included.
- Unauthorized facts and future evidence remain protected.
- Malformed model output results in the agreed safe fallback.
- The security test log records expected and actual reason codes.
- No test relies only on subjective prose to declare a pass.

---

## 6. Definition of Ready (DoR)

A backlog item is Ready when:

- [ ] The objective and expected deliverable are clear.
- [ ] Acceptance criteria are documented.
- [ ] An owner is assigned.
- [ ] Dependencies and required interfaces are identified.
- [ ] The member can work using the existing fixture and contracts.
- [ ] The task is small enough to make measurable progress within the sprint.
- [ ] Required input data and test commands are available.
- [ ] Any unresolved contract ambiguity has been raised to the integration lead.

If a task is blocked by an unresolved interface, the member should continue independent specification or test preparation rather than modifying shared contracts independently.

---

## 7. Definition of Done (DoD)

A task is Done only when its applicable completion checks pass.

### Implementation and specification

- [ ] The deliverable satisfies its acceptance criteria.
- [ ] The implementation or specification follows `shared/contracts.py` and `shared/interfaces.md`.
- [ ] Inputs, outputs, errors and edge cases are documented.
- [ ] No unauthorized shared-file changes have been made.
- [ ] No secrets or credentials have been committed.

### Testing and verification

- [ ] Relevant tests have been executed.
- [ ] Actual test output is recorded.
- [ ] Expected and actual behavior agree.
- [ ] Regression tests are included for discovered defects where applicable.
- [ ] Known limitations are explicitly documented.
- [ ] The work can be reproduced by another team member.

### Submission

- [ ] Work is committed on the member's own branch.
- [ ] `members/<name>/SUBMISSION.md` is complete.
- [ ] Branch name and commit SHA are included.
- [ ] Dependencies and exact versions are listed.
- [ ] Exact execution and test commands are provided.
- [ ] The submission is ready for integration-lead review.

### Sprint-level Definition of Done

Sprint 1 is Done only when:

- [ ] The mystery case meets the required content specification.
- [ ] Case integrity and reference validation pass.
- [ ] Suspect knowledge boundaries have unambiguous semantics.
- [ ] The epistemic query is implemented or explicitly integrated and verified against the approved contract.
- [ ] Reveal progression and evidence authorization are deterministic.
- [ ] The reference acceptance suite passes against the integrated implementation.
- [ ] Required adversarial tests pass or any unresolved failures are explicitly recorded as sprint blockers.
- [ ] All required work is reviewed and integrated.
- [ ] The mentor can inspect the implementation, tests and evidence in the repository.

A document describing an implementation is not proof that the implementation works. Where the deliverable is a specification, its completion requires review; where it is executable code, it requires successful tests.

---

## 8. Agile Workflow and Ceremonies

### A. Sprint Planning

**Purpose:** Agree on the Sprint Goal, scope, capacity and ownership.

Agenda:

1. Review the product backlog and current repository state.
2. Confirm the Sprint Goal and priority of each item.
3. Check Definition of Ready.
4. Review dependencies and identify blockers.
5. Confirm individual ownership and acceptance criteria.
6. Agree on the sprint duration and planned scope.
7. Record the Sprint Backlog.

**Output:** An agreed Sprint Backlog with owners, acceptance criteria and dependencies.

### B. Daily Scrum

**Purpose:** Inspect progress toward the Sprint Goal and adapt the day's plan.

Each member reports:

1. What was completed since the previous check-in?
2. What is the next concrete deliverable?
3. Is anything blocked?
4. Is another member's interface or output required?

Keep the meeting focused on coordination. Technical discussions that require extended debugging should continue separately with the relevant members.

### C. Backlog Refinement

**Purpose:** Clarify upcoming work before implementation begins.

Activities:

- Break oversized items into smaller deliverables.
- Review acceptance criteria.
- Identify missing fixture fields or interface definitions.
- Update estimates when assumptions change.
- Raise contract change requests to the integration lead.

### D. Sprint Review

**Purpose:** Demonstrate working outcomes to the team and mentor.

Demonstrations should include:

- Loading the mystery case.
- Inspecting the victim, suspects, clues and timeline.
- Querying suspect knowledge for authorized and unauthorized facts.
- Demonstrating reveal progression.
- Running acceptance and adversarial tests.
- Reviewing reproducibility evidence and known limitations.

The review should use actual code and test output, not only slides or progress claims.

### E. Sprint Retrospective

**Purpose:** Improve the team's process for the next sprint.

Discuss:

- What worked well?
- What caused delays or duplicated effort?
- Were interface contracts sufficiently clear?
- Were task estimates realistic?
- Did members receive timely reviews?
- Which one or two process changes should be adopted next sprint?

**Output:** A short list of specific improvements with owners.

---

## 9. Task Board and Work-in-Progress Policy

Use the following board columns:

1. **Product Backlog** — not yet selected.
2. **Ready** — meets Definition of Ready.
3. **In Progress** — actively being worked on.
4. **In Review** — submitted for technical or specification review.
5. **Changes Requested** — review feedback must be addressed.
6. **Done** — satisfies the applicable Definition of Done.

Rules:

- Every task has one accountable owner.
- A member should finish or unblock current work before starting unnecessary parallel work.
- A pull request into `main` is not part of the current contribution workflow.
- The integration lead reviews submissions and copies approved work into the appropriate central location.
- Blocked tasks must include the blocker, the person needed to resolve it and the next action.

### Suggested WIP limit

Aim for one primary in-progress task per member. Additional work is acceptable when it unblocks another member or is explicitly agreed during the Daily Scrum.

---

## 10. Branching, Submission and Integration Workflow

Each member must:

1. Work in `members/<name>/`.
2. Develop against `shared/fixture_case.py` and `make_case_001()`.
3. Use the shared contracts as read-only dependencies.
4. Commit work to their own branch.
5. Include `members/<name>/SUBMISSION.md`.
6. Report the commit SHA and exact test command.
7. Submit work for integration-lead review.

The submission must include:

- Task name and scope.
- Files created or modified.
- Branch and commit SHA.
- Dependencies with exact versions and whether already listed in `requirements.txt`.
- Execution and test commands.
- Actual test output.
- Known limitations and unresolved issues.

**Repository restrictions:** Members must not edit `shared/`, `src/`, central `tests/` or other members' directories. Only the integration lead modifies shared contracts and performs central integration. Do not merge branches or open pull requests into `main` under the current workflow.

Development command:

`pip install -r requirements.txt && python -m pytest`

---

## 11. Risk Register

| Risk | Impact | Mitigation | Owner |
|---|---|---|---|
| Case narrative contradicts canonical facts | Invalid mystery | Independent timeline and integrity review | Ananya, Paras |
| Knowledge semantics are ambiguous | Incorrect information exposure | Approve epistemic policy before integration | Harsh, Anand |
| Clue dependencies create unreachable states | Broken investigation progression | Validate the reveal graph and state machine | Gagan, Khushi |
| Interface mismatch between members | Integration delays | Contract compatibility audit and early review | Anshul, Pushparaj |
| Prompt injection bypasses intended restrictions | Protected information leak | Adversarial testing and fail-closed validation | Devansh |
| Nondeterministic results | Unreliable acceptance tests | Reproducibility checks and stable ordering | Chhavi |
| Tests are submitted too late | Defects found near sprint end | Write acceptance tests in parallel with specifications | Preksha, Paras |
| Integration becomes a bottleneck | Delayed completion | Small submissions and early contract checks | Pushparaj |

---

## 12. Metrics and Reporting

Track the following measures throughout the sprint:

- **Sprint completion:** completed backlog items versus committed items.
- **Acceptance-test pass rate:** passing required tests divided by executed required tests.
- **Defect count:** open defects by severity.
- **Blocked work:** number of blocked items and time spent blocked.
- **Review turnaround:** time between submission and review.
- **Determinism:** repeated executions that produce equivalent outputs for identical inputs.
- **Security outcomes:** unauthorized-disclosure attempts detected and correctly rejected.

Do not invent performance figures or report proposed latency targets as measured results. Benchmark results must include sample counts and distinguish model-side TTFT from player-visible total latency.

Story points are planning estimates; they should not be used to compare individual members' productivity.

---

## 13. Sprint Exit Checklist

Before declaring Sprint 1 complete, verify:

- [ ] All required case content is present.
- [ ] Case integrity validation passes.
- [ ] Suspect knowledge boundaries are explicit and testable.
- [ ] The fact-knowledge query behaves according to its approved contract.
- [ ] Evidence reveal and progression rules are deterministic.
- [ ] Reference-flow and regression tests pass.
- [ ] Adversarial scenarios have been executed and recorded.
- [ ] Benchmark and baseline artifacts are correctly labeled.
- [ ] All member submissions include reproducible evidence.
- [ ] Integration review is complete.
- [ ] Remaining risks and deferred work are recorded for Sprint 2.
- [ ] The sprint review and retrospective have been completed.

**Sprint outcome:** A validated, deterministic foundation for Red Thread that is ready for subsequent dialogue, investigation and gameplay development without weakening the epistemic trust model.
