# SUBMISSION — Module 4: Dialogue Generator (Anshul)

**Status:** code-complete and review-ready. Three fields remain intentionally
unfilled because they are machine-specific and the team rule forbids
reporting unmeasured results as achieved:

- §1 commit SHA & base SHA (paste from `git rev-parse HEAD` / `git merge-base`)
- §5 pytest output (paste from running the commands in §4)
- §6 real-model evidence table (paste from `results/ollama_smoke.json`)

All other sections are final.

---

## 1. Branch & commits

- **Branch:** `members/anshul` (push with `git push origin members/anshul`)
- **Latest commit SHA:** *PASTE →* `git rev-parse HEAD`
- **Base:** branched from `main` @ *PASTE →* `git merge-base main members/anshul`
- **Scope check:** this branch touches only `members/anshul/` — no edits to
  `shared/`, `src/`, `tests/`, or other members' folders.

## 2. Files delivered

| File | Purpose |
|---|---|
| `members/anshul/dialogue_generator.py` | Module 4 implementation: prompt builder (trust layout), strict JSON parser, deterministic mock backend, streaming Ollama backend |
| `members/anshul/test_dialogue_generator.py` | 18 test functions (22 offline cases + 2 opt-in real-model cases) |
| `members/anshul/SUBMISSION.md` | this file |
| `members/anshul/results/` | created automatically by the real-model tests |

## 3. Dependencies

| Package | Version | In `requirements.txt`? |
|---|---|---|
| `pytest` | (repo-pinned) | **yes** — unit tests run as-is |
| `requests` | *PASTE from `pip show requests`* | **NO** — see §8. Imported lazily inside `OllamaBackend.complete`, so mock mode and all CI tests need zero third-party packages. |

## 4. Run commands

```bash
# Offline unit tests (no Ollama needed; expected: 20 passed, 2 skipped)
python -m pytest members/anshul/test_dialogue_generator.py -q

# Real-model tests (start Ollama first)
ollama pull qwen2.5:3b-instruct
RUN_LLM_SMOKE=1 LLM_MODEL=qwen2.5:3b-instruct \
    python -m pytest members/anshul/test_dialogue_generator.py -q
# writes members/anshul/results/ollama_smoke.json and injection_attempt_ollama.json
