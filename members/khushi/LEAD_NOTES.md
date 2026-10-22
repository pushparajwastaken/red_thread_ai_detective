# Notes for the integration lead (Module 6)

## 1. Contract decisions I made that interfaces.md does not state

| # | Question | What `interrogate()` does now | Why |
| --- | --- | --- | --- |
| 1 | `DialogueRequest` raises `ContractError` if `presented_evidence_ids` is not a subset of `permitted_evidence_ids`, but the interface only says "discovered and revealed". | Presented evidence is also intersected with `npc.permitted_evidence_ids`; the rest is dropped. | Otherwise presenting evidence an NPC may not know would produce `SETUP_ERROR`. |
| 2 | What goes in `request.evidence`? | Presented evidence first, then retrieved evidence, de-duplicated, content re-read from the case by ID. | The NPC can react to what the player shows, and a faulty retriever cannot inject content. |
| 3 | Who advances `progression` / `discovered_evidence_ids`, and by what rule? | `interrogate()` never mutates the case. `advance_progression(case, to)` (monotonic) and `discover_evidence(case, id)` are provided for the game loop. | The rule table is not defined anywhere. Please confirm it (suggest: Richa / Pushparaj). |
| 4 | Behaviour when `presented_evidence_ids` is garbage. | Ignored (the model sees less, never more). | Fail-safe direction. |

## 2. Findings for the validator owner (Harsh) from the red-team run

Evidence: `results/integration_test_log.csv` (rows DINJ-05..DINJ-12 and ADV-B-*) and
`results/integration_summary.json`. Mock generator, real validator, fixture case.

The validator's text check is NFKC + casefold + whitespace collapse, then a word-boundary match on
authored terms. Measured against the term `brandy` / `poisoned` with NO other protected word in the text:

| Variant | Caught? |
| --- | --- |
| Plain text, fullwidth Unicode | Yes |
| Leet-speak (`br4ndy`, `p0is0ned`) | No |
| Cyrillic homoglyphs | No |
| Hyphen / dot / space separated letters | No |
| Zero-width characters inside words | No |
| Reversed text | No |
| Inflections not in the authored `terms` (`brandies`, `poisoning`) | No |
| Paraphrase or synonym with no authored term | No |

Result: 0 of 18 plain/structural attack units leaked; 32 of 32 obfuscation units leaked. A claim of "zero
spoilers across N attacks" is therefore only valid for the attack classes actually tested.

Suggested directions (validator owner's decision; I changed nothing outside `members/khushi/`):

1. Before matching, drop Unicode category `Cf` characters (zero-width) and fold common Cyrillic/Greek
   confusables and leet digits to Latin.
2. Also match terms against a "skeleton" form with separators between single letters removed. Check the
   false-positive cost on short terms.
3. Require authors to list inflections in `terms`, or stem both sides.
4. Reversed text and paraphrase cannot be fixed lexically. They need the semantic check (NLI or a judge
   model) or a tighter output constraint (for example, text composed only from cited facts).

## 3. Optional contract change request

If you want a pre-generation input firewall that blocks (as in the review's "injection classifier"), a new
reason code such as `INPUT_BLOCKED` is needed in `shared/contracts.py`. I deliberately do NOT block on the
heuristic: false positives would damage the game, and a distinct refusal path is an oracle. Today the
heuristic only sets `trace.injection_suspected` / `trace.evidence_injection_suspected`.

## 4. Handling of the three issues raised in the EPAM review

* Latency and cost depend mainly on the model backend, which is Module 4. The hooks here are `Deps`
  (swap in a local llama.cpp / Ollama generator), per-stage `TurnTrace`, deadline enforcement and
  `cost_usd` passthrough.
* The review estimates $3-5 per session while the team deck states roughly $0.54-0.72 per 1,000 turns on
  budget models. These conflict. Settle it by measuring tokens per turn x price on the chosen backend, not
  by choosing one of the two figures.
* The "50 attacks" acceptance criterion (Sprint 3) needs a real-model run (Devansh). With a mock model the
  output ignores the question text, so my 50 units are (behaviour x NPC x presented-evidence) combinations.
  A 0/50 result would only bound the true leak rate at about 7% (95% upper bound), so 100+ distinct attacks
  are advisable.

## 5. Scope

Per the agreed split with Pushparaj: Khushi owns `interrogate()`, timing/tracing, the stubs and the
integration tests. Pushparaj owns copying into `src/`, `scripts/run_game.py` and the reference acceptance
test. Nothing outside `members/khushi/` was edited.