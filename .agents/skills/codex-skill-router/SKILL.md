---
name: codex-skill-router
description: >-
  Use when a Codex engineering task is non-trivial and the minimum useful Skill set
  is ambiguous, or when the user explicitly asks which Skills/workflow profile to
  use. Recommend the smallest relevant Skill set and a MINIMAL/STANDARD/STRICT
  harness profile. Do not implement the task and do not activate for obvious single-
  skill or trivial work.
---

# Codex Skill Router

## Responsibility

Select only the Skills that materially improve the current work unit and recommend
one harness profile. Return a recommendation only; do not edit files or execute the
routed task.

The goal is progressive disclosure: keep permanent context small and load detailed
workflows only when they are needed.

## Fast Path

Do not use this router when the answer is obvious.

Examples:

- typo or tiny local edit -> no Skill required
- explicit readability/refactor request -> `human-readable-code`
- explicit technical guide PPTX -> `guide-ppt-creator`
- explicit model/reasoning/topology choice -> `codex-task-router`

For ambiguous non-trivial work, classify the task and select the smallest set below.

## Skill Selection

| Task trait | Skill |
| --- | --- |
| requirements, architecture, significant feature/refactor, agent/RAG/tool contracts, evidence design | `ai-agent-development-playbook` |
| readability, maintainability, naming, explanation, learning-oriented code | `human-readable-code` |
| whole project build from request through implementation/verification | `human-centered-project-builder` |
| substantial multi-cycle, resumable, repository-scale execution | `codex-long-run` |
| capability/model/reasoning/subagent-topology decision | `codex-task-router` |
| technical/guide slide deck workflow | `guide-ppt-creator` |

Rules:

1. Start with zero Skills and add only clear matches.
2. Prefer one Skill when one Skill fully owns the task.
3. Add `codex-long-run` only for genuinely long or multi-cycle execution.
4. Add `codex-task-router` only when capability allocation materially matters.
5. Do not pair `human-centered-project-builder` with every underlying Skill by
   default; add another Skill only when the builder does not sufficiently cover the
   specialized concern.
6. Repository instructions always outrank this routing recommendation.

## Harness Profile

Recommend the lowest profile that still matches consequence and verification need.

### MINIMAL

Use for clear, isolated, low-risk changes with easy verification.

Expected gate:
- Git diff hygiene
- unresolved-conflict check
- focused verification appropriate to the edit

### STANDARD

Default for ordinary non-trivial engineering in an approved architecture.

Expected gate:
- MINIMAL checks
- changed-file and conflict-marker inspection
- suspicious-secret scan on changed content
- repository-defined verification evidence

### STRICT

Use when errors have high consequence or verification is difficult, including
security/permission changes, migrations, production/deployment behavior, significant
architecture/public-contract changes, destructive operations, or other high-risk
work.

Expected gate:
- STANDARD checks
- stronger secret handling
- explicit verification command/evidence
- applicable Human Gate before high-impact side effects

A stronger model is not a substitute for a stronger verification profile.

## Output

```text
SKILL ROUTING

Work Unit: <one coherent outcome>
Profile: MINIMAL / STANDARD / STRICT
Skills:
- <skill or NONE>
Reason: <why this is the minimum sufficient set>
Long-run: YES / NO
Capability Routing: YES / NO
Human Gate: YES / NO
Reason: <gate reason or none>
```

## Anti-patterns

Do not load every Skill, route microscopic subtasks independently, add a Skill only
because it exists, use `codex-long-run` for short edits, use `codex-task-router` for
routine choices, or escalate the harness profile merely because a task is large.
Risk and verification difficulty matter more than raw file count.
