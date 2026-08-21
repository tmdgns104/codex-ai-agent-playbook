---
name: human-centered-project-builder
description: >
  Use to start or implement a non-trivial software project end-to-end when the user wants
  disciplined requirements/architecture/task planning plus human-readable, learning-friendly
  code, tests, documentation, and evidence. This is the one-call project-building workflow.
  Do not use for tiny edits or presentation-only work.
---

# Human-Centered Project Builder

This is the convenience workflow for building a project in a way that is both controlled
and understandable to humans.

`Problem → Requirements → Architecture → Task → Readable Implementation → Verification → Explanation`

It does not replace specialized presentation work. Use `guide-ppt-creator` when the user
asks for a PPT/slide deck.

## Core Principle

Human owns the problem, goals, important decisions, architecture approval, and final acceptance.

Codex owns scoped implementation choices, execution, tests, and evidence.

The resulting code must be understandable enough that a developer can trace the system,
not merely accept generated output as a black box.

## Greenfield Project

If project design does not yet exist:

1. Inspect available context.
2. Clarify only decisions that materially change the solution.
3. Define:
   - Problem
   - Goal
   - Users
   - Scope
   - Out of Scope
   - Functional Requirements
   - Non-Functional Requirements
   - Success Criteria
4. Propose architecture.
5. Record major decisions.
6. Create or update:
   - `PROJECT.md`
   - `REQUIREMENTS.md`
   - `ARCHITECTURE.md`
   - `DECISIONS.md`
   - project `AGENTS.md`
7. Decompose work into Task Contracts.
8. Unless the user explicitly asked to implement immediately, stop for architecture approval.

## Existing Project / Current Task

1. Read global/project instructions and approved design docs.
2. Read the current task contract.
3. Inspect the code before editing.
4. State the minimum implementation plan.
5. Implement only the approved scope.
6. Keep code human-readable.
7. Run tests/checks.
8. Review acceptance criteria and readability.
9. Update README/architecture docs when behavior or structure changed.
10. Produce evidence and an explanation handoff.

## Human-Readable Implementation Standard

- prefer descriptive names
- keep one clear responsibility per function/module when practical
- make the main data/control flow explicit
- avoid deep nesting where a simpler flow exists
- avoid speculative abstraction and unnecessary design patterns
- do not hide core learning concepts behind high-level frameworks unless approved
- comments explain why, constraints, assumptions, and workarounds
- keep README's code-reading order accurate

For learning-oriented projects, correctness and understandability come before premature
generalization or micro-optimization.

## Architecture Changes

If implementation requires changing approved high-level architecture:

`DESIGN CHANGE REQUIRED`

Report:
- current design
- blocking problem
- proposed change
- alternatives
- affected interfaces/files
- risks
- migration impact

Wait for approval before applying the architectural change.

## Verification

A task is not done until relevant verification has actually run.

Report:
- commands
- results
- acceptance criteria PASS/FAIL
- readability review
- regressions considered
- `UNVERIFIED` items

Never claim success based only on code inspection when execution was possible but not run.

## Completion Handoff

Explain:

1. What changed.
2. Why this structure was selected.
3. Main execution/data flow.
4. Important files and symbols.
5. How to run.
6. How to test.
7. Recommended code-reading order.
8. Difficult concepts a learner should understand.
9. Risks and deferred work.

## References

- Project input template → `references/BUILD_REQUEST_TEMPLATE_KO.md`
- One-call prompt examples → `references/ONE_CALL_PROMPTS_KO.md`
- Completion handoff → `references/COMPLETION_TEMPLATE.md`
