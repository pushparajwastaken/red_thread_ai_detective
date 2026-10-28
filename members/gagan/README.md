# Module 3: Evidence Retrieval

Owner: Gagan. Implements the v2 signature in `shared/interfaces.md`.

```python
from members.gagan.retriever import retrieve_evidence
```

Run from the repository root (Python 3.11+). No API key, network call or third-party package is needed:

```bash
python -B -m unittest discover -s members/gagan -p test_retriever.py -v
python -B -m members.gagan.demo
```

The tests use `shared/fixture_case.py`. Evidence content returned by this module is **data**; the player UI must never display it directly and the generator must label it untrusted.

## What it does

```python
retrieve_evidence(question: str, permitted_evidence_ids: list[str],
                  *, case: CaseState, top_k: int = 3) -> list[EvidenceItem]
```

Given a player question, return the few evidence items most relevant to it, using only evidence the NPC is allowed to see right now.

1. Walk `permitted_evidence_ids` (the NPC's permitted list, supplied by Integration). Duplicates are processed once.
2. Skip any ID that is not a `str`, is unknown to `case.evidence`, or has `reveal_at > case.progression` (spoiler gate).
3. Score each remaining item against the question (see below). Items scoring 0 are not returned.
4. Sort by `(score desc, evidence_id asc)` and return the first `top_k` as **fresh copies** of `EvidenceItem`.

## Scoring (deliberately simple)

| Signal | Points |
| --- | --- |
| Each distinct authored `EvidenceItem.terms` entry found in the question as a whole word/phrase | 3 |
| Each distinct word (3+ letters, not a stop word) shared by the question and the item's `content` | 1 |

Text is normalized with NFKC, case-folding and whitespace collapsing before matching. Matching uses escaped whole-word patterns, so `will` does not match `willing`.

## Explicit policy choices

- **Permission is never derived from the question.** Mentioning `E009`, or writing "ignore previous instructions", changes nothing. Only the permitted list and `case` decide what can be returned.
- **Zero-score items are not returned.** "No relevant evidence" is a valid answer and is an empty list. (The shared interface does not say; this is the safest reading.)
- **IDs are exact.** `e001` or ` E001` never match `E001`.
- **Fail closed.** Wrong argument types, a non-`CaseState` case, `top_k` that is not an int >= 1 (booleans rejected), or any unexpected internal error returns `[]` and never raises.
- **Bounded work.** Only the first `MAX_QUESTION_CHARS` (2000) characters of the question are used.
- **Read only.** The case and the input list are never modified; returned items are copies.
- **`case` is keyword-only**, per the v2 signature.
- **Does not check `discovered_evidence_ids`.** Per `shared/interfaces.md`, Integration filters what the player has presented. This module filters by permission and reveal stage only.
- **Does not read `clues`, `timeline`, `canonical_facts` or `fact_meta`.** It cannot leak what it never reads.

## Known limits

This is lexical keyword matching, not semantic search.

- No stemming: `glove` does not match `gloves` unless the case author lists both in `terms` (same rule the shared contract gives for fact terms). `test_known_limit_inflection_not_matched` records this.
- Synonyms, paraphrases, typos and translations are not matched.
- Content overlap uses the item's own text, so hostile evidence content can attract matches. Example: in the demo, a question containing "instructions" retrieves `E003` (the authored injection fixture) because its content contains that word. This is not a leak: `E003` is permitted for the gardener, and its text is returned only as untrusted data for the generator's delimited block. The validator and the generator prompt remain the controls against acting on it.
- Common words that appear in many items can produce loose matches; the stop-word list is small and hand-written.
- Ranking quality has not been evaluated on a real case, only on the golden fixture.

## Contribution workflow

- Work only in `members/gagan/`, including tests and evidence.
- Push the member branch. **Do not open a PR into `main`; do not merge.** This supersedes the outdated root README steps 4-5.
- The lead reviews and copies approved files into `src/`, and owns `shared/`.
- Record branch, tested commit, dependencies, exact commands, outputs and limits in `SUBMISSION.md`.
- Never commit secrets. This module requires no environment variables.

Implementation and tests were prepared with AI assistance. Gagan should review and be able to explain the module before handoff.
