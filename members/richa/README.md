# Case Engine

Author: Richa Bharti

## Overview

`load_case(case_id: str) -> CaseState` loads the deterministic `case_001` case
fixture. The returned public case contract contains canonical facts, fact
metadata, evidence, and NPC grants for exactly three suspects.

## Case contents

- One victim and a coherent ground-truth timeline.
- Ten internal clues with references to valid facts, evidence, and suspects.
- Lowercase fact metadata terms with relevant word inflections.
- An authored in-world lie marked with `kind="cover_story"`.
- Fresh case data for each call; no mutable state is shared across loads.

The `clues` and `timeline` fields are for the Case Engine only. Other modules
must not read them.

## Running tests

```powershell
python -m pytest members/richa/test_case_engine.py
```

See [SUBMISSION.md](./SUBMISSION.md) for the integrity report and test result.
