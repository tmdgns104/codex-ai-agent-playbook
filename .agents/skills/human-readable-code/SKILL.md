---
name: human-readable-code
description: >
  Use when writing, refactoring, reviewing, or explaining code where human readability,
  learning value, maintainability, clear project structure, explicit data flow, naming,
  comments, README guidance, or beginner-friendly code matters. Prefer understandable
  code over clever compression while preserving correctness and appropriate performance.
---

# Human Readable Code

Your job is not merely to make code run. Make the codebase understandable to a human
developer who did not write it.

## Priority

Unless the project explicitly requires otherwise, optimize in this order:

1. Correctness
2. Understandability
3. Testability
4. Maintainability
5. Performance
6. Cleverness / brevity

Do not intentionally make code slow or naive when performance is a real requirement.
Instead, make performance-sensitive code explicit and document why the complexity exists.

## Core Rules

- Prefer clear code over clever or overly compact code.
- Use descriptive variable, function, class, file, and module names.
- Keep the main execution/data flow traceable.
- Give each function or class a clear responsibility.
- Prefer early returns over deep nesting when appropriate.
- Avoid hidden side effects.
- Avoid unnecessary abstraction, indirection, factories, managers, adapters, registries,
  and design patterns unless they solve a current concrete problem.
- Do not generalize for hypothetical future requirements.
- Keep public interfaces small and predictable.
- Prefer explicit intermediate variables when they make transformations easier to follow.
- Avoid dense one-liners when a few clear statements communicate intent better.

## Comments and Docstrings

Comments should explain WHY, assumptions, constraints, tradeoffs, invariants,
non-obvious behavior, or workarounds.

Do not add comments that simply narrate obvious syntax.

For important public functions/classes, document:
- responsibility
- inputs
- outputs
- important side effects
- exceptions or failure behavior when relevant

Read `references/COMMENTS_AND_DOCSTRINGS.md` when documentation style matters.

## Project Structure

The directory tree should reflect the system's mental model.

A developer should be able to infer major responsibilities before opening every file.

For non-trivial projects maintain a README that includes:
- project purpose
- architecture overview
- data/control flow
- directory structure
- entry point
- important modules
- how to run
- how to test
- recommended code-reading order

Use `references/PROJECT_STRUCTURE_GUIDE.md` and `references/README_TEMPLATE.md`.

## Learning-Oriented Projects

When the project is partly educational:

- Keep the underlying mechanism visible.
- Do not hide core learning concepts behind a high-level framework unless approved.
- Introduce one abstraction at a time.
- Prefer direct implementations before generalized plugin/factory architectures.
- Explain unfamiliar concepts after implementation.
- Preserve a readable mapping between architecture diagrams and code modules.

## Before Editing

1. Inspect the repository.
2. Identify the main entry point and execution flow.
3. Identify project conventions.
4. Determine whether the requested change can remain locally understandable.
5. Avoid broad readability refactors outside the task scope unless explicitly requested.

## After Editing

Review changed code with `references/READABILITY_REVIEW_CHECKLIST.md`.

When useful, run:

```text
python <skill-path>/scripts/readability_audit.py <python-file-or-directory>
```

The audit is heuristic evidence, not a substitute for human review.

## Completion Report

Report:

1. What changed.
2. Why the structure was chosen.
3. Main execution/data flow.
4. Important files/functions/classes.
5. Tests/checks executed.
6. Readability issues intentionally left in place and why.
7. Anything a beginner may still find difficult.
8. `UNVERIFIED` items.

Use `references/EXPLANATION_REPORT_TEMPLATE.md` when a structured handoff is useful.

## Progressive Disclosure

- Naming → `references/NAMING_GUIDE.md`
- Comments/docstrings → `references/COMMENTS_AND_DOCSTRINGS.md`
- Project/module layout → `references/PROJECT_STRUCTURE_GUIDE.md`
- README → `references/README_TEMPLATE.md`
- Review → `references/READABILITY_REVIEW_CHECKLIST.md`
- Reusable prompts → `references/STARTER_PROMPTS_KO.md`
