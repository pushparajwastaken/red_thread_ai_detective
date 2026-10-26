# import sys
# from pathlib import Path
# import pytest
# ROOT = Path(__file__).resolve().parent.parent.parent
# sys.path.insert(0, str(ROOT))
# for f in (ROOT / "members").iterdir():
#     if f.is_dir() and f.name != "__pycache__":
#         sys.path.insert(0, str(f))
# from shared.contracts import NPCContext
# from dialogue_generator import clear_mock_scripts

# def make_npc_context(case, npc_id):
#     g = case.npc_grants[npc_id]
#     return NPCContext(
#         npc_id=npc_id,
#         authorized_fact_ids=list(g.fact_ids),
#         permitted_evidence_ids=list(g.evidence_ids),
#         persona=g.persona,
#     )

# @pytest.fixture
# def mock_cleanup():
#     clear_mock_scripts()
#     yield
#     clear_mock_scripts()


"""
conftest.py — Preksha QA test suite.

Part 1: Environment setup (sys.path, shim, fixtures)
Part 2: Reporting hooks (per-file CSVs after each run)
"""
# ═══════════════════════════════════════════════════════════════════
# PART 1 — ENVIRONMENT SETUP (do not touch — 15+ tests depend on it)
# ═══════════════════════════════════════════════════════════════════
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

for f in (ROOT / "members").iterdir():
    if f.is_dir() and f.name != "__pycache__":
        sys.path.insert(0, str(f))

from shared.contracts import NPCContext
from dialogue_generator import clear_mock_scripts


def make_npc_context(case, npc_id):
    """Shim until Anand's build_npc_context is contract-compliant."""
    g = case.npc_grants[npc_id]
    return NPCContext(
        npc_id=npc_id,
        authorized_fact_ids=list(g.fact_ids),
        permitted_evidence_ids=list(g.evidence_ids),
        persona=g.persona,
    )


@pytest.fixture
def mock_cleanup():
    """Clear mock scripts before AND after each test."""
    clear_mock_scripts()
    yield
    clear_mock_scripts()


# ═══════════════════════════════════════════════════════════════════
# PART 2 — REPORTING HOOKS (writes CSVs to results/ after each run)
# ═══════════════════════════════════════════════════════════════════
import csv
from datetime import datetime

RESULTS_DIR     = Path(__file__).parent / "results"
BY_FILE_DIR     = RESULTS_DIR / "by_file"
BY_CATEGORY_DIR = RESULTS_DIR / "by_category"
LOGS_DIR        = RESULTS_DIR / "logs"

CATEGORY_MAP = {
    "test_contracts.py":               "contracts",
    "test_fixture.py":                 "fixture",
    "test_authorization.py":           "authorization",
    "test_progression.py":             "progression",
    "test_request_security.py":        "request_security",
    "test_spoiler.py":                 "spoiler",
    "test_unsupported_claim.py":       "unsupported_claim",
    "test_malformed_output.py":        "malformed_output",
    "test_timeout.py":                 "timeout",
    "test_make_fallback.py":           "fallback",
    "test_validator_failclosed.py":    "validator_failure",
    "test_npc_shim.py":                "npc_shim",
    "test_validator_ids.py":           "validator_ids",
    "test_validator_terms.py":         "validator_terms",
    "test_validator_metrics.py":       "validator_metrics",
    "test_case_engine_load.py":        "case_engine",
    "test_e2e.py":                     "e2e",
    "test_bug_anand_contract.py":      "bug_evidence",
    "test_bug_richa_fixture_drift.py": "bug_evidence",
}

_results: list[dict] = []
_session_start: datetime | None = None
_run_id: str = ""


def pytest_sessionstart(session):
    global _session_start, _run_id
    _session_start = datetime.now()
    _run_id = _session_start.strftime("%Y%m%d_%H%M%S")
    for d in (RESULTS_DIR, BY_FILE_DIR, BY_CATEGORY_DIR, LOGS_DIR):
        d.mkdir(parents=True, exist_ok=True)
    _results.clear()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    capture = (
        report.when == "call"
        or (report.when == "setup" and (report.failed or report.skipped))
    )
    if not capture:
        return

    try:
        test_file = item.path.name
    except AttributeError:
        test_file = Path(str(item.fspath)).name

    if report.passed:
        status = "PASSED"
    elif report.failed:
        status = "FAILED"
    elif report.skipped:
        status = "SKIPPED"
    else:
        status = "UNKNOWN"

    message = ""
    if report.failed and report.longrepr:
        for line in str(report.longrepr).splitlines():
            if line.strip().startswith("E "):
                message = line.strip()[2:].strip()[:250]
                break
        if not message:
            message = str(report.longrepr).splitlines()[-1].strip()[:250]

    test_idx = sum(1 for r in _results if r["file"] == test_file) + 1
    _results.append({
        "test_id":     f"TC_{test_file.replace('test_', '').replace('.py', '').upper()}_{test_idx:03d}",
        "file":        test_file,
        "function":    item.name,
        "class":       item.cls.__name__ if item.cls else "",
        "status":      status,
        "duration_ms": round(report.duration * 1000, 2),
        "message":     message,
        "category":    CATEGORY_MAP.get(test_file, "unknown"),
    })


def _write_csv(path: Path, rows: list[dict]):
    fieldnames = ["test_id", "file", "function", "class",
                  "status", "duration_ms", "message", "category"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def pytest_sessionfinish(session, exitstatus):
    if not _results:
        return

    _write_csv(RESULTS_DIR / "summary.csv", _results)

    for fname in sorted({r["file"] for r in _results}):
        rows = [r for r in _results if r["file"] == fname]
        _write_csv(BY_FILE_DIR / fname.replace(".py", ".csv"), rows)

    for cat in sorted({r["category"] for r in _results}):
        rows = [r for r in _results if r["category"] == cat]
        _write_csv(BY_CATEGORY_DIR / f"{cat}.csv", rows)

    total    = len(_results)
    passed   = sum(1 for r in _results if r["status"] == "PASSED")
    failed   = sum(1 for r in _results if r["status"] == "FAILED")
    skipped  = sum(1 for r in _results if r["status"] == "SKIPPED")
    duration = (datetime.now() - _session_start).total_seconds()

    md = [
        "# Test Run Summary",
        "",
        f"**Run ID:** `{_run_id}`  ",
        f"**Started:** {_session_start.isoformat()}  ",
        f"**Duration:** {duration:.2f}s",
        "",
        "## Overall",
        "",
        "| Metric | Count |",
        "|---|---|",
        f"| Total | {total} |",
        f"| ✅ Passed | {passed} |",
        f"| ❌ Failed | {failed} |",
        f"| ⏭ Skipped | {skipped} |",
        "",
        "## By File",
        "",
        "| File | Total | Passed | Failed |",
        "|---|---|---|---|",
    ]
    for fname in sorted({r["file"] for r in _results}):
        rows = [r for r in _results if r["file"] == fname]
        p = sum(1 for r in rows if r["status"] == "PASSED")
        fl = sum(1 for r in rows if r["status"] == "FAILED")
        md.append(f"| `{fname}` | {len(rows)} | {p} | {fl} |")

    md += ["", "## Failures", ""]
    failures = [r for r in _results if r["status"] == "FAILED"]
    if not failures:
        md.append("_No failures._")
    else:
        for r in failures:
            md.append(f"- **`{r['file']}::{r['function']}`** — {r['message']}")

    (RESULTS_DIR / "summary.md").write_text("\n".join(md), encoding="utf-8")

    (RESULTS_DIR / "latest_run.txt").write_text(
        f"run_id={_run_id}\n"
        f"total={total}\npassed={passed}\nfailed={failed}\nskipped={skipped}\n"
        f"duration_s={duration:.2f}\n",
        encoding="utf-8",
    )

    print("\n" + "─" * 60)
    print("📊 Results written:")
    print(f"   summary.csv       → {RESULTS_DIR/'summary.csv'}")
    print(f"   summary.md        → {RESULTS_DIR/'summary.md'}")
    print(f"   per-file CSVs     → {BY_FILE_DIR}/")
    print(f"   per-category CSVs → {BY_CATEGORY_DIR}/")
    print("─" * 60)

