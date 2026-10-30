# ADR-0001: Keep canonical truth outside generation

Status: Accepted for the current prototype
Context: Free-form interrogation must not give the generator authority over
case truth, NPC permissions, or player progression.

Options:
1. Supply the entire case to one LLM and instruct it not to spoil.
2. Supply only NPC-authorized facts/evidence; validate its draft against
   trusted case and NPC context.
3. Use exclusively authored branching dialogue.

Decision: Option 2. Integration constructs the bounded request; generation
returns an untrusted draft; validation or fallback produces the result.

Consequences: Better enforceability and testability, at the cost of extra
authoring, validation work, and possible false-positive fallbacks.
A citation is not proof that prose is semantically correct.

Revisit if: Real-model evaluation shows unacceptable leakage or dialogue
quality, or if the shared contract changes.
