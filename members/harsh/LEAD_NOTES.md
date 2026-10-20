# Integration handoff notes

Base reviewed: `720634d26b5c41c3427ebea6f10f59712d5d0666`.

No shared contract changes are required by this implementation. Public functions use the exact v2 signatures and shared classes. Copying/integration is owned by the lead.

## Root README workflow correction

Failing scenario: a contributor follows root README steps 4–5 and opens a PR for merging into `main`, contradicting `shared/interfaces.md`.

Proposed diff for the lead (not applied outside the member folder):

```diff
-3. Implement and test your component.
-4. Open a pull request.
-5. Obtain review before merging into main.
+3. Implement and test only inside members/<name>/.
+4. Push your own branch. Do not open PRs into main and do not merge.
+5. Submit members/<name>/SUBMISSION.md with branch, commit SHA, files,
+   dependencies, exact run command, test output and known limits.
+6. The lead reviews, copies approved code into src/, owns shared/,
+   and resolves interface mismatches.
```

## Empty environment template

Failing scenario: a generator/integration contributor opens `.env.example` at the reviewed base and finds an empty file. The shared interface documentation lists four required variables.

Proposed contents for the lead:

```dotenv
LLM_PROVIDER=
LLM_MODEL=
LLM_TIMEOUT_S=
LLM_API_KEY=
```

Never place actual values or credentials in this handoff. The validator and its local tests use no environment variables.

## Acceptance suite availability

`shared/interfaces.md` references `tests/test_reference_flow.py`, but that file is absent at the reviewed base. Member tests validate Module 5 against the golden fixture. End-to-end integration acceptance is not claimed. The lead/QA should add the referenced suite and run it after integration.

## Policies to review during integration

Term visibility and citation require intersection with at least one authorized owner, not every owner of an ambiguous word. Evidence support links do not implicitly cite fact owners. Empty v1 payloads/default metadata remain compatible with the shared dataclasses; missing term metadata cannot provide lexical leak protection. These choices and tests are documented in README.md. If the lead requires different behaviour, provide a failing fixture and an explicit behavioural-contract diff before changing shared code.
