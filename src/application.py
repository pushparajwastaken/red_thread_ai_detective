"""Application lifecycle and orchestration for Red Thread.

This layer owns the *session* (which case is loaded, what the player holds) and routes every
request to the existing member modules. It contains no game rules of its own:

* knowledge          -> members.anand.npc_knowledge.build_npc_context     (via Deps)
* evidence retrieval -> members.gagan.retriever.retrieve_evidence          (inside the pipeline)
* generation         -> members.anshul.dialogue_generator.generate_dialogue (inside the pipeline)
* validation         -> members.harsh.validator.validate_dialogue          (inside the pipeline)
* interrogation turn -> src.pipeline.interrogate_with_trace
* state changes      -> members.khushi.integration.advance_progression / discover_evidence

Every player question goes through ``src.pipeline.interrogate_with_trace``; this module never calls the
generator directly and never hands the full CaseState to anything but the pipeline.
"""
from __future__ import annotations

import csv
import json
import os
import statistics
import subprocess
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Optional

from members.khushi.integration import (
    Deps, TurnTrace, advance_progression, discover_evidence,
)
from members.richa.case_engine import CASE_001_ID, CASE_002_ID
from shared.contracts import (
    DEFAULT_TIMEOUT_S, CaseState, ContractError, DialogueResult, NPCContext, UnknownNPCError,
)
from src import bootstrap
from src.pipeline import interrogate_with_trace, load_case, real_deps

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE = CASE_001_ID
KNOWN_CASES = (CASE_001_ID, CASE_002_ID)
ENV_LOG_DIR = "RT_LOG_DIR"


class ApplicationError(Exception):
    """Base class for errors the terminal shows to the user."""


class ComponentUnavailable(ApplicationError):
    """A required or optional component is not ready for this operation."""


class InvalidSuspectError(ApplicationError):
    """The suspect id is not defined by the loaded case (ids are exact and case-sensitive)."""


class InvalidInputError(ApplicationError):
    """The request itself is invalid (empty question, bad case id, bad progression ...)."""


# ------------------------------------------------------------------ view types
@dataclass(frozen=True)
class SuspectInfo:
    npc_id: str
    persona: str
    authorized_facts: int
    granted_facts: int
    permitted_evidence: int
    granted_evidence: int


@dataclass(frozen=True)
class KnowledgeView:
    npc_id: str
    persona: str
    progression: int
    facts: list            # [(fact_id, kind, text)] authorized now
    evidence_ids: list     # permitted now
    withheld_facts: int    # granted but not yet revealed (text deliberately not exposed)
    withheld_evidence: int


@dataclass(frozen=True)
class EvidenceView:
    evidence_id: str
    content: str           # DATA; shown verbatim, never interpreted
    reveal_at: int
    visible_to: list       # suspects whose context permits it right now


@dataclass
class TurnOutcome:
    npc_id: str
    question: str
    result: DialogueResult
    trace: TurnTrace
    progression: int
    mode: str
    presented_dropped: int = 0


@dataclass
class SecurityRun:
    rows: list = field(default_factory=list)      # dicts: test_id, category, expected, actual, passed
    mode_note: str = ""

    @property
    def passed(self) -> int:
        return sum(1 for r in self.rows if r["passed"])

    @property
    def failed(self) -> int:
        return len(self.rows) - self.passed

    def by_category(self) -> dict:
        out: dict = {}
        for r in self.rows:
            c = out.setdefault(r["category"], [0, 0])
            c[0] += 1 if r["passed"] else 0
            c[1] += 1
        return out


# ------------------------------------------------------------------ application
class Application:
    def __init__(self, case_id: str = DEFAULT_CASE, *, deps: Optional[Deps] = None,
                 case_loader: Optional[Callable[[str], CaseState]] = None,
                 log_dir: Optional[Path] = None, timeout_s: float = DEFAULT_TIMEOUT_S) -> None:
        self.case_id = case_id
        self._deps = deps
        self._case_loader = case_loader or load_case
        self._timeout_s = timeout_s
        self._log_dir = Path(log_dir) if log_dir else Path(os.environ.get(ENV_LOG_DIR) or ROOT / "logs")
        self._log_fh = None
        self.log_path: Optional[Path] = None
        self.log_warning = ""
        self.report: Optional[bootstrap.BootReport] = None
        self.case: Optional[CaseState] = None
        self._closed = False

    # ---- lifecycle
    @property
    def deps(self) -> Deps:
        if self._deps is None:
            self._deps = real_deps()          # the real member modules; never stubs
        return self._deps

    @property
    def mode(self) -> str:
        return bootstrap.generation_mode()

    @property
    def ready(self) -> bool:
        return bool(self.report and self.report.ok and self.case is not None)

    def startup(self, case_id: Optional[str] = None) -> bootstrap.BootReport:
        """Initialise components, exercise each one, then load the case for play."""
        if case_id is not None:
            self.case_id = case_id
        try:
            deps = self.deps
        except Exception as exc:  # noqa: BLE001 - a member module failed to import
            self.case = None
            self.report = bootstrap.BootReport(self.case_id, self.mode, [bootstrap.ComponentStatus(
                "Member modules", "members/*", True, bootstrap.FAILED, f"{type(exc).__name__}: {exc}")])
            return self.report
        self.report = bootstrap.run_health_checks(self.case_id, deps, self._case_loader)
        self.case = None
        if self.report.is_ok("Case Engine"):
            try:
                self.case = self._case_loader(self.case_id)       # fresh copy; probes never touch it
            except Exception:  # noqa: BLE001
                self.case = None
        self._open_log()
        self._log("session_start", case_id=self.case_id, mode=self.mode, ready=self.ready,
                  components={c.name: c.state for c in self.report.components})
        return self.report

    def start_investigation(self, case_id: str) -> bootstrap.BootReport:
        """(Re)start on a case: fresh state, progression and inventory reset, components re-verified."""
        try:
            self._case_loader(case_id)
        except ContractError as exc:
            raise InvalidInputError(f"unknown case {case_id!r} (known: {', '.join(KNOWN_CASES)})") from exc
        return self.startup(case_id)

    def shutdown(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._log("session_end")
        if self._log_fh:
            try:
                self._log_fh.close()
            except OSError:
                pass
            self._log_fh = None

    def __enter__(self) -> "Application":
        return self

    def __exit__(self, *exc) -> None:
        self.shutdown()

    # ---- logging (never breaks the app)
    def _open_log(self) -> None:
        if self._log_fh:
            return
        try:
            self._log_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            self.log_path = self._log_dir / f"session-{stamp}-{uuid.uuid4().hex[:6]}.jsonl"
            self._log_fh = self.log_path.open("a", encoding="utf-8")
        except OSError as exc:
            self._log_fh, self.log_path = None, None
            self.log_warning = f"session logging disabled: {exc}"

    def _log(self, event: str, **data) -> None:
        if not self._log_fh:
            return
        try:
            rec = {"ts": datetime.now(timezone.utc).isoformat(), "event": event, **data}
            self._log_fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
            self._log_fh.flush()
        except (OSError, ValueError):
            self._log_fh = None
            self.log_warning = "session logging stopped after a write error"

    # ---- guards
    def _need_case(self) -> CaseState:
        if self.case is None:
            raise ComponentUnavailable("Case Engine is not ready; no case is loaded")
        return self.case

    def _need_ready(self) -> CaseState:
        case = self._need_case()
        if not self.ready:
            names = ", ".join(c.name for c in self.report.failed_required) if self.report else "unknown"
            raise ComponentUnavailable(f"required components are not ready: {names}")
        return case

    def _need_optional(self, name: str) -> None:
        if not (self.report and self.report.is_ok(name)):
            c = self.report.get(name) if self.report else None
            raise ComponentUnavailable(f"{name} is unavailable: {c.detail if c else 'not initialised'}")

    def _context(self, npc_id: object) -> NPCContext:
        case = self._need_case()
        try:
            return self.deps.build_npc_context(case, npc_id)     # exact, case-sensitive
        except UnknownNPCError as exc:
            raise InvalidSuspectError(
                f"unknown suspect {npc_id!r}; valid ids: {', '.join(case.npc_grants)}") from exc

    # ---- read-only views
    def case_overview(self) -> dict:
        """Reviewer view of the PUBLIC CaseState fields. clues/timeline are Case-Engine internal."""
        case = self._need_case()
        return {
            "case_id": case.case_id, "progression": case.progression,
            "facts": [(f, case.fact_meta[f].kind, case.fact_meta[f].reveal_at, t)
                      for f, t in case.canonical_facts.items()],
            "evidence": [(e, i.reveal_at, i.content) for e, i in case.evidence.items()],
            "suspects": {n: (g.persona, list(g.fact_ids), list(g.evidence_ids))
                         for n, g in case.npc_grants.items()},
            "inventory": list(case.discovered_evidence_ids),
        }

    def suspects(self) -> list[SuspectInfo]:
        case = self._need_case()
        out = []
        for npc_id, grant in case.npc_grants.items():
            npc = self._context(npc_id)
            out.append(SuspectInfo(npc_id, npc.persona, len(npc.authorized_fact_ids), len(grant.fact_ids),
                                   len(npc.permitted_evidence_ids), len(grant.evidence_ids)))
        return out

    def knowledge(self, npc_id: str) -> KnowledgeView:
        case = self._need_case()
        npc = self._context(npc_id)
        grant = case.npc_grants[npc_id]
        facts = [(f, case.fact_meta[f].kind, case.canonical_facts[f]) for f in npc.authorized_fact_ids]
        return KnowledgeView(npc_id, npc.persona, case.progression, facts, list(npc.permitted_evidence_ids),
                             len(grant.fact_ids) - len(npc.authorized_fact_ids),
                             len(grant.evidence_ids) - len(npc.permitted_evidence_ids))

    def evidence_inventory(self) -> list[EvidenceView]:
        case = self._need_case()
        contexts = {n: self._context(n) for n in case.npc_grants}
        out = []
        for eid in case.discovered_evidence_ids:
            item = case.evidence[eid]
            if item.reveal_at > case.progression:
                continue
            out.append(EvidenceView(eid, item.content, item.reveal_at,
                                    [n for n, c in contexts.items() if eid in c.permitted_evidence_ids]))
        return out

    def collectable_evidence(self) -> list[str]:
        case = self._need_case()
        return [e for e, i in case.evidence.items()
                if e not in case.discovered_evidence_ids and i.reveal_at <= case.progression]

    # ---- state changes (deterministic rules in members.khushi.integration only)
    def discover_evidence(self, evidence_id: str) -> None:
        case = self._need_case()
        if not discover_evidence(case, evidence_id):
            raise InvalidInputError(
                f"cannot collect {evidence_id!r}: unknown, already held, or not yet revealed")
        self._log("discover_evidence", evidence_id=evidence_id)

    def advance_progression(self, to: int) -> None:
        case = self._need_case()
        before = case.progression
        if not advance_progression(case, to):
            raise InvalidInputError(f"progression must be an integer above the current value ({before})")
        self._log("advance_progression", before=before, after=case.progression)

    # ---- the interrogation workflow
    def interrogate(self, npc_id: str, question: str,
                    presented_evidence_ids: Iterable[str] = ()) -> TurnOutcome:
        """One turn: context -> permitted evidence -> generation -> validation -> reply.

        Order and every authorization check live in src.pipeline / members.khushi.integration.
        This method only rejects unusable input and records the turn.
        """
        case = self._need_ready()
        if type(question) is not str or not question.strip():
            raise InvalidInputError("the question is empty")
        self._context(npc_id)                                    # rejects unknown suspects early
        presented = list(presented_evidence_ids)
        result, trace = interrogate_with_trace(
            case, npc_id, question, presented_evidence_ids=presented, timeout_s=self._timeout_s,
            deps=self.deps, request_id=uuid.uuid4().hex[:12])
        outcome = TurnOutcome(npc_id, question, result, trace, case.progression, self.mode,
                              trace.presented_dropped)
        self._log("turn", case_id=case.case_id, progression=case.progression, npc_id=npc_id,
                  question=question, presented=presented, valid=result.valid,
                  used_fallback=result.used_fallback, reasons=list(result.reasons), text=result.text,
                  cited_fact_ids=list(result.cited_fact_ids),
                  cited_evidence_ids=list(result.cited_evidence_ids), mode=self.mode,
                  trace=trace.to_dict())
        return outcome

    # ---- evaluation tools
    def run_security_validation(self) -> SecurityRun:
        """Run the shared 50-scenario adversarial table through the REAL pipeline.

        The scenarios script adversarial *drafts* into the offline mock generator, so they always run with
        the mock provider (they test the pipeline and validator, not a language model). They use their own
        fresh case_001 copies and do not touch the active investigation.
        """
        self._need_optional("Security Validation Suite")
        mod = bootstrap.load_security_module()
        run = SecurityRun(mode_note="scripted adversarial drafts via the offline mock generator; "
                                    "tests the pipeline + validator, NOT a language model")
        with bootstrap.forced_mock_provider():
            for s in mod.SCENARIOS:
                result, _ = mod.run_scenario(s)
                actual, exp = mod.outcome(result), mod.expected(s)
                run.rows.append({"test_id": s.test_id, "category": s.category, "expected": exp,
                                 "actual": actual, "passed": actual == exp})
        self._log("security_run", total=len(run.rows), passed=run.passed, failed=run.failed)
        return run

    def run_benchmark(self, warm_passes: int = 1) -> dict:
        """Run scripts/run_benchmark.py (dynamic pipeline vs branching baseline) and summarise it."""
        self._need_optional("Benchmark Harness")
        provider = bootstrap.provider_name()
        if provider not in ("mock", "ollama"):
            raise ComponentUnavailable(f"benchmark supports providers mock|ollama, not {provider!r}")
        if type(warm_passes) is not int or warm_passes < 0:
            raise InvalidInputError("warm passes must be a non-negative integer")
        self._log_dir.mkdir(parents=True, exist_ok=True)
        out = self._log_dir / f"benchmark-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.csv"
        cmd = [sys.executable, str(ROOT / "scripts" / "run_benchmark.py"), "--all",
               "--warm-passes", str(warm_passes), "--provider", provider, "--out", str(out)]
        if provider == "ollama":
            if os.environ.get("LLM_MODEL"):
                cmd += ["--model", os.environ["LLM_MODEL"]]
            cmd += ["--timeout-s", "20"]
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=1800)
        if proc.returncode != 0:
            raise ApplicationError(f"benchmark failed (exit {proc.returncode}): {proc.stderr.strip()[-400:]}")
        summary = self.summarise_benchmark(out)
        summary.update(csv_path=str(out), generation_mode=self.mode)
        self._log("benchmark_run", **{k: v for k, v in summary.items() if k != "modes"}, modes=summary["modes"])
        return summary

    @staticmethod
    def summarise_benchmark(path: Path) -> dict:
        with Path(path).open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        modes: dict = {}
        for mode in sorted({r["mode"] for r in rows}):
            mrows = [r for r in rows if r["mode"] == mode]
            cold = [r for r in mrows if r["run_id"].endswith("-cold")]
            ms = [float(r["total_ms"]) for r in mrows if r["total_ms"]]
            modes[mode] = {
                "model": mrows[0]["model"], "rows": len(mrows), "questions": len(cold),
                "valid": sum(r["valid"] == "True" for r in cold),
                "fallback": sum(r["used_fallback"] == "True" for r in cold),
                "answer_correct": sum(r["answer_correct"] == "True" for r in cold),
                "leaked_protected_fact": sum(r["leaked_protected_fact"] == "True" for r in cold),
                "median_total_ms": round(statistics.median(ms), 3) if ms else None,
            }
        return {"rows": len(rows), "modes": modes}
