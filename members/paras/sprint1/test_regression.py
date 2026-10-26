"""
Regression & Reference-Flow Tests — Paras Gupta (Module 7)
===========================================================
Sprint 1 | Red Thread AI Detective

Rules:
- Only imports from shared/ (never src/)
- Does NOT edit tests/test_reference_flow.py
- All tests are deterministic (no network, no randomness)
- Reason codes are compared as constants, never as hardcoded strings
- Reference-flow signature tests are skip-guarded (pass if module not yet implemented)
"""

import inspect
import pytest

from shared.contracts import (
    CaseState,
    ContractError,
    DialogueDraft,
    DialogueRequest,
    DialogueResult,
    EvidenceItem,
    FactMeta,
    NPCContext,
    NPCGrant,
    Reason,
    SAFE_FALLBACK_TEXT,
    TurnMetrics,
    UnknownNPCError,
)
from shared.fixture_case import make_case_001


# ============================================================
# SECTION 1 — CaseState Contract Integrity Tests
# ============================================================

class TestCaseStateContract:
    """Verify CaseState construction enforces its documented invariants."""

    def test_valid_case_state_constructs_without_error(self):
        """Fixture case must construct cleanly at progression 0."""
        case = make_case_001()
        assert case.case_id == "case_001"
        assert case.progression == 0

    def test_valid_case_state_at_higher_progression(self):
        """CaseState at progression=2 must also be valid."""
        case = make_case_001(progression=2)
        assert case.progression == 2

    def test_negative_progression_raises_contract_error(self):
        """progression < 0 must raise ContractError."""
        with pytest.raises(ContractError):
            CaseState(
                case_id="case_x",
                canonical_facts={"F001": "A fact."},
                clues=[],
                timeline=[],
                progression=-1,
            )

    def test_fact_meta_key_not_in_canonical_facts_raises(self):
        """fact_meta referencing an unknown fact_id must raise ContractError."""
        with pytest.raises(ContractError):
            CaseState(
                case_id="case_x",
                canonical_facts={"F001": "A fact."},
                clues=[],
                timeline=[],
                fact_meta={"F999": FactMeta(0, "fact", [])},  # F999 not in canonical_facts
            )

    def test_evidence_key_mismatch_raises(self):
        """evidence dict key must equal EvidenceItem.evidence_id, else ContractError."""
        with pytest.raises(ContractError):
            CaseState(
                case_id="case_x",
                canonical_facts={"F001": "A fact."},
                clues=[],
                timeline=[],
                evidence={
                    "E001": EvidenceItem(
                        evidence_id="E999",   # key is E001 but id is E999 → mismatch
                        content="Some evidence.",
                    )
                },
            )

    def test_evidence_referencing_unknown_fact_raises(self):
        """EvidenceItem.fact_ids must only reference existing canonical_facts."""
        with pytest.raises(ContractError):
            CaseState(
                case_id="case_x",
                canonical_facts={"F001": "A fact."},
                clues=[],
                timeline=[],
                evidence={
                    "E001": EvidenceItem(
                        evidence_id="E001",
                        content="Evidence content.",
                        fact_ids=["F999"],  # F999 not in canonical_facts
                    )
                },
            )

    def test_npc_grant_referencing_unknown_fact_raises(self):
        """NPCGrant.fact_ids must only reference existing canonical_facts."""
        with pytest.raises(ContractError):
            CaseState(
                case_id="case_x",
                canonical_facts={"F001": "A fact."},
                clues=[],
                timeline=[],
                npc_grants={
                    "suspect": NPCGrant(fact_ids=["F999"])  # F999 does not exist
                },
            )

    def test_npc_grant_referencing_unknown_evidence_raises(self):
        """NPCGrant.evidence_ids must only reference existing evidence."""
        with pytest.raises(ContractError):
            CaseState(
                case_id="case_x",
                canonical_facts={"F001": "A fact."},
                clues=[],
                timeline=[],
                evidence={
                    "E001": EvidenceItem("E001", "Content.")
                },
                npc_grants={
                    "suspect": NPCGrant(evidence_ids=["E999"])  # E999 does not exist
                },
            )

    def test_discovered_evidence_id_not_in_evidence_raises(self):
        """discovered_evidence_ids must only reference evidence in the case."""
        with pytest.raises(ContractError):
            CaseState(
                case_id="case_x",
                canonical_facts={"F001": "A fact."},
                clues=[],
                timeline=[],
                evidence={
                    "E001": EvidenceItem("E001", "Content.")
                },
                discovered_evidence_ids=["E999"],  # E999 not in evidence
            )

    def test_empty_case_state_constructs_with_defaults(self):
        """Minimal CaseState with only required fields must be valid."""
        case = CaseState(
            case_id="case_min",
            canonical_facts={},
            clues=[],
            timeline=[],
        )
        assert case.progression == 0
        assert case.fact_meta == {}
        assert case.evidence == {}
        assert case.npc_grants == {}
        assert case.discovered_evidence_ids == []


# ============================================================
# SECTION 2 — DialogueRequest Contract Tests
# ============================================================

class TestDialogueRequestContract:
    """Verify DialogueRequest enforces its authorization invariants."""

    def test_valid_dialogue_request_constructs(self):
        """A well-formed DialogueRequest with matching IDs must not raise."""
        req = DialogueRequest(
            npc_id="gardener",
            question="What did you see?",
            authorized_fact_ids=["F001", "F002"],
            permitted_evidence_ids=["E001"],
            facts={"F001": "I saw a figure near the greenhouse."},
            evidence=[EvidenceItem("E001", "A torn glove.", ["F001"])],
            presented_evidence_ids=["E001"],
        )
        assert req.npc_id == "gardener"

    def test_unauthorized_fact_in_facts_dict_raises(self):
        """Facts dict carrying an ID not in authorized_fact_ids must raise ContractError."""
        with pytest.raises(ContractError):
            DialogueRequest(
                npc_id="gardener",
                question="Tell me.",
                authorized_fact_ids=["F001"],
                permitted_evidence_ids=[],
                facts={"F002": "Unauthorized fact text."},  # F002 not authorized
            )

    def test_unpermitted_evidence_in_evidence_list_raises(self):
        """Evidence list carrying an ID not in permitted_evidence_ids must raise ContractError."""
        with pytest.raises(ContractError):
            DialogueRequest(
                npc_id="gardener",
                question="Tell me.",
                authorized_fact_ids=["F001"],
                permitted_evidence_ids=["E001"],
                evidence=[EvidenceItem("E999", "Unpermitted evidence.")],  # not permitted
            )

    def test_presented_id_not_in_permitted_raises(self):
        """presented_evidence_ids must be a subset of permitted_evidence_ids."""
        with pytest.raises(ContractError):
            DialogueRequest(
                npc_id="gardener",
                question="Tell me.",
                authorized_fact_ids=[],
                permitted_evidence_ids=["E001"],
                presented_evidence_ids=["E999"],  # E999 not in permitted
            )

    def test_empty_facts_evidence_presented_is_valid_edge_case(self):
        """All optional ID lists being empty is a legitimate valid state."""
        req = DialogueRequest(
            npc_id="gardener",
            question="",
            authorized_fact_ids=[],
            permitted_evidence_ids=[],
            facts={},
            evidence=[],
            presented_evidence_ids=[],
        )
        assert req.facts == {}
        assert req.evidence == []
        assert req.presented_evidence_ids == []

    def test_multiple_authorized_facts_all_included_is_valid(self):
        """All authorized fact IDs may be included in facts dict."""
        req = DialogueRequest(
            npc_id="cook",
            question="Were you in the kitchen?",
            authorized_fact_ids=["F001", "F002", "F003"],
            permitted_evidence_ids=[],
            facts={
                "F001": "Fact 1 text.",
                "F002": "Fact 2 text.",
                "F003": "Fact 3 text.",
            },
        )
        assert set(req.facts.keys()) == {"F001", "F002", "F003"}


# ============================================================
# SECTION 3 — DialogueResult Contract Tests
# ============================================================

class TestDialogueResultContract:
    """Verify DialogueResult enforces its structural invariants."""

    def test_valid_result_true_false(self):
        """valid=True, used_fallback=False is the normal success case."""
        result = DialogueResult(
            npc_id="gardener",
            text="I saw someone near the greenhouse.",
            cited_fact_ids=["F001"],
            valid=True,
            used_fallback=False,
            latency_ms=150.0,
        )
        assert result.valid is True
        assert result.used_fallback is False

    def test_valid_result_false_true(self):
        """valid=False, used_fallback=True is the normal fallback case."""
        result = DialogueResult(
            npc_id="gardener",
            text=SAFE_FALLBACK_TEXT,
            cited_fact_ids=[],
            valid=False,
            used_fallback=True,
            latency_ms=20.0,
        )
        assert result.used_fallback is True
        assert result.text == SAFE_FALLBACK_TEXT

    def test_both_valid_and_fallback_true_raises(self):
        """valid=True and used_fallback=True simultaneously must raise ContractError."""
        with pytest.raises(ContractError):
            DialogueResult(
                npc_id="gardener",
                text="Some text.",
                cited_fact_ids=[],
                valid=True,
                used_fallback=True,  # invalid: cannot be both
                latency_ms=10.0,
            )

    def test_both_valid_and_fallback_false_raises(self):
        """valid=False and used_fallback=False simultaneously must raise ContractError."""
        with pytest.raises(ContractError):
            DialogueResult(
                npc_id="gardener",
                text="Some text.",
                cited_fact_ids=[],
                valid=False,
                used_fallback=False,  # invalid: must be one or the other
                latency_ms=10.0,
            )

    def test_negative_latency_raises(self):
        """latency_ms < 0 must raise ContractError."""
        with pytest.raises(ContractError):
            DialogueResult(
                npc_id="gardener",
                text="Some text.",
                cited_fact_ids=[],
                valid=True,
                used_fallback=False,
                latency_ms=-1.0,  # negative latency is invalid
            )

    def test_zero_latency_is_valid(self):
        """latency_ms == 0.0 is a valid edge case (no minimum above zero)."""
        result = DialogueResult(
            npc_id="gardener",
            text="I cannot answer that reliably.",
            cited_fact_ids=[],
            valid=False,
            used_fallback=True,
            latency_ms=0.0,
        )
        assert result.latency_ms == 0.0

    def test_fallback_with_cited_facts_raises(self):
        """A fallback result (used_fallback=True) must carry no citations."""
        with pytest.raises(ContractError):
            DialogueResult(
                npc_id="gardener",
                text=SAFE_FALLBACK_TEXT,
                cited_fact_ids=["F001"],  # citations not allowed with fallback
                valid=False,
                used_fallback=True,
                latency_ms=10.0,
            )

    def test_fallback_with_cited_evidence_raises(self):
        """A fallback result must also carry no evidence citations."""
        with pytest.raises(ContractError):
            DialogueResult(
                npc_id="gardener",
                text=SAFE_FALLBACK_TEXT,
                cited_fact_ids=[],
                cited_evidence_ids=["E001"],  # evidence citations not allowed with fallback
                valid=False,
                used_fallback=True,
                latency_ms=10.0,
            )

    def test_safe_fallback_text_exact_value(self):
        """SAFE_FALLBACK_TEXT must be exactly the documented string — no variations."""
        assert SAFE_FALLBACK_TEXT == "I cannot answer that reliably."

    def test_reason_codes_are_correct_string_constants(self):
        """Spot-check Reason constants to verify they are the expected string values."""
        assert Reason.OK == "OK"
        assert Reason.SETUP_ERROR == "SETUP_ERROR"
        assert Reason.GEN_TIMEOUT == "GEN_TIMEOUT"
        assert Reason.GEN_ERROR == "GEN_ERROR"
        assert Reason.GEN_MALFORMED == "GEN_MALFORMED"
        assert Reason.SCHEMA_INVALID == "SCHEMA_INVALID"
        assert Reason.AUTH_MISMATCH == "AUTH_MISMATCH"
        assert Reason.AUTH_FUTURE == "AUTH_FUTURE"
        assert Reason.UNKNOWN_FACT_ID == "UNKNOWN_FACT_ID"
        assert Reason.UNAUTHORIZED_FACT == "UNAUTHORIZED_FACT"
        assert Reason.UNKNOWN_EVIDENCE_ID == "UNKNOWN_EVIDENCE_ID"
        assert Reason.UNAUTHORIZED_EVIDENCE == "UNAUTHORIZED_EVIDENCE"
        assert Reason.PROTECTED_TERM_LEAK == "PROTECTED_TERM_LEAK"
        assert Reason.UNCITED_ASSERTION == "UNCITED_ASSERTION"
        assert Reason.VALIDATOR_ERROR == "VALIDATOR_ERROR"


# ============================================================
# SECTION 4 — Determinism & Edge-Case Regression Tests
# ============================================================

class TestDeterminismAndEdgeCases:
    """Verify fixture determinism, NPC grant boundaries, and case-sensitive IDs."""

    def test_make_case_001_called_twice_identical_facts(self):
        """make_case_001() must return equivalent data on repeated calls (determinism)."""
        case_a = make_case_001()
        case_b = make_case_001()
        assert case_a.case_id == case_b.case_id
        assert case_a.canonical_facts == case_b.canonical_facts
        assert set(case_a.evidence.keys()) == set(case_b.evidence.keys())
        assert set(case_a.npc_grants.keys()) == set(case_b.npc_grants.keys())

    def test_make_case_001_progression_parameter_changes_only_progression(self):
        """Two calls with different progressions must differ ONLY in progression."""
        case_0 = make_case_001(progression=0)
        case_2 = make_case_001(progression=2)
        assert case_0.progression == 0
        assert case_2.progression == 2
        assert case_0.canonical_facts == case_2.canonical_facts
        assert set(case_0.evidence.keys()) == set(case_2.evidence.keys())

    def test_f004_is_spoiler_at_progression_zero(self):
        """F004 has reveal_at=2; at progression=0 it must be treated as unrevealed."""
        case = make_case_001(progression=0)
        f004_meta = case.fact_meta["F004"]
        assert f004_meta.reveal_at == 2
        assert case.progression < f004_meta.reveal_at, (
            "F004 should be a spoiler at progression=0"
        )

    def test_f004_is_revealed_at_progression_two(self):
        """F004 has reveal_at=2; at progression=2 it must be visible."""
        case = make_case_001(progression=2)
        f004_meta = case.fact_meta["F004"]
        assert case.progression >= f004_meta.reveal_at, (
            "F004 should be revealed at progression=2"
        )

    def test_e009_is_unrevealed_at_progression_zero(self):
        """Evidence E009 has reveal_at=2; at progression=0 it must be treated as future."""
        case = make_case_001(progression=0)
        e009 = case.evidence["E009"]
        assert e009.reveal_at == 2
        assert case.progression < e009.reveal_at, (
            "E009 should not be accessible at progression=0"
        )

    def test_e009_is_revealed_at_progression_two(self):
        """Evidence E009 must be accessible at progression=2."""
        case = make_case_001(progression=2)
        e009 = case.evidence["E009"]
        assert case.progression >= e009.reveal_at

    def test_gardener_grant_includes_f001_f002(self):
        """Gardener must be granted exactly F001 and F002 (not F003, F004, L001)."""
        case = make_case_001()
        grant = case.npc_grants["gardener"]
        assert "F001" in grant.fact_ids
        assert "F002" in grant.fact_ids
        assert "F003" not in grant.fact_ids
        assert "F004" not in grant.fact_ids
        assert "L001" not in grant.fact_ids

    def test_cook_grant_includes_f003_l001(self):
        """Cook must be granted exactly F003 and L001 (not F001, F002, F004)."""
        case = make_case_001()
        grant = case.npc_grants["cook"]
        assert "F003" in grant.fact_ids
        assert "L001" in grant.fact_ids
        assert "F001" not in grant.fact_ids
        assert "F002" not in grant.fact_ids
        assert "F004" not in grant.fact_ids

    def test_gardener_evidence_grant(self):
        """Gardener must be granted E001 and E003 (hostile injection fixture)."""
        case = make_case_001()
        grant = case.npc_grants["gardener"]
        assert "E001" in grant.evidence_ids
        assert "E003" in grant.evidence_ids

    def test_cook_has_no_evidence_grant(self):
        """Cook has no evidence grant — evidence_ids must be empty."""
        case = make_case_001()
        grant = case.npc_grants["cook"]
        assert grant.evidence_ids == []

    def test_l001_is_cover_story_kind(self):
        """L001 must have kind='cover_story', marking it as an authored in-world lie."""
        case = make_case_001()
        l001_meta = case.fact_meta["L001"]
        assert l001_meta.kind == "cover_story"

    def test_f001_is_regular_fact_kind(self):
        """F001 must have kind='fact' (the default kind)."""
        case = make_case_001()
        f001_meta = case.fact_meta["F001"]
        assert f001_meta.kind == "fact"

    def test_case_sensitive_id_f001_vs_lowercase(self):
        """IDs are case-sensitive: 'f001' must NOT match 'F001'."""
        case = make_case_001()
        assert "F001" in case.canonical_facts
        assert "f001" not in case.canonical_facts  # lowercase is a different key

    def test_case_sensitive_id_e001_vs_lowercase(self):
        """Evidence IDs are case-sensitive: 'e001' must NOT match 'E001'."""
        case = make_case_001()
        assert "E001" in case.evidence
        assert "e001" not in case.evidence

    def test_discovered_evidence_ids_in_fixture(self):
        """Fixture must have E001 and E003 as pre-discovered evidence."""
        case = make_case_001()
        assert "E001" in case.discovered_evidence_ids
        assert "E003" in case.discovered_evidence_ids
        assert "E009" not in case.discovered_evidence_ids  # future evidence

    def test_e003_is_hostile_injection_fixture(self):
        """E003 content contains a prompt injection payload — a known security test fixture."""
        case = make_case_001()
        e003 = case.evidence["E003"]
        assert "IGNORE ALL PREVIOUS INSTRUCTIONS" in e003.content

    def test_f004_terms_include_poison_variants(self):
        """F004 terms must include both 'poison' and 'poisoned' (inflection coverage)."""
        case = make_case_001()
        terms = case.fact_meta["F004"].terms
        assert "poison" in terms
        assert "poisoned" in terms

    def test_all_fact_meta_keys_exist_in_canonical_facts(self):
        """Every key in fact_meta must have a corresponding canonical_facts entry."""
        case = make_case_001()
        for fid in case.fact_meta:
            assert fid in case.canonical_facts, (
                f"fact_meta references {fid} which is missing from canonical_facts"
            )

    def test_all_evidence_keys_match_evidence_ids(self):
        """Every evidence dict key must match its EvidenceItem.evidence_id."""
        case = make_case_001()
        for key, item in case.evidence.items():
            assert key == item.evidence_id, (
                f"Evidence dict key '{key}' != evidence_id '{item.evidence_id}'"
            )

    def test_npc_grant_fact_ids_exist_in_canonical_facts(self):
        """All NPC grant fact IDs must be present in canonical_facts (referential integrity)."""
        case = make_case_001()
        for npc_id, grant in case.npc_grants.items():
            for fid in grant.fact_ids:
                assert fid in case.canonical_facts, (
                    f"NPC '{npc_id}' grants fact '{fid}' which is not in canonical_facts"
                )

    def test_npc_grant_evidence_ids_exist_in_evidence(self):
        """All NPC grant evidence IDs must reference existing evidence (referential integrity)."""
        case = make_case_001()
        for npc_id, grant in case.npc_grants.items():
            for eid in grant.evidence_ids:
                assert eid in case.evidence, (
                    f"NPC '{npc_id}' grants evidence '{eid}' which is not in case.evidence"
                )

    def test_dialogue_draft_defaults(self):
        """DialogueDraft default status must be 'ok' and text must be empty string."""
        draft = DialogueDraft(npc_id="gardener")
        assert draft.status == "ok"
        assert draft.text == ""
        assert draft.cited_fact_ids == []
        assert draft.cited_evidence_ids == []

    def test_turn_metrics_default_mode(self):
        """TurnMetrics default mode must be 'dynamic'."""
        metrics = TurnMetrics()
        assert metrics.mode == "dynamic"
        assert metrics.total_ms == 0.0
        assert metrics.cost_usd is None
        assert metrics.ttft_ms is None


# ============================================================
# SECTION 5 — Reference-Flow Signature Tests
# (Skip-guarded: pass if module not yet implemented)
# ============================================================

class TestReferenceFlowSignatures:
    """
    Validate that implemented modules expose the exact public signatures
    documented in interfaces.md. Each test is skip-guarded so it passes
    gracefully when a module has not yet been implemented.
    """

    def test_load_case_signature(self):
        """load_case(case_id: str) -> CaseState"""
        mod = pytest.importorskip(
            "members.richa.case_engine",
            reason="Case Engine (Richa) not yet implemented",
        )
        fn = getattr(mod, "load_case", None)
        assert fn is not None, "load_case not found in members.richa.case_engine"
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())
        assert "case_id" in params, f"Expected 'case_id' param, got: {params}"

    def test_build_npc_context_signature(self):
        """build_npc_context(case: CaseState, npc_id: str) -> NPCContext"""
        mod = pytest.importorskip(
            "members.anand.npc_knowledge",
            reason="NPC Knowledge (Anand) not yet implemented",
        )
        fn = getattr(mod, "build_npc_context", None)
        assert fn is not None, "build_npc_context not found"
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())
        assert "case" in params
        assert "npc_id" in params

    def test_retrieve_evidence_signature(self):
        """retrieve_evidence(question, permitted_evidence_ids, *, case, top_k=3) -> list"""
        mod = pytest.importorskip(
            "members.gagan.evidence_retrieval",
            reason="Evidence Retrieval (Gagan) not yet implemented",
        )
        fn = getattr(mod, "retrieve_evidence", None)
        assert fn is not None, "retrieve_evidence not found"
        sig = inspect.signature(fn)
        params = sig.parameters
        assert "question" in params
        assert "permitted_evidence_ids" in params
        assert "case" in params
        # top_k must be a keyword-only param with default 3
        assert params["case"].kind in (
            inspect.Parameter.KEYWORD_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
        if "top_k" in params:
            assert params["top_k"].default == 3

    def test_generate_dialogue_signature(self):
        """generate_dialogue(request: DialogueRequest) -> DialogueDraft"""
        mod = pytest.importorskip(
            "members.anshul.dialogue_generator",
            reason="Dialogue Generator (Anshul) not yet implemented",
        )
        fn = getattr(mod, "generate_dialogue", None)
        assert fn is not None, "generate_dialogue not found"
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())
        assert "request" in params

    def test_validate_dialogue_signature(self):
        """validate_dialogue(request, draft, case, npc) -> DialogueResult"""
        mod = pytest.importorskip(
            "members.harsh.validator",
            reason="Validator (Harsh) not yet implemented",
        )
        fn = getattr(mod, "validate_dialogue", None)
        assert fn is not None, "validate_dialogue not found"
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())
        assert "request" in params
        assert "draft" in params
        assert "case" in params
        assert "npc" in params

    def test_make_fallback_signature(self):
        """make_fallback(npc_id, reasons, metrics=None) -> DialogueResult"""
        mod = pytest.importorskip(
            "members.harsh.validator",
            reason="Validator (Harsh) not yet implemented",
        )
        fn = getattr(mod, "make_fallback", None)
        assert fn is not None, "make_fallback not found"
        sig = inspect.signature(fn)
        params = sig.parameters
        assert "npc_id" in params
        assert "reasons" in params
        if "metrics" in params:
            assert params["metrics"].default is None

    def test_interrogate_signature(self):
        """interrogate(case, npc_id, question, *, presented_evidence_ids=()) -> DialogueResult"""
        mod = pytest.importorskip(
            "members.pushparaj.integration",
            reason="Integration (Pushparaj) not yet implemented",
        )
        fn = getattr(mod, "interrogate", None)
        assert fn is not None, "interrogate not found"
        sig = inspect.signature(fn)
        params = sig.parameters
        assert "case" in params
        assert "npc_id" in params
        assert "question" in params
        if "presented_evidence_ids" in params:
            default = params["presented_evidence_ids"].default
            assert default == () or default == [], (
                "presented_evidence_ids default must be empty iterable"
            )


# ============================================================
# SECTION 6 — Progression Boundary Regression Tests
# ============================================================

class TestProgressionBoundary:
    """
    Pure data assertions on the fixture to verify progression-gating logic
    is correct WITHOUT requiring any external module implementation.
    """

    def test_f004_unrevealed_boundary(self):
        """F004 reveal_at=2 means: at progression=1 it is still a spoiler."""
        case = make_case_001(progression=1)
        reveal_at = case.fact_meta["F004"].reveal_at
        assert case.progression < reveal_at, (
            f"Expected F004 to be unrevealed at progression=1 "
            f"(reveal_at={reveal_at})"
        )

    def test_f004_exactly_at_reveal_boundary(self):
        """At progression == reveal_at, the fact must be considered revealed."""
        case = make_case_001(progression=2)
        reveal_at = case.fact_meta["F004"].reveal_at
        assert case.progression >= reveal_at, (
            f"F004 should be visible at progression=2 (reveal_at={reveal_at})"
        )

    def test_f001_always_revealed(self):
        """F001 has reveal_at=0 — it must be visible at any progression including 0."""
        case = make_case_001(progression=0)
        reveal_at = case.fact_meta["F001"].reveal_at
        assert reveal_at == 0
        assert case.progression >= reveal_at

    def test_e009_unrevealed_at_progression_zero(self):
        """E009 has reveal_at=2 and must be gated at progression=0."""
        case = make_case_001(progression=0)
        e009 = case.evidence["E009"]
        assert e009.reveal_at == 2
        assert case.progression < e009.reveal_at

    def test_e009_revealed_at_progression_two(self):
        """E009 must be accessible at progression=2."""
        case = make_case_001(progression=2)
        e009 = case.evidence["E009"]
        assert case.progression >= e009.reveal_at

    def test_e001_always_accessible(self):
        """E001 has reveal_at=0 — always accessible from the start."""
        case = make_case_001(progression=0)
        e001 = case.evidence["E001"]
        assert e001.reveal_at == 0
        assert case.progression >= e001.reveal_at

    def test_e003_accessible_at_progression_zero(self):
        """E003 (hostile injection fixture) has reveal_at=0 — accessible from the start."""
        case = make_case_001(progression=0)
        e003 = case.evidence["E003"]
        assert e003.reveal_at == 0
        assert case.progression >= e003.reveal_at

    def test_reveal_at_helper_returns_zero_for_unknown_fact(self):
        """CaseState.reveal_at() must return 0 for a fact_id with no metadata entry."""
        case = make_case_001()
        # Unknown ID has no metadata → defaults to 0 (always revealed)
        assert case.reveal_at("F_NONEXISTENT") == 0

    def test_reveal_at_helper_returns_correct_value_for_f004(self):
        """CaseState.reveal_at() must return 2 for F004."""
        case = make_case_001()
        assert case.reveal_at("F004") == 2

    def test_all_evidence_reveal_at_values_are_non_negative(self):
        """All evidence reveal_at values must be >= 0 (no negative gating)."""
        case = make_case_001()
        for eid, item in case.evidence.items():
            assert item.reveal_at >= 0, (
                f"Evidence '{eid}' has negative reveal_at={item.reveal_at}"
            )

    def test_all_fact_meta_reveal_at_values_are_non_negative(self):
        """All fact_meta reveal_at values must be >= 0."""
        case = make_case_001()
        for fid, meta in case.fact_meta.items():
            assert meta.reveal_at >= 0, (
                f"Fact '{fid}' has negative reveal_at={meta.reveal_at}"
            )
