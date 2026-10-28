# Integration handoff notes

No shared contract changes are required. `retrieve_evidence` uses the exact v2 signature (keyword-only `case`, returns `list[EvidenceItem]`).

## For Integration (Pushparaj, Khushi)

- Pass the NPC's `permitted_evidence_ids` from `NPCContext`. This module does **not** check `case.discovered_evidence_ids`; filter `presented_evidence_ids` separately, as `shared/interfaces.md` Module 6 describes.
- An empty list is a normal result. Do not treat it as an error. Bad input also returns `[]` (it never raises), so a wiring mistake looks the same as "nothing relevant". Check argument types in Integration.
- Returned items are copies, safe to put into `DialogueRequest.evidence`. Their `content` is untrusted data and must stay inside the generator's delimited evidence block.

## Policies to review

- Items with score 0 are omitted rather than returned as low-ranked filler.
- Scoring weights (term 3, content word 1) and the stop-word list are first-pass choices, adjustable in `retriever.py` constants.
- Hostile evidence content can attract matches on its own words (see README Known limits). If the lead wants content excluded from scoring, only authored `terms` would count; that is a one-line change but lowers recall for items like `E003` that have no terms. Please tell me which you prefer.

## Observation (not changed)

`CONTRIBUTING.md` is empty at the reviewed base. No action taken.
