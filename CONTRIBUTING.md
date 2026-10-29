# Contributing

Authoritative contract: `shared/interfaces.md` (+ `shared/contracts.py`, `shared/fixture_case.py`).
Only the integration lead edits `shared/`. To request a contract change, send the lead the failing
scenario and a proposed diff.

## Workflow (supersedes any "open a PR and merge" text)

1. Work only in `members/<name>/`. Do not edit `src/`, `shared/`, `tests/` or other members' folders.
2. Develop against `shared/fixture_case.py` (`make_case_001()`); use the shared contract types.
3. Push your **own branch**. **Do not open PRs into `main`. Do not merge.**
4. Deliver `members/<name>/SUBMISSION.md`: branch, commit SHA, files, dependencies (name == version and
   whether in `requirements.txt`), exact run command, real test output, known limits. Do not invent SHAs or results.
5. The lead reviews, copies approved work, resolves interface mismatches, and runs the acceptance suite.

## Rules

- IDs are exact and case-sensitive; never trim or case-fold them.
- Reason codes never contain fact IDs. Only `DialogueResult.text` is shown to the player.
- Untrusted: model output, the player question, evidence content. They never change trusted state.
- No secrets in git. Use `.env.example`. No new dependencies without justification and a pinned version.
- Before handing in: `python -m pytest` from the repo root must pass.
