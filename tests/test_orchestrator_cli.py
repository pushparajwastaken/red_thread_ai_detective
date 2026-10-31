"""Command-line and terminal-menu tests for run.py / src.terminal."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from src.terminal import EXIT_BAD_INPUT, EXIT_NOT_READY, EXIT_OK, main

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("RT_LOG_DIR", str(tmp_path))


def run(argv, inputs=()):
    lines, feed = [], iter(inputs)
    def ask(prompt=""):
        try:
            return next(feed)
        except StopIteration:
            raise EOFError
    rc = main(argv, input_fn=ask, out=lines.append)
    return rc, "\n".join(lines)


def test_check_returns_zero_and_prints_report():
    rc, text = run(["--check"])
    assert rc == EXIT_OK
    assert "[OK] Case Engine" in text and "OFFLINE DETERMINISTIC MOCK" in text
    assert "[NOT IMPLEMENTED]" in text and "[UNAVAILABLE] Real LLM Generation" in text


def test_check_with_unknown_case_fails():
    rc, text = run(["--check", "--case", "case_999"])
    assert rc == EXIT_NOT_READY and "[FAILED] Case Engine" in text


def test_help_exits_cleanly(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--help"])
    assert e.value.code == 0
    assert "--check" in capsys.readouterr().out


def test_ask_returns_validated_reply():
    rc, text = run(["--ask", "gardener", "What did you see near the greenhouse?", "--present", "E001"])
    assert rc == EXIT_OK and "valid=True" in text and "OFFLINE" in text


def test_ask_invalid_suspect_is_rejected():
    rc, text = run(["--ask", "nobody", "hello?"])
    assert rc == EXIT_BAD_INPUT and "unknown suspect" in text


def test_ask_with_progression_uses_real_gating():
    rc, text = run(["--case", "case_002", "--ask", "rohan", "What did you receive?", "--progression", "1"])
    assert rc == EXIT_OK and "valid=True" in text


def test_menu_session_lists_only_working_options_and_exits():
    rc, text = run([], inputs=["3", "10"])       # List Suspects, then Exit (9 options + Exit)
    assert rc == EXIT_OK
    assert "Interrogate a Suspect" in text and "Run Security Validation" in text and "Run Benchmark" in text
    assert "gardener" in text and "cook" in text


def test_menu_interrogation_flow():
    rc, text = run([], inputs=["4", "1", "E001", "What did you see near the greenhouse?", "", "10"])
    assert rc == EXIT_OK and "[validated]" in text and "gardener:" in text


def test_menu_rejects_invalid_suspect_with_helpful_error():
    rc, text = run([], inputs=["4", "butler", "10"])
    assert rc == EXIT_OK and "Error: unknown suspect 'butler'" in text


def test_menu_survives_eof():
    rc, _ = run([], inputs=[])
    assert rc == EXIT_OK


def test_run_py_is_the_single_entry_point(tmp_path):
    proc = subprocess.run([sys.executable, "run.py", "--check", "--log-dir", str(tmp_path)],
                          cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "Required components: all OK." in proc.stdout
