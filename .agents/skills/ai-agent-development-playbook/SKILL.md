---
name: ai-agent-development-playbook
description: >
  Use for non-trivial software engineering with Codex: starting a project,
  requirements and architecture design, task decomposition, significant refactors,
  RAG, MCP, LangGraph, tool-using agents, stateful agents, persistence,
  human-in-the-loop, evaluation, or multi-agent systems. Provides a contract-driven
  Human + GPT + Codex workflow with evidence-based verification.
---

# AI Agent Development Playbook

Use this skill to keep Codex implementation inside a human-approved engineering process.

## First Principle

Do not jump from a vague request directly to large implementation.

Use the smallest process that fits the task:

- **Simple local edit:** inspect → edit → test → report.
- **Non-trivial feature:** requirement → architecture impact → task contract → implement → verify → review.
- **Agent system:** additionally define state, nodes, tools/resources, risk, persistence, verification, and execution budgets.

## Before Implementation

1. Inspect the repository and applicable `AGENTS.md`.
2. Read existing project knowledge if present:
   - `PROJECT.md`
   - `REQUIREMENTS.md`
   - `ARCHITECTURE.md`
   - `DECISIONS.md`
3. For agent-runtime work also read:
   - `AGENT_ARCHITECTURE.md`
   - `STATE.md`
   - relevant node/tool/resource contracts
4. Read the current `tasks/TASK-XXX.md` if one exists.
5. Identify:
   - goal
   - allowed/forbidden changes
   - acceptance criteria
   - change budget
   - verification commands
6. If a high-level design change is required, stop and propose it before implementing.

## Implementation

- Prefer the minimum necessary change.
- Preserve approved public interfaces unless the task explicitly changes them.
- Do not add dependencies without explaining the trade-off.
- Write or update tests when behavior changes.
- For bug fixes, add a regression test when practical.
- Do not bypass policy, risk, approval, or idempotency rules.

## Agent Runtime Work

Before implementing an agent, answer:

1. Does this problem actually require an agent?
2. What state must persist?
3. Which node owns each state mutation?
4. What are the graph transitions and termination states?
5. What tools can cause side effects?
6. Which tools are retry-safe and idempotent?
7. Which resources are trusted/untrusted?
8. What is verified after execution?
9. What is the retry/execution budget?
10. When must a human approve or take over?
11. Where are checkpoints stored?
12. What traces/evals prove the agent works?

Use these contracts when needed:
- `references/TASK_TEMPLATE.md`
- `references/STATE_TEMPLATE.md`
- `references/NODE_TEMPLATE.md`
- `references/TOOL_TEMPLATE.md`
- `references/RESOURCE_TEMPLATE.md`
- `references/RESULT_TEMPLATE.md`
- `references/REVIEW_TEMPLATE.md`

For the full methodology, read `references/PLAYBOOK.md`.

Do **not** load the full playbook or every template unless relevant to the current task.

## Completion Evidence

Finish non-trivial work with:

- `STATUS`
- changed files
- implementation summary
- commands actually executed
- test/check results
- acceptance criteria PASS/FAIL
- architecture/invariant status
- unverified items
- known risks
- recommended next step

Never substitute confidence language for evidence.
