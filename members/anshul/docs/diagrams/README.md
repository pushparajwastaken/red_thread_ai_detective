# Red Thread: Architecture Diagrams

Diagrams for the interrogation pipeline of Red Thread. Author: Anshul.

**Status:** Draft for review. The shared contracts in `shared/interfaces.md`
and `shared/contracts.py` are authoritative. If a diagram disagrees with them,
the contracts win and the diagram needs fixing.

## Contents

| File | What it shows | Status |
|---|---|---|
| `c4-context.mmd` | C4 level 1: players, the system and the optional LLM provider | Current |
| `c4-containers.mmd` | C4 level 2: Python prototype and its modules | Current, with proposed parts dashed |
| `c4-components.mmd` | C4 level 3: components inside the pipeline | Current |
| `sequence-interrogation.mmd` | One interrogation turn, question to validated reply or fallback | Current |
| `sequence-evidence-update.mmd` | How evidence and progression updates should be checked | **Proposed** |
| `erd-persistence.mmd` | Possible relational schema for cases, NPC grants and session events | **Proposed** |

## How to read them

- Solid lines and boxes describe what the repository does now.
- Dashed lines and anything marked "Proposed" are design ideas. They are not
  implemented, and no API, database or client exists yet.
- The generator only receives authorized facts and evidence. Its output is an
  untrusted draft until the validator accepts it or a safe fallback replaces it.

## Viewing

The `.mmd` files are Mermaid source. GitHub renders Mermaid inside markdown
files, so you can paste a diagram into a markdown file in a mermaid code block
to preview it. To see one outside GitHub, paste it into https://mermaid.live
or export it with `mmdc` from `@mermaid-js/mermaid-cli`.

## Editing

1. Edit the `.mmd` source file, not an exported image.
2. Check the result in mermaid.live.
3. If you keep exported PNG or SVG copies, re-export them and commit them
   together with the source.
4. Re-check the diagram against `shared/interfaces.md` and `src/pipeline.py`.

## Review

Please review these against the current code. Changes to shared interfaces
go through the integration lead first.
