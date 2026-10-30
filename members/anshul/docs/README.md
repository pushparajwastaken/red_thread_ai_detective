# Anshul's Documentation: Red Thread Dialogue Generation

Documentation for the **Dialogue generation** workstream of the Red Thread
sprint (owner: Anshul), plus supporting architecture and planning drafts.

**Status:** Draft for team review. Nothing here changes `shared/`, `src/` or
another member's folder.

> **Authority:** `shared/interfaces.md` and `shared/contracts.py` are the
> authoritative contracts. These documents explain them and never override
> them. If something here disagrees with the contracts, the contracts win
> and the document needs fixing.

---

## 1. Purpose

Red Thread is an AI-driven detective game where players question characters
in free text. The sprint goal is to build a testable prototype that:

- presents evidence without leaking future plot,
- recovers from hallucinations through validation and fallback, and
- compares dynamic interrogation against branching dialogue.

My workstream is **dialogue generation**: a deterministic mock dialogue
generator first, followed by LLM integration. These docs describe how that
work fits into the pipeline and the decisions around it.

## 2. Scope: current vs proposed

Every document is labelled one of three ways:

| Label | Meaning |
|---|---|
| **Current** | Describes behaviour the repository has now |
| **Proposed** | A design idea. Not implemented; no approval implied |
| **Template / Not run** | A form to fill in or an experiment not yet performed |

The repository currently has a Python interrogation pipeline, shared contracts,
an offline mock, tests and benchmark artifacts. It does **not** have a game
client, web API, database, agent runtime or measured real-model results.
Please don't read the proposed documents as claims otherwise.

## 3. Folder map

```
members/anshul/docs/
├── README.md                   ← this file
├── architecture.md             Architecture overview
├── diagrams/                   Architecture diagrams (SVG), has its own README
├── adr/                        Architecture decision records
├── product/                    Lean PRD and story map
├── agile/                      Sprint backlog, definition of done, RAID, retro
├── spikes/                     Research spikes
├── poc/                        Proof-of-concept readouts
└── operations/                 Incident review template
```

## 4. Document index

### Architecture and design

| File | Summary | Status |
|---|---|---|
| `architecture.md` | Trust boundary, current pipeline, proposed extensions | Current + Proposed |
| `diagrams/` | C4 context/container/component, interrogation sequence, proposed evidence-update sequence, proposed ERD | Current + Proposed |
| `adr/0001-canonical-truth-and-bounded-dialogue.md` | Keep canonical truth outside generation; supply only authorized facts | Accepted for prototype |
| `adr/0002-offline-first-provider-adapter.md` | Keep a deterministic offline path next to any live model | Accepted for prototype |
| `adr/0003-persistence-and-orchestration.md` | Defer database and agent-framework choice until a spike | Proposed |

### Planning

| File | Summary | Status |
|---|---|---|
| `product/lean-prd.md` | Problem, outcome, MVP1 scope, success measures | Proposed |
| `product/story-map.md` | User journey and epics | Proposed |
| `agile/sprint-backlog.md` | Candidate next-sprint items | Proposed |
| `agile/definition-of-done.md` | Checklist for closing a story | Proposed |

### Research and learning

| File | Summary | Status |
|---|---|---|
| `spikes/001-real-model-and-player-visible-latency.md` | Questions and method for measuring a real model | **Not run** |
| `poc/offline-interrogation/README.md` | Reproducing the offline interrogation PoC | Current |

### Risk and process

| File | Summary | Status |
|---|---|---|
| `agile/raid-log.md` | Risks, assumptions, issues, dependencies | Living draft |
| `agile/retrospective-template.md` | Template for sprint retrospectives | Template |
| `operations/incident-postmortem-template.md` | Blameless incident review form | Template (no real incident) |

## 5. How my component fits the pipeline

```
player question + presented evidence IDs
        │
        ▼
 NPC knowledge      → authorized facts for this NPC          (Anand)
 Evidence retrieval → permitted evidence only                (Gagan)
        │
        ▼
 Dialogue generator → untrusted draft (mock or LLM)          (Anshul)
        │
        ▼
 Validator          → accepted reply or safe fallback        (Harsh)
        │
        ▼
 Integration        → text shown to the player               (Pushparaj, Khushi)
```

Rules my component follows:

- It receives only authorized facts and evidence, never the full case state.
- Player input and evidence text are treated as untrusted data.
- Its output is an untrusted draft. Nothing is shown to the player until it
  has been validated, and on failure the approved fallback is shown instead.
- The mock and LLM versions use the same interface so they can be swapped.

## 6. Evidence rules for claims

Following the team reporting rule, security and performance claims need
recorded tests.

- The offline mock verifies integration behaviour. It does **not** measure
  live-model latency, quality or cost.
- Real-model results are **not run** until Spike 001 is completed or
  recorded as blocked, with the prerequisite named.
- Every result should state its type: mock, real model, human playtest or
  not run.

## 7. Reproducing the offline checks

From the repository root, with Python 3.11 or newer:

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python -m pytest
```

See `poc/offline-interrogation/README.md` for the focused commands. Test
counts in older documents are historical. Rerun the tests on your commit
before relying on them.

## 8. Contributing to these docs

1. Work on a feature branch, for example `feature/anshul-docs`.
2. Edit only files inside `members/anshul/`.
3. Mark anything not implemented as **Proposed**.
4. Update the relevant ADR when a decision changes.
5. Check diagrams and claims against `shared/interfaces.md` and
   `src/pipeline.py` before opening a pull request.
6. Never commit API keys or `.env` files.

Changes to shared interfaces go through the integration lead first.

## 9. Known limits

- Lexical validation can miss meaning-level leaks. The risk is recorded in
  `agile/raid-log.md`.
- No live-model measurements exist yet.
- No human playtest has been run.
- Proposed persistence, UI and agent designs are untested.

## 10. Contact and review

Owner: Anshul. Reviewer: integration lead (Pushparaj, Khushi). Open an issue
or comment on the pull request with corrections.
