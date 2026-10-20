# Module 5: Validator and Fallback

Owner: Harsh Gupta. Implements the v2 signatures in `shared/interfaces.md`.

```python
from members.harsh.validator import validate_dialogue, make_fallback
```

Run from the repository root (Python 3.11+). No API key, network call or third-party package is needed:

```bash
python -B -m unittest discover -s members/harsh -p test_validator.py -v
python -B -m members.harsh.demo
```

The tests use `shared/fixture_case.py`. The four demo outputs are developer diagnostics; a player UI must show only `DialogueResult.text`.

## Behaviour

1. Validate trusted case/context structure without reading `clues` or `timeline`.
2. Cross-check the request against the NPC. Exact permission sets must match, independent of list order. A future NPC permission gives `AUTH_FUTURE`. When case grants exist, the NPC context cannot exceed them.
3. Verify resolved request payloads against the case when present. Presented evidence must also be discovered and NPC-permitted. Player questions and evidence content never grant permissions.
4. Recognize generator failure statuses. For `ok`, require a nonblank string of at most `MAX_DIALOGUE_CHARS`, well-typed citation lists, valid metrics and the correct NPC ID. Duplicate IDs fail closed. IDs are never trimmed or case-folded.
5. Check every cited fact/evidence ID for existence, authorization and progression gating.
6. Check every authored case term across the entire text, including denials and text with no citations. A term is visible if at least one authorized owner exists. At least one visible owner must be cited. A protected-only term rejects the draft.
7. Accept authorized `cover_story` statements without comparing the sentence to canonical reality. Copy citations/metrics into the result. Failures always return the shared constant fallback with no citations.

Both entry points contain bad-input failures. Unknown/internal exceptions map to `VALIDATOR_ERROR`; malformed case/context structures map to `SETUP_ERROR`. Reason codes never contain fact IDs or exception messages. The result NPC ID comes from the trusted context, never the request or draft.

`make_fallback` sanitizes reasons to the closed `Reason` set. Invalid metrics are discarded; valid metrics are copied. `latency_ms` equals `metrics.total_ms` when metrics exist, otherwise zero. Validation measures `validation_ms` only; Integration owns whole-turn `total_ms`.

## Explicit policy choices

- Authorization is checked before generation status. Non-ok generator payload text/citations are discarded, and the recognized `GEN_*` code is returned when authorization is consistent.
- An unknown status is `SCHEMA_INVALID`.
- Empty request fact/evidence payloads remain supported for v1 compatibility. Nonempty payloads must match the trusted case. Empty case grants are also compatible with v1; a supplied NPC context then remains the authority.
- `FactMeta` missing for a known fact retains the contract's `reveal_at=0` behaviour and contributes no lexical terms. Complete term metadata is the author's responsibility.
- Direct term ownership determines citations. `EvidenceItem.fact_ids` does not automatically cite every fact supported by an evidence item. If a term belongs to both a fact and evidence, either authorized owner can support it.
- Normalize text using NFKC, case-folding and whitespace collapsing, then use escaped whole-word/phrase matches. Normalize no identifiers.
- Inputs are read only. No case progression, inventory, prompt, or LLM call is produced here.

## Known limits

This is lexical boundary checking, not hallucination prevention or semantic entailment. It can accept a false combination of individually authorized terms. `test_known_limit_false_combination_of_visible_terms_can_pass` deliberately records this limitation.

Missing aliases/inflections, paraphrases, translations, zero-width characters and other obfuscations can evade matching. Homonyms and overlapping phrases can cause false positives. Text with no registered case terms needs no citation and can still contain unsupported meaning. Citation presence does not prove a sentence follows from that source.

This module does not implement NLI, timeline algebra, regeneration, prompt filtering, persona scoring, or API timeout enforcement. Integration must avoid displaying draft tokens before validation and must enforce timeouts itself. Tests are deterministic offline checks in the assistant's execution environment, not an end-to-end game or live LLM evaluation.

## Contribution workflow

- Work only in `members/harsh/`, including tests and evidence.
- Push the member branch. **Do not open a PR into `main`; do not merge.** This supersedes the outdated root README steps 4–5.
- The lead reviews and copies approved files into `src/`, owns `shared/`, and resolves interface mismatches.
- Record branch, tested commit, dependencies, exact commands, outputs and limits in `SUBMISSION.md`.
- The root README replacement and missing integration prerequisites are recorded in `LEAD_NOTES.md`, without editing lead-owned files.
- Never commit secrets. Integration uses `LLM_PROVIDER`, `LLM_MODEL`, `LLM_TIMEOUT_S`, `LLM_API_KEY`; blank placeholders belong in the lead-owned `.env.example`. This module requires none of those variables.

Implementation and tests were prepared with AI assistance. Harsh should review and explain the module before handoff.
