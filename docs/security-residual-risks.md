# Security: controls, tests and KNOWN RESIDUAL RISKS

The validator is a deterministic **lexical** control. It is not hallucination prevention. Evidence: `results/security_test_log.csv`
(regenerate: `python scripts/run_security_suite.py`), `tests/test_reference_flow.py`, `tests/test_validator_claim_support.py`,
`tests/test_timeout_robustness.py`.

## What the validator enforces (members/harsh/validator.py)

1. Authorization of every cited fact/evidence ID against trusted NPC context and `reveal_at` (exact, case-sensitive IDs).
2. Term ownership: a visible case term owned only by unauthorized/future items -> `PROTECTED_TERM_LEAK`; owned by an
   authorized-but-uncited item -> `UNCITED_ASSERTION`.
3. **Claim support (added after audit finding UNSUP-03)**, applied to any reply that cites something or mentions a case term:
   every word must be a function word, a persona word, or a word of a *cited* statement; every sentence must share a content
   word with a citation or be a recognised deflection; every citation must be visible in the reply; a cited statement may not
   be negated, and a cited negation (e.g. the cover story "never left the kitchen") may not be dropped. Failure ->
   `UNCITED_ASSERTION`.

## Residual risks (not fixed; documented, with tests where noted)

| Risk | Why it remains | Evidence |
|---|---|---|
| Term-free, **uncited** accusations ("He did it.") pass | v2 contract: text with no case terms needs no citation. `SUPPORT_SCOPE="all"` closes it but rejects most free-form role-play; needs lead approval | `UNSUP-10`; `test_term_free_uncited_replies_pass_by_default_documented_residual`; `test_strict_scope_all_closes_the_residual` |
| Recombination of authorized words that changes meaning ("The figure heard glass break in the greenhouse" citing F001+F002) | no semantic parsing | `UNSUP-11`; `test_known_limit_false_combination_of_visible_terms_can_pass` |
| Word order / role swaps ("Lord Ashby argued with Lady Ashby") | tokens are checked as a set, not a parse | not separately tested |
| Paraphrase of protected facts using words that are not listed terms | ownership is by listed terms | existing Harsh tests document the limit |
| False positives: harmless wording outside the cited statements, or a negation absent from the cited evidence, is rejected | fail-closed by design | `IINJ-03` |
| `UNCITED_ASSERTION` is reused for "reply not supported by its citations" | the closed `Reason` set has no separate code and `shared/` is unchanged | lead decision: add a dedicated code later |
| A stuck backend thread cannot be killed | Python limitation; daemonised, capped at `MAX_ABANDONED_WORKERS=8`, new calls then fail fast with `GEN_TIMEOUT` until workers drain | `tests/test_timeout_robustness.py` |
| Real-model behaviour (prompt-injection resistance, JSON compliance, fallback rate) | no real model was available | `docs/real-model-validation.md` |
| The question-level injection heuristic (`flag_input`) is informational only | by design; authorization never depends on it | - |
