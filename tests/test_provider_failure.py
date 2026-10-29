"""Provider-failure handling through the REAL Ollama backend code path (no server needed).

These do NOT validate real-model quality; they prove that a missing/dead/misconfigured provider degrades to the
standard fallback without raising, and quickly.
"""
import sys
import time

import pytest

from shared.contracts import SAFE_FALLBACK_TEXT, Reason
from src.pipeline import interrogate_with_trace, load_case


def ask(timeout=5.0):
    t = time.perf_counter()
    res, trace = interrogate_with_trace(load_case("case_001"), "gardener", "What did you see?", timeout_s=timeout)
    return res, time.perf_counter() - t


def test_ollama_backend_with_dead_endpoint_falls_back(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_URL", "http://127.0.0.1:9")          # discard port: connection refused
    res, elapsed = ask()
    assert res.used_fallback and res.text == SAFE_FALLBACK_TEXT and res.reasons == [Reason.GEN_ERROR]
    assert res.metrics.ttft_ms is None and res.metrics.cost_usd is None and elapsed < 4


def test_unknown_provider_name_falls_back(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "definitely-not-a-provider")
    res, _ = ask()
    assert res.used_fallback and res.reasons == [Reason.GEN_ERROR]


def test_missing_requests_package_falls_back(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setitem(sys.modules, "requests", None)              # makes `import requests` raise ImportError
    res, _ = ask()
    assert res.used_fallback and res.text == SAFE_FALLBACK_TEXT and res.reasons == [Reason.GEN_ERROR]


def test_default_provider_is_the_offline_mock(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    res, _ = ask()
    assert res.valid and res.metrics.model == "mock"
