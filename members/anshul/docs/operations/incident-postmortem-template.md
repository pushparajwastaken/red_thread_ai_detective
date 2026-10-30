# Blameless incident review — [incident ID and title]

Status: TEMPLATE / NOT AN ACTUAL INCIDENT
Incident commander: [name]
Start / detection / mitigation / resolution: [times and time zone]
Severity and affected environment: [e.g., playtest build, staging, production]

## Player impact
[Number of sessions; whether a secret leaked, an accusation failed, or
interrogation became unavailable. State what is unknown.]

## Timeline
| Time | Observation or action | Evidence link |
|---|---|---|
| | | |

## Technical explanation
Trigger:
Contributing conditions:
Trust boundary or control that failed:
Why detection did or did not catch it:

## Five whys
1. Why did the player-visible failure occur?
2. Why did the immediate control fail?
3. Why was that condition possible?
4. Why did tests/monitoring not prevent or detect it?
5. Which system-level change prevents recurrence?

## Recovery and verification
[Rollback, fallback, affected data, replay results, owner, sign-off.]

## Action items
| Action | Owner | Due | Verification test | Issue |
|---|---|---|---|---|
| | | | | |

## Follow-up
[Update relevant ADR, security regression, case-authoring guidance,
runbook, and release gate. Review without assigning personal blame.]
