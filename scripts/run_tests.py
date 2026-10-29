"""Run everything needed to reproduce Sprint 1 acceptance: pytest (root + members) and the question-set validator."""
import subprocess
import sys

steps = [[sys.executable, "-m", "pytest", "-q"], [sys.executable, "scripts/validate_benchmark_questions.py"]]
raise SystemExit(max(subprocess.call(s) for s in steps))
