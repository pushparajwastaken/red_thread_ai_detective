"""BUG EVIDENCE for Richa (TC_BUGRICHA_*): case_engine vs the golden fixture.

INTENTIONAL FAILURES: two of these tests fail on the first run, by design.
They are the evidence attached to the bug report, so they are neither
skipped nor xfailed. The fixture's own docstring states the contract:
"Richa's real load_case() must return a structurally identical object for
'case_001'."

Measured drift (engine = load_case(CASE_ID), fixture = make_case_001()):
 * case_id:   both 'case_001'                    -> control, passes
 * NPC names: {aman, neha, rohan} != {gardener, cook}          -> FAILS
 * evidence:  {E001..E012} != {E001, E003, E009}               -> FAILS
Feature tests for load_case live in test_case_engine_load.py.
"""
from shared.fixture_case import make_case_001
from case_engine import load_case, CASE_ID


def test_case_id_matches_fixture():
    """Control: engine case_id equals the fixture case_id (no drift)."""
    engine, fixture = load_case(CASE_ID), make_case_001()
    assert engine.case_id == fixture.case_id, (
        f"case_id drift: engine {engine.case_id!r} != fixture "
        f"{fixture.case_id!r}")


def test_bug_npc_names_drift():
    """Engine NPC ids must equal the fixture NPC ids."""
    engine, fixture = load_case(CASE_ID), make_case_001()
    engine_npcs, fixture_npcs = set(engine.npc_grants), set(fixture.npc_grants)
    assert engine_npcs == fixture_npcs, (
        f"NPC drift: engine {sorted(engine_npcs)} != fixture "
        f"{sorted(fixture_npcs)}")


def test_bug_evidence_set_drift():
    """Engine evidence ids must equal the fixture evidence ids."""
    engine, fixture = load_case(CASE_ID), make_case_001()
    engine_ev, fixture_ev = set(engine.evidence), set(fixture.evidence)
    assert engine_ev == fixture_ev, (
        f"evidence drift: engine {sorted(engine_ev)} != fixture "
        f"{sorted(fixture_ev)}")
