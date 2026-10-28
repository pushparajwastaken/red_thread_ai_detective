# SUBMISSION — Module 7: Adversarial Security Tests

**Author:** Devansh Vinayak  
**Module:** 7 (Testing — Adversarial Security Runs)  
**Sprint:** 1 — Case Engine & Epistemic Schema  
**Base Commit SHA:** `e4cd493adb7cba472848421a53c69a6eff98909f`  
**Test Date:** 26 October 2026  

---

## 1. Files Submitted

| File | Purpose |
|---|---|
| `members/devansh/test_adversarial_security.py` | 34 pytest tests covering direct injection, indirect injection, spoilers, unauthorized claims, fallback invariants, and lexical boundaries |
| `members/devansh/run_security_suite.py` | Standalone runner executing attack matrix and generating `TestRecord` logs |
| `members/devansh/adversarial_cases.json` | Structured JSON attack cases for direct/indirect prompt injection and spoiler probes |
| `members/devansh/security_test_log.csv` | Recorded outcomes matching `TestRecord` schema |
| `members/devansh/test-output.txt` | Captured actual pytest verbose test execution output |
| `members/devansh/README.md` | Comprehensive documentation on test scope, methodology, results, and recommendations |
| `members/devansh/SUBMISSION.md` | This formal submission handoff record |
| `test_cases/prompt_injection_cases.json` | Shared attack test case definitions |
| `results/security_test_log.csv` | Central security test log in `TestRecord` field order |

---

## 2. Dependencies and Environment

| Package | Version | In requirements.txt? |
|---|---|---|
| Python | 3.12+ (tested on 3.12.0) | Runtime (Python 3.11+ required) |
| pytest | 8.3.3 | Yes |
| Standard Library | `dataclasses`, `csv`, `json`, `pathlib`, `uuid`, `datetime` | Yes (Standard Library) |

No external network calls, API keys, or paid tokens are required for offline adversarial testing.

---

## 3. Exact Run Commands

From the repository root:

```powershell
# Run the adversarial unit and invariant test suite
python -m pytest members/devansh/test_adversarial_security.py -v

# Run the security scenario runner to populate security_test_log.csv
python members/devansh/run_security_suite.py
```

---

## 4. Actual Test Output

```
============================= test session starts =============================
platform win32 -- Python 3.12.0, pytest-8.3.3, pluggy-1.6.0
rootdir: C:\Users\iambe\.gemini\antigravity\scratch\red_thread_ai_detective
configfile: pytest.ini
collected 34 items

members/devansh/test_adversarial_security.py::TestDirectInjection::test_direct_injection_ignore_all_instructions_caught PASSED [  2%]
members/devansh/test_adversarial_security.py::TestDirectInjection::test_direct_injection_authority_impersonation_caught PASSED [  5%]
members/devansh/test_adversarial_security.py::TestDirectInjection::test_direct_injection_fullwidth_unicode_normalized_and_caught PASSED [  8%]
members/devansh/test_adversarial_security.py::TestDirectInjection::test_direct_injection_oversized_payload_truncated_and_safe PASSED [ 11%]
members/devansh/test_adversarial_security.py::TestIndirectInjection::test_indirect_injection_stored_evidence_e003_caught PASSED [ 14%]
members/devansh/test_adversarial_security.py::TestIndirectInjection::test_indirect_injection_presented_evidence_e003_caught PASSED [ 17%]
members/devansh/test_adversarial_security.py::TestIndirectInjection::test_indirect_injection_unpermitted_evidence_injection_filtered PASSED [ 20%]
members/devansh/test_adversarial_security.py::TestSpoilerExtraction::test_spoiler_future_fact_f004_uncited_caught_as_protected_leak PASSED [ 23%]
members/devansh/test_adversarial_security.py::TestSpoilerExtraction::test_spoiler_future_fact_f004_cited_caught_as_unauthorized_fact PASSED [ 26%]
members/devansh/test_adversarial_security.py::TestSpoilerExtraction::test_spoiler_future_evidence_e009_citation_caught PASSED [ 29%]
members/devansh/test_adversarial_security.py::TestSpoilerExtraction::test_spoiler_future_evidence_presented_by_player_dropped PASSED [ 32%]
members/devansh/test_adversarial_security.py::TestUnauthorizedClaims::test_unauthorized_fact_cross_npc_leak_caught PASSED [ 35%]
members/devansh/test_adversarial_security.py::TestUnauthorizedClaims::test_unauthorized_fact_citation_caught PASSED [ 38%]
members/devansh/test_adversarial_security.py::TestUnauthorizedClaims::test_uncited_assertion_of_authorized_fact_caught PASSED [ 41%]
members/devansh/test_adversarial_security.py::TestFallbackInvariance::test_fallback_invariants_across_all_attack_vectors[compromised] PASSED [ 44%]
members/devansh/test_adversarial_security.py::TestFallbackInvariance::test_fallback_invariants_across_all_attack_vectors[compromised_cited] PASSED [ 47%]
members/devansh/test_adversarial_security.py::TestFallbackInvariance::test_fallback_invariants_across_all_attack_vectors[cites_future_evidence] PASSED [ 50%]
members/devansh/test_adversarial_security.py::TestFallbackInvariance::test_fallback_invariants_across_all_attack_vectors[follows_evidence_inj] PASSED [ 52%]
members/devansh/test_adversarial_security.py::TestFallbackInvariance::test_fallback_invariants_across_all_attack_vectors[uncited] PASSED [ 55%]
members/devansh/test_adversarial_security.py::TestFallbackInvariance::test_fallback_invariants_across_all_attack_vectors[cites_unknown_fact] PASSED [ 58%]
members/devansh/test_adversarial_security.py::TestFallbackInvariance::test_fallback_invariants_across_all_attack_vectors[malformed] PASSED [ 61%]
members/devansh/test_adversarial_security.py::TestFallbackInvariance::test_fallback_invariants_across_all_attack_vectors[too_long] PASSED [ 64%]
members/devansh/test_adversarial_security.py::TestFallbackInvariance::test_fallback_invariants_across_all_attack_vectors[bad_metrics] PASSED [ 67%]
members/devansh/test_adversarial_security.py::TestFallbackInvariance::test_fallback_invariants_across_all_attack_vectors[timeout] PASSED [ 70%]
members/devansh/test_adversarial_security.py::TestFallbackInvariance::test_fallback_invariants_across_all_attack_vectors[error] PASSED [ 73%]
members/devansh/test_adversarial_security.py::TestObfuscationEvasionLimits::test_fullwidth_unicode_is_caught_by_normalization PASSED [ 76%]
members/devansh/test_adversarial_security.py::TestObfuscationEvasionLimits::test_documented_lexical_limits[leet_leak] PASSED [ 79%]
members/devansh/test_adversarial_security.py::TestObfuscationEvasionLimits::test_documented_lexical_limits[cyrillic_leak] PASSED [ 82%]
members/devansh/test_adversarial_security.py::TestObfuscationEvasionLimits::test_documented_lexical_limits[hyphen_leak] PASSED [ 85%]
members/devansh/test_adversarial_security.py::TestObfuscationEvasionLimits::test_documented_lexical_limits[zero_width_leak] PASSED [ 88%]
members/devansh/test_adversarial_security.py::TestObfuscationEvasionLimits::test_documented_lexical_limits[spaced_leak] PASSED [ 91%]
members/devansh/test_adversarial_security.py::TestObfuscationEvasionLimits::test_documented_lexical_limits[reversed_leak] PASSED [ 94%]
members/devansh/test_adversarial_security.py::TestObfuscationEvasionLimits::test_documented_lexical_limits[inflection_leak] PASSED [ 97%]
members/devansh/test_adversarial_security.py::TestObfuscationEvasionLimits::test_documented_lexical_limits[paraphrased_leak] PASSED [100%]

============================= 34 passed in 0.30s ==============================
```

---

## 5. Known Limitations & Sprint 2 Recommendations

1. **Current Lexical Detection:**
   - Detects all exact keyword leaks, casefold variants, and fullwidth Unicode normalization.
   - Word-boundary matching does not catch leet-speak (`br4ndy`), Cyrillic homoglyphs, or intra-word zero-width spaces (`\u200b`).
2. **Sprint 2 Roadmap:**
   - Integrate unicode character filtering (strip category `Cf` zero-width chars and normalize homoglyphs).
   - Employ a lightweight NLI or LLM-judge for semantic paraphrase leak detection.
