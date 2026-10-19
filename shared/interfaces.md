# Red Thread: Shared Interface Contracts

## Purpose

All team members must use these agreed data structures and function
signatures. Discuss interface changes with the integration lead before
changing shared contracts.

## Module 1: Case Engine

Owner: Richa

Location: src/case_engine/

Responsibilities:
- Store the canonical truth of the mystery.
- Define suspects, clues, facts and the timeline.
- Return case state using the shared CaseState structure.

Required function:

    def load_case(case_id: str) -> CaseState:
        ...

Import CaseState from shared.contracts.

Security: Do not pass the complete canonical case state to an NPC's
language model prompt.

## Module 2: NPC Knowledge

Owner: Anand

Location: src/epistemic_security/

Required function:

    def build_npc_context(
        case: CaseState,
        npc_id: str,
    ) -> NPCContext:
        ...

Return only facts and evidence authorized for that NPC.

## Module 3: Evidence Retrieval

Owner: Gagan

Location: src/evidence_retrieval/

Required function:

    def retrieve_evidence(
        question: str,
        permitted_evidence_ids: list[str],
    ) -> list[dict]:
        ...

Return only evidence IDs explicitly permitted by the caller.
Each evidence record should contain an evidence_id and its content.

## Module 4: Dialogue Generator

Owner: Anshul

Location: src/dialogue/

Required function:

    def generate_dialogue(
        request: DialogueRequest,
    ) -> str:
        ...

The initial implementation may use a deterministic mock response.
A later implementation may use a local or hosted LLM.

The generator must receive only the restricted dialogue request,
not the complete canonical case state.

## Module 5: Validator and Fallback

Owner: Harsh

Location: src/validation/

Required function:

    def validate_dialogue(
        request: DialogueRequest,
        generated_text: str,
        cited_fact_ids: list[str],
    ) -> DialogueResult:
        ...

Check schema, cited fact authorization, factual support and spoiler
constraints. Return a safe fallback response when validation fails.

Citation IDs alone do not prove that a generated statement is true.
Verify the claims against the canonical facts and permitted evidence.

## Module 6: Integration

Owners: Pushparaj and Khushi

Connect the modules into one interrogation flow:
case engine -> NPC knowledge -> evidence retrieval -> dialogue
generation -> validation/fallback -> player.

Keep the public function signatures stable.

## Module 7: Testing

Owners: Preksha and Paras

Location: tests/ and test_cases/

- Unit-test individual functions.
- Test unauthorized fact access.
- Test direct and indirect prompt injection.
- Test malformed model output.
- Test fallback behavior.

Devansh runs adversarial experiments and records reproducible results.

## Module 8: Benchmarking

Owner: Chhavi

Measure actual first-token latency, total response latency and token
usage where available. Record model, hardware, prompt size and sample
count. Do not report unmeasured targets as achieved results.

## Module 9: Branching Dialogue Baseline

Owner: Ananya

Build a deterministic branching dialogue baseline and compare it
with dynamic dialogue using the same case, questions and evaluation
criteria.

## Shared Rules and Contribution Workflow

### 1. Individual Development

- Each member must work only inside their assigned `members/<name>/` folder.
- Each member's folder should contain their implementation, component tests, results where applicable, and a README explaining setup and execution.
- Do not modify `src/`, `shared/`, or another member's folder without explicit approval from the integration lead.

### 2. Shared Contracts

- Import common data structures from `shared.contracts`.
- Do not rename contract fields or change public function signatures independently.
- Requests to modify `shared/` must be discussed with the integration lead first.
- The integration lead maintains the authoritative shared contracts.

### 3. Submission Workflow

- Pull the latest `main` before starting work.
- Create a separate feature branch for your assigned task.
- Commit and push your work to that branch.
- Before submission, run your component tests and document the results.
- Send the integration lead your branch name, files changed, test results, dependencies, and instructions to run your component.
- Do not merge branches into `main` or integrate code into `src/`. The integration lead reviews and integrates approved contributions.

### 4. Integration

- Only the integration lead moves or adapts approved implementations into `src/`.
- Integrated application tests belong in `tests/`.
- The integration lead resolves interface mismatches and verifies that the combined application works end to end.
- Members must report blockers and dependency issues immediately.

### 5. Security and Quality

- Do not commit API keys, credentials, or other secrets.
- Do not expose the full canonical case state to an NPC's language model prompt.
- Every security or performance claim must be supported by reproducible test results.
- Do not report unmeasured latency, cost, or security targets as achieved.
