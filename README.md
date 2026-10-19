# Red Thread - AI Detective Game

A prototype detective game using dynamic dialogue, evidence-based
interrogation, restricted NPC knowledge, and response validation.

## Project Goals

- Present evidence without revealing future plot information.
- Prevent NPCs from claiming facts they are not authorized to know.
- Validate generated dialogue and fall back safely when necessary.
- Benchmark dynamic dialogue against branching dialogue trees.

## Setup

Use Python 3.11 or newer.

Create a virtual environment:

    python -m venv .venv

Activate it in Windows PowerShell:

    .\.venv\Scripts\Activate.ps1

Install dependencies:

    python -m pip install -r requirements.txt

Run contract tests from the repository root:

    python -m pytest tests/test_contracts.py -q

## Repository Structure

- shared/: common data structures and interfaces
- members/: individual working areas and experiments
- src/: integrated application modules
- tests/: unit, integration and adversarial tests
- test_cases/: reusable security test cases
- results/: measured benchmark and test results
- docs/: architecture, decisions and reports
- scripts/: application and test entry points

## Team Workflow

1. Pull the latest main branch.
2. Create a feature branch for your assigned task.
3. Implement and test your component.
4. Open a pull request.
5. Obtain review before merging into main.

See shared/interfaces.md before implementing a module.

## Security Notice

NPC prompts must contain only authorized facts and evidence.
Never expose the entire canonical case state to the LLM.
Do not commit credentials, API keys or private configuration files.
