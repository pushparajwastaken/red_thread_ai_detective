# ADR-0003: Defer database and durable-agent framework selection

Status: Proposed — decision pending spike
Context: The current production entry point is a Python function. Future
MVPs propose persistent sessions, event-aware memory, and agent planning.
Neither a database migration nor a durable workflow requirement has yet been
established by the current prototype.

Options to evaluate:
A. Keep Python orchestration; add a small relational event store.
B. Add a graph/agent framework for planning while retaining the case engine
   as the sole authority.
C. Add durable workflow execution if measured recovery needs justify it.

Provisional decision: Do not introduce a framework just to match the
presentation. First measure restart/replay requirements, operational
complexity, failure recovery, and the need for multi-step durable execution.

Acceptance for a future ADR: A spike demonstrates restart-safe replay,
NPC visibility filtering, idempotent state transitions, and measured
maintenance cost. Name the selected database/framework and migration
procedure only then.
