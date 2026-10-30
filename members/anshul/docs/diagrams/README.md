# Red Thread: Architecture Diagrams

Diagrams for the interrogation pipeline of Red Thread. Author: Anshul.

**Status:** Draft for review. The shared contracts in `shared/interfaces.md`
and `shared/contracts.py` are authoritative. If a diagram disagrees with them,
the contracts win and the diagram needs fixing.

## Contents

| File | What it shows | Status |
|---|---|---|
| `c4-context.svg` | C4 level 1: players, the system and the optional LLM provider | Current |
| `c4-containers.svg` | C4 level 2: Python prototype and its modules | Current, with proposed parts dashed |
| `c4-components.svg` | C4 level 3: components inside the pipeline | Current |
| `sequence-interrogation.svg` | One interrogation turn, question to validated reply or fallback | Current |
| `sequence-evidence-update.svg` | How evidence and progression updates should be checked | **Proposed** |
| `erd-persistence.svg` | Possible relational schema for cases, NPC grants and session events | **Proposed** |

## How to read them

- Solid lines and boxes describe what the repository does now.
- Dashed lines and anything marked "Proposed" are design ideas. They are not
  implemented, and no API, database or client exists yet.
- The generator only receives authorized facts and evidence. Its output is an
  untrusted draft until the validator accepts it or a safe fallback replaces it.

## Previews

### System context
![System context](c4-context.svg)

### Containers
![Containers](c4-containers.svg)

### Components
![Components](c4-components.svg)

### One interrogation turn
![Interrogation sequence](sequence-interrogation.svg)

### Evidence update (proposed)
![Evidence update sequence](sequence-evidence-update.svg)

### Persistence ERD (proposed)
![Persistence ERD](erd-persistence.svg)

## Viewing

Click any `.svg` file on GitHub to open it, or open it in a browser.
SVGs scale without losing quality, so zoom in for detail.

## Editing

These files were exported from Mermaid diagrams (mermaid.live). To change one:

1. Re-create or edit the diagram in https://mermaid.live.
2. Export it as SVG using the same file name.
3. Replace the file and commit it.
4. Re-check the diagram against `shared/interfaces.md` and `src/pipeline.py`.

The Mermaid source is not stored in this folder. If you want edits without
redrawing, add the `.mmd` source files next to the SVGs.

## Review

Please review these against the current code. Changes to shared interfaces
go through the integration lead first.
