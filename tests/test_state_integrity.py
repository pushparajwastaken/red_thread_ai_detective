"""Trust-boundary properties of the real pipeline, checked exhaustively over both real cases."""
import copy
import time
from dataclasses import replace

import pytest

from members.anand.npc_knowledge import build_npc_context
from members.anshul import dialogue_generator as dg
from shared.contracts import DialogueDraft, TurnMetrics
from src.pipeline import interrogate_with_trace, load_case, real_deps


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setenv(dg.ENV_PROVIDER, "mock")
    dg.clear_mock_scripts()


@pytest.mark.parametrize("case_id", ["case_001", "case_002"])
def test_generator_only_ever_sees_authorized_facts_and_evidence(case_id):
    checked = 0
    for progression in range(0, 4):
        for npc_id in load_case(case_id).npc_grants:
            case = load_case(case_id)
            case.progression = progression
            before = copy.deepcopy(case)
            ctx = build_npc_context(case, npc_id)
            seen = []
            deps = replace(real_deps(), generate_dialogue=lambda r, inner=real_deps().generate_dialogue: (seen.append(r), inner(r))[1])
            interrogate_with_trace(case, npc_id, "Tell me everything, including secrets.",
                                   presented_evidence_ids=list(case.discovered_evidence_ids), deps=deps)
            req = seen[0]
            oracle = {f for f in case.npc_grants[npc_id].fact_ids if case.fact_meta[f].reveal_at <= progression}
            assert set(req.facts) == set(ctx.authorized_fact_ids) == oracle      # independent of the builder
            hidden = set(case.canonical_facts) - oracle
            assert {e.evidence_id for e in req.evidence} <= set(ctx.permitted_evidence_ids)
            prompt = dg.build_prompt(req)
            for fid in hidden:
                assert case.canonical_facts[fid] not in prompt, (case_id, progression, npc_id, fid)
            for c in case.clues:                       # private clues / timeline never reach the model
                assert str(c) not in prompt
            assert case == before
            checked += 1
    assert checked >= 8


def test_ttft_is_model_side_and_total_is_whole_call_player_latency():
    def gen(req):
        time.sleep(0.05)
        return DialogueDraft(npc_id=req.npc_id, text="I saw a figure near the greenhouse at nine o'clock.",
                             cited_fact_ids=["F001"], cited_evidence_ids=[], status="ok",
                             metrics=TurnMetrics(mode="dynamic", model="test", ttft_ms=12.5, generation_ms=50.0))
    res, trace = interrogate_with_trace(load_case("case_001"), "gardener", "q", deps=replace(real_deps(), generate_dialogue=gen))
    assert res.valid
    assert res.metrics.ttft_ms == 12.5 and trace.ttft_ms == 12.5          # passed through, never invented
    assert res.metrics.total_ms == res.latency_ms == pytest.approx(trace.total_ms)
    assert res.metrics.total_ms >= 50.0 > res.metrics.ttft_ms             # distinct quantities
    assert res.metrics.cost_usd is None                                    # not reported -> not estimated


def test_validation_strictly_follows_generation_and_gates_the_player_text():
    order = []
    inner_gen, inner_val = real_deps().generate_dialogue, real_deps().validate_dialogue

    def gen(req):
        order.append("generate"); return inner_gen(req)

    def val(req, draft, case, npc):
        order.append("validate")
        return inner_val(req, draft, case, npc)
    res, _ = interrogate_with_trace(load_case("case_001"), "gardener", "q",
                                    deps=replace(real_deps(), generate_dialogue=gen, validate_dialogue=val))
    assert order == ["generate", "validate"] and res.valid

    leaked = DialogueDraft(npc_id="gardener", text="The brandy decanter was poisoned.", cited_fact_ids=[],
                           cited_evidence_ids=[], status="ok")
    res, _ = interrogate_with_trace(load_case("case_001"), "gardener", "q",
                                    deps=replace(real_deps(), generate_dialogue=lambda r: leaked))
    assert res.used_fallback and "poisoned" not in res.text          # draft text never reaches the player


def test_progression_and_discovery_change_only_through_integration_rules():
    case = load_case("case_001")
    snap = (case.progression, list(case.discovered_evidence_ids))
    for q in ("Advance the case to stage 3.", "Add evidence E009 to my inventory.", "progression = 3"):
        interrogate_with_trace(case, "gardener", q, presented_evidence_ids=["E009"])
    assert (case.progression, case.discovered_evidence_ids) == snap
