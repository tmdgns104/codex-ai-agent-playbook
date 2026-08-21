# Repository Instructions

## Required Context

Before non-trivial implementation, inspect the documents that actually exist:

- `PROJECT.md`
- `REQUIREMENTS.md`
- `ARCHITECTURE.md`
- `DECISIONS.md`
- current file under `tasks/`

For agent-runtime changes also inspect:

- `AGENT_ARCHITECTURE.md`
- `STATE.md`
- relevant files under `contracts/`
- `docs/PERSISTENCE.md`
- `docs/SECURITY.md`

## Workflow

1. Understand the current task.
2. Inspect the existing code before editing.
3. Stay within allowed changes and change budget.
4. Propose high-level design changes before applying them.
5. Implement the minimum necessary change.
6. Run relevant tests/checks.
7. Review the diff.
8. Report evidence and unverified items.

## Architecture

Architecture-specific invariants belong in `docs/INVARIANTS.md`.

Do not invent architecture rules that are not approved.

## Agent Runtime

For tool-using/stateful agents:
- respect state mutation ownership,
- respect node responsibilities,
- respect tool risk/approval/idempotency contracts,
- respect retry/execution budgets,
- preserve checkpoint/recovery semantics.

## Completion

Do not report PASS without verification evidence.
If a check was not run, mark it `UNVERIFIED`.
