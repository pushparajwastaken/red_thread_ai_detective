# ADR-0002: Retain an offline deterministic path

Status: Accepted for the current prototype
Context: Contributors need reproducible tests without credentials, network,
a model server, or variable model outputs.

Options:
1. Require a live hosted model for all tests.
2. Test the integrated pipeline offline with a mock; run a separate,
   explicitly labeled real-model validation track.

Decision: Option 2.

Consequences: CI can test contracts, trust boundaries, failure handling,
and regression deterministically. Mock latency and canned answer quality
must never be presented as live-model performance.

Revisit if: A stable, budgeted model-test environment is available.
