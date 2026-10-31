"""Terminal interface and command-line handling. Presentation only: every action calls Application."""
from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

from src.application import (
    DEFAULT_CASE, KNOWN_CASES, Application, ApplicationError, ComponentUnavailable, InvalidInputError,
    InvalidSuspectError,
)

ROOT = Path(__file__).resolve().parents[1]

EXIT_OK, EXIT_NOT_READY, EXIT_BAD_INPUT, EXIT_TEST_FAILED = 0, 1, 2, 3

EPILOG = """\
examples:
  python run.py                         interactive terminal
  python run.py --check                 initialise and verify components, then exit
  python run.py --case case_002         start on the larger three-suspect case
  python run.py --ask gardener "What did you see?"   one interrogation turn, then exit
  python run.py --security              run the 50-scenario security validation
  python run.py --test                  run the supported pytest suites

generation is an OFFLINE DETERMINISTIC MOCK unless you pass --provider ollama
(needs a running Ollama server; only member-submitted, unreviewed real-model results exist).
"""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="run.py", description="Red Thread AI Detective - unified application",
                                epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--case", default=DEFAULT_CASE, help=f"case to load ({', '.join(KNOWN_CASES)}; default %(default)s)")
    p.add_argument("--check", action="store_true", help="initialise and verify every component, then exit (0 = required OK)")
    p.add_argument("--test", action="store_true", help="run the pytest suites (tests/ and members/, see docs/run-guide.md)")
    p.add_argument("--include-preksha", action="store_true",
                   help="with --test: also run members/preksha separately (known to fail in this snapshot)")
    p.add_argument("--ask", nargs=2, metavar=("SUSPECT", "QUESTION"), help="ask one question, print the reply, exit")
    p.add_argument("--present", default="", metavar="IDS", help="with --ask: comma-separated evidence ids to present")
    p.add_argument("--progression", type=int, default=None, metavar="N",
                   help="advance the case progression to N before --ask (manual stand-in for a game loop)")
    p.add_argument("--security", action="store_true", help="run the security validation suite, then exit")
    p.add_argument("--benchmark", action="store_true", help="run the dynamic-vs-branching benchmark, then exit")
    p.add_argument("--warm-passes", type=int, default=1, help="warm benchmark passes (default %(default)s)")
    p.add_argument("--provider", choices=("mock", "ollama"), help="generation provider (default: LLM_PROVIDER or mock)")
    p.add_argument("--model", help="model name for --provider ollama")
    p.add_argument("--log-dir", help="session log directory (default ./logs or $RT_LOG_DIR)")
    return p


# ------------------------------------------------------------------- --test
def run_tests(include_preksha: bool = False, out: Callable[[str], None] = print) -> int:
    if importlib.util.find_spec("pytest") is None:
        out("pytest is not installed: run  python -m pip install -r requirements.txt")
        return EXIT_TEST_FAILED
    cmd = [sys.executable, "-m", "pytest", "-q", "tests", "members", "--ignore=members/preksha"]
    out("Running: " + " ".join(cmd))
    out("(members/preksha is excluded: its suite has collection errors in this snapshot; see docs/integration-status.md)")
    rc = subprocess.call(cmd, cwd=ROOT)
    if include_preksha:
        cmd2 = [sys.executable, "-m", "pytest", "-q", "members/preksha"]
        out("Running: " + " ".join(cmd2))
        rc2 = subprocess.call(cmd2, cwd=ROOT)
        if rc2 != 0:
            out("members/preksha FAILED (documented, pre-existing; not caused by the integration).")
        rc = rc or rc2
    return EXIT_OK if rc == 0 else EXIT_TEST_FAILED


# ----------------------------------------------------------------- menu UI
class Terminal:
    def __init__(self, app: Application, input_fn: Callable[[str], str] = input,
                 out: Callable[[str], None] = print) -> None:
        self.app, self.ask, self.out = app, input_fn, out

    # -- helpers
    def banner(self) -> None:
        self.out(f"[generation mode] {self.app.mode}")

    def _pick_suspect(self) -> Optional[str]:
        infos = self.app.suspects()
        for i, s in enumerate(infos, 1):
            self.out(f"  {i}. {s.npc_id}  - {s.persona}")
        raw = self.ask("Suspect (number or id, blank to cancel): ").strip()
        if not raw:
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(infos):
            return infos[int(raw) - 1].npc_id
        return raw                                           # exact id; the application rejects bad ones

    def _guard(self, fn: Callable[[], None]) -> None:
        try:
            fn()
        except ApplicationError as exc:
            self.out(f"Error: {exc}")

    # -- menu actions
    def start_investigation(self) -> None:
        self.out(f"Known cases: {', '.join(KNOWN_CASES)}  (current: {self.app.case_id})")
        raw = self.ask(f"Case id [{self.app.case_id}]: ").strip() or self.app.case_id
        report = self.app.start_investigation(raw)
        self.out(report.render())
        if self.app.ready:
            self.out(f"\nInvestigation started: {self.app.case.case_id}, progression {self.app.case.progression}.")
            self.list_suspects()
        self.banner()

    def inspect_case(self) -> None:
        ov = self.app.case_overview()
        self.out("REVIEWER VIEW - this reveals canonical truth and spoils the mystery.")
        self.out(f"Case {ov['case_id']} (progression {ov['progression']})")
        self.out("Facts (id, kind, reveal_at, text):")
        for f, kind, reveal, text in ov["facts"]:
            self.out(f"  {f} [{kind}, reveal_at={reveal}] {text}")
        self.out("Evidence (id, reveal_at, content):")
        for e, reveal, content in ov["evidence"]:
            self.out(f"  {e} [reveal_at={reveal}] {content}")
        self.out("Suspects and their grants (before reveal gating):")
        for n, (persona, facts, ev) in ov["suspects"].items():
            self.out(f"  {n}: facts={facts} evidence={ev}  - {persona}")
        self.out("(clues and timeline are internal to the Case Engine and are not displayed.)")

    def list_suspects(self) -> None:
        self.out("Suspects:")
        for s in self.app.suspects():
            self.out(f"  {s.npc_id:<10} {s.persona}  | may speak of {s.authorized_facts}/{s.granted_facts} "
                     f"facts, {s.permitted_evidence}/{s.granted_evidence} evidence items now")

    def interrogate(self) -> None:
        npc_id = self._pick_suspect()
        if not npc_id:
            return
        self.app.knowledge(npc_id)                            # fail early on an invalid suspect
        inv = self.app.evidence_inventory()
        presented: list = []
        if inv:
            self.out("Your evidence: " + ", ".join(e.evidence_id for e in inv))
            raw = self.ask("Present evidence ids (comma separated, blank for none): ").strip()
            presented = [x.strip() for x in raw.split(",") if x.strip()]
        self.banner()
        while True:
            q = self.ask(f"Ask {npc_id} (blank to stop): ").strip()
            if not q:
                return
            o = self.app.interrogate(npc_id, q, presented)
            r = o.result
            self.out(f"{npc_id}: {r.text}")
            if r.valid:
                self.out(f"  [validated] cited facts={r.cited_fact_ids} evidence={r.cited_evidence_ids}")
            else:
                self.out(f"  [safe fallback] reason codes (log only): {', '.join(r.reasons)}")
            if o.presented_dropped:
                self.out(f"  note: {o.presented_dropped} presented evidence id(s) were not accepted "
                         "(not held, not revealed, or this suspect may not see it)")
            self.out(f"  {r.latency_ms:.1f} ms, progression {o.progression}")

    def evidence(self) -> None:
        inv = self.app.evidence_inventory()
        self.out("Evidence you hold and may use (id: who can be shown it):")
        for e in inv:
            self.out(f"  {e.evidence_id} [reveal_at={e.reveal_at}] {e.content}")
            self.out(f"      shown to: {', '.join(e.visible_to) or 'no suspect'}")
        if not inv:
            self.out("  (none)")

    def check_knowledge(self) -> None:
        npc_id = self._pick_suspect()
        if not npc_id:
            return
        k = self.app.knowledge(npc_id)
        self.out(f"{k.npc_id} - {k.persona}  (progression {k.progression})")
        self.out("May speak of:")
        for f, kind, text in k.facts:
            self.out(f"  {f} [{kind}] {text}")
        if not k.facts:
            self.out("  (nothing yet)")
        self.out(f"May be shown evidence: {', '.join(k.evidence_ids) or '(none)'}")
        self.out(f"Withheld until later progression: {k.withheld_facts} fact(s), {k.withheld_evidence} evidence item(s)")

    def controls(self) -> None:
        self.out("Investigator controls: manual stand-ins for the game loop (not implemented in this repository).")
        self.out(f"Progression: {self.app.case.progression}.  Collectable evidence: "
                 f"{', '.join(self.app.collectable_evidence()) or '(none)'}")
        raw = self.ask("Enter 'p N' to advance progression, an evidence id to collect it, blank to return: ").strip()
        if not raw:
            return
        if raw.lower().startswith("p "):
            try:
                self.app.advance_progression(int(raw[2:]))
            except ValueError as exc:
                raise InvalidInputError("progression must be an integer") from exc
            self.out(f"Progression is now {self.app.case.progression}.")
        else:
            self.app.discover_evidence(raw)
            self.out(f"Collected {raw}.")

    def security(self) -> None:
        self.out("Running the security validation suite (a few seconds)...")
        run = self.app.run_security_validation()
        self.out(f"Note: {run.mode_note}")
        for cat, (ok, total) in sorted(run.by_category().items()):
            self.out(f"  {cat:<20} {ok}/{total}")
        for r in run.rows:
            if not r["passed"]:
                self.out(f"  FAILED {r['test_id']}: expected {r['expected']} got {r['actual']}")
        self.out(f"Result: {run.passed}/{len(run.rows)} scenarios passed.")

    def benchmark(self) -> None:
        self.banner()
        self.out("Running the benchmark: dynamic pipeline vs branching baseline on case_001 (30 questions)...")
        s = self.app.run_benchmark()
        for mode, m in s["modes"].items():
            self.out(f"  {mode:<10} model={m['model']:<11} valid {m['valid']}/{m['questions']}  fallback {m['fallback']}  "
                     f"answer_correct {m['answer_correct']}  leaked {m['leaked_protected_fact']}  "
                     f"median {m['median_total_ms']} ms")
        if self.app.mode.startswith("OFFLINE"):
            self.out("These numbers measure pipeline overhead with the mock; they are not LLM quality or latency.")
        self.out(f"Raw rows: {s['csv_path']}")

    # -- loop
    def menu_items(self) -> list:
        r = self.app.report
        have_case = self.app.case is not None
        ready = self.app.ready
        items = []
        items.append(("Start Investigation (choose / restart case)", self.start_investigation))
        if have_case:
            items.append(("Inspect Canonical Case (reviewer view, spoilers)", self.inspect_case))
            items.append(("List Suspects", self.list_suspects))
        if ready:
            items.append(("Interrogate a Suspect", self.interrogate))
        if have_case:
            items.append(("Inspect Available Evidence", self.evidence))
            items.append(("Check Suspect Knowledge", self.check_knowledge))
            items.append(("Investigator controls (advance progression / collect evidence)", self.controls))
        if r and r.is_ok("Security Validation Suite"):
            items.append(("Run Security Validation", self.security))
        if r and r.is_ok("Benchmark Harness"):
            items.append(("Run Benchmark", self.benchmark))
        return items

    def run(self) -> int:
        while True:
            items = self.menu_items()
            self.out("\n=== Red Thread AI Detective ===")
            self.banner()
            for i, (label, _) in enumerate(items, 1):
                self.out(f"  {i}. {label}")
            self.out(f"  {len(items) + 1}. Exit")
            try:
                raw = self.ask("> ").strip()
            except (EOFError, KeyboardInterrupt):
                self.out("")
                return EXIT_OK
            if raw.isdigit() and int(raw) == len(items) + 1 or raw.lower() in ("q", "exit"):
                return EXIT_OK
            if raw.isdigit() and 1 <= int(raw) <= len(items):
                try:
                    self._guard(items[int(raw) - 1][1])
                except (EOFError, KeyboardInterrupt):
                    self.out("")
                    return EXIT_OK
            else:
                self.out("Please enter a number from the menu.")


# --------------------------------------------------------------------- main
def main(argv: Optional[list] = None, input_fn: Callable[[str], str] = input,
         out: Callable[[str], None] = print) -> int:
    args = build_parser().parse_args(argv)
    if args.provider:
        os.environ["LLM_PROVIDER"] = args.provider
    if args.model:
        os.environ["LLM_MODEL"] = args.model
    if args.test:
        return run_tests(args.include_preksha, out)

    app = Application(args.case, log_dir=Path(args.log_dir) if args.log_dir else None)
    try:
        report = app.startup()
        out(report.render())
        if app.log_path:
            out(f"Session log: {app.log_path}")
        if app.log_warning:
            out(f"Warning: {app.log_warning}")
        if args.check:
            return EXIT_OK if report.ok else EXIT_NOT_READY
        try:
            if args.ask:
                return _ask_once(app, args, out)
            if args.security:
                return _security_once(app, out)
            if args.benchmark:
                return _benchmark_once(app, args, out)
        except InvalidInputError as exc:
            out(f"Error: {exc}")
            return EXIT_BAD_INPUT
        except InvalidSuspectError as exc:
            out(f"Error: {exc}")
            return EXIT_BAD_INPUT
        except ComponentUnavailable as exc:
            out(f"Error: {exc}")
            return EXIT_NOT_READY
        if app.case is None:
            out("Cannot start: the Case Engine is not available.")
            return EXIT_NOT_READY
        if not app.ready:
            out("Starting in limited mode: interrogation is disabled until the required components above are fixed.")
        return Terminal(app, input_fn, out).run()
    finally:
        app.shutdown()


def _ask_once(app: Application, args, out) -> int:
    if args.progression is not None:
        app.advance_progression(args.progression)
    presented = [x.strip() for x in args.present.split(",") if x.strip()]
    npc_id, question = args.ask
    o = app.interrogate(npc_id, question, presented)
    out(f"[generation mode] {app.mode}")
    out(f"{npc_id}: {o.result.text}")
    out(f"valid={o.result.valid} fallback={o.result.used_fallback} reasons={','.join(o.result.reasons)}")
    return EXIT_OK


def _security_once(app: Application, out) -> int:
    run = app.run_security_validation()
    out(f"Security validation: {run.passed}/{len(run.rows)} scenarios passed ({run.mode_note})")
    return EXIT_OK if run.failed == 0 else EXIT_TEST_FAILED


def _benchmark_once(app: Application, args, out) -> int:
    s = app.run_benchmark(args.warm_passes)
    out(f"[generation mode] {app.mode}")
    for mode, m in s["modes"].items():
        out(f"{mode}: {m}")
    out(f"Raw rows: {s['csv_path']}")
    return EXIT_OK
