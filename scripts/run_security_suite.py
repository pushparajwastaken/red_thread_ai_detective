"""Regenerate results/security_test_log.csv from ACTUAL runs of the real pipeline.

    python scripts/run_security_suite.py

Header == shared.contracts.TestRecord field order. ``passed`` compares reason CODES and
``used_fallback`` only (never prose). Offline: forces the deterministic mock provider.
"""
from __future__ import annotations

import csv
import dataclasses
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["LLM_PROVIDER"] = "mock"

from shared.contracts import TestRecord                      # noqa: E402
from tests.security_scenarios import SCENARIOS, expected, outcome, run_scenario  # noqa: E402

OUT = ROOT / "results" / "security_test_log.csv"


def main() -> int:
    run_id = "sprint1-sec-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rows = []
    for s in SCENARIOS:
        result, _ = run_scenario(s)
        actual = outcome(result)
        rows.append(TestRecord(
            test_id=s.test_id, category=s.category, expected=expected(s), actual=actual,
            passed=(actual == expected(s)), details=s.details, run_id=run_id, model="mock"))
    fields = [f.name for f in dataclasses.fields(TestRecord)]
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(fields)
        for r in rows:
            w.writerow([getattr(r, f) for f in fields])
    failed = [r.test_id for r in rows if not r.passed]
    print(f"wrote {OUT.relative_to(ROOT)}: {len(rows)} rows, {len(rows) - len(failed)} passed, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
