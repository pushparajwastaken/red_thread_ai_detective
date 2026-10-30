# RAID log

Status: Living working draft. Review at planning and fortnightly connect.
Owner fields marked TBD must be assigned by the team.

| ID | Type | Item | Evidence / impact | Response or decision | Owner | Status |
|---|---|---|---|---|---|---|
| R1 | Risk | Semantic or term-free unsupported replies pass validation | Lexical residual; threatens mystery integrity | Add measured adversarial and human review; decide SUPPORT_SCOPE through contract review | Validation lead TBD | Open |
| R2 | Risk | Validation rejects harmless natural dialogue | High fallback harms play | Measure fallback rate and usefulness together; curate safe deflections | Product + validation TBD | Open |
| R3 | Risk | Model tokens shown before validation | Potential irreversible spoiler | Client must buffer draft; test player-visible boundary | Integration lead | Open for future UI |
| R4 | Risk | Abandoned backend workers after timeout | Resource exhaustion | Exercise whole-call deadlines; monitor/cap abandoned workers | Runtime lead TBD | Monitor |
| A1 | Assumption | A live model can meet the desired latency and quality | Mock cannot establish this | Run Spike 001 before promising an SLO | Research lead TBD | Unvalidated |
| A2 | Assumption | A full MVP1 case is solvable by players | No completed human playtest in audited record | Test clue reachability and conduct consented playtest | Product owner TBD | Unvalidated |
| I1 | Issue | Current src/ wiring imports member modules | Makes ownership/deployment boundary less clear | Lead decides whether/when to copy approved modules into src/ | Integration lead | Open decision |
| D1 | Dependency | Live provider, hardware, or credentials | Required for real-model claims | Obtain approved test environment; never commit credentials | Faculty/infra TBD | Pending |
| D2 | Dependency | Human participants and study approval | Required for player-experience claims | Confirm protocol, consent, recruitment, and analysis plan | Research lead TBD | Pending |

At each review: update probability/impact and evidence, assign an owner,
record a due date, and close an item only with a link to its verification.
