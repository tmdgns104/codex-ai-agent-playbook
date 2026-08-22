---
name: codex-task-router
description: >-
  Use only when the user explicitly asks for Codex capability/model/reasoning/
  topology selection, or when a defined engineering work unit has a material
  capability-allocation decision because of high uncertainty, risk, architecture
  impact, hard verification, or meaningful parallel work. Recommend the minimum
  sufficient supported capability. Do not implement the task.
---

# Codex Task Router

Route one coherent engineering work unit. Return a recommendation only.

Do not activate for routine small edits, ordinary coding, or simple questions unless
routing is explicitly requested. Stronger reasoning is not a substitute for unclear
requirements or architecture.

## 1. Define the Work Unit

Route a coherent outcome, not every helper function.

Include the implementation, investigation, tests, fixtures, and small supporting
refactors needed to complete that outcome.

If the work is not defined well enough to route reliably, return `INVESTIGATE FIRST`
with only the missing routing facts.

## 2. Fast Path

Use `LIGHT` when all are true:

- clear and isolated
- deterministic
- low consequence
- architecture-neutral
- easy to verify

Do not perform broad repository analysis merely to justify a trivial route.

## 3. Safety Floor

For non-trivial work, classify only what changes the decision:

| Dimension | Lower floor | Middle floor | Higher floor |
| --- | --- | --- | --- |
| Complexity | LOW -> LIGHT | MEDIUM -> STANDARD | HIGH/VERY HIGH -> DEEP |
| Uncertainty | LOW -> LIGHT | MEDIUM -> STANDARD | HIGH -> DEEP |
| Risk | LOW -> LIGHT | MEDIUM -> STANDARD | HIGH -> DEEP / CRITICAL -> CRITICAL |
| Architecture impact | NONE -> LIGHT | LIMITED -> STANDARD | SIGNIFICANT -> DEEP |
| Verification difficulty | LOW -> LIGHT | MEDIUM -> STANDARD | HIGH -> DEEP |
| Project criticality | NORMAL -> LIGHT | IMPORTANT -> STANDARD | CRITICAL -> CRITICAL |

Take the strongest applicable minimum.

Breadth, cost sensitivity, user preference, and parallelizability may raise the
recommendation or choose among options at/above the floor; they never lower the
required floor.

Route meanings:

- `LIGHT`: clear, isolated, low-risk, easy verification.
- `STANDARD`: normal engineering inside known architecture.
- `DEEP`: difficult investigation, interacting modules, high uncertainty, or hard verification.
- `CRITICAL`: high-consequence/security/migration/architecture work needing the strongest appropriate single-agent route.
- `PARALLEL COMPLEX`: DEEP/CRITICAL work with genuinely independent workstreams where delegation materially helps.

## 4. Resolve Current Capability

Do not keep a permanent model-name or pricing table in this Skill.

Use, in order:

1. effective runtime/session configuration already observed;
2. current Codex model/reasoning controls exposed by the active product;
3. current official OpenAI Codex documentation when verification is needed.

Never invent a model, reasoning level, Ultra/subagent feature, switch command, price,
or account entitlement.

Choose the least expensive currently supported configuration likely to complete the
work correctly without costly failure, rework, context reconstruction, or excessive
verification.

If the available configuration cannot be confirmed, report `UNKNOWN` rather than
guessing.

## 5. Parallel / Ultra Guard

Default `Ultra: NO`.

Recommend parallel/Ultra-style execution only when all are true:

1. the serial floor is DEEP or CRITICAL;
2. at least two substantial workstreams are meaningfully independent;
3. delegation improves quality, review breadth, or throughput;
4. coordination/token overhead is acceptable;
5. the critical path is not fundamentally sequential.

One hard algorithm, one race condition, or one sequential debugging chain does not
justify parallel execution.

## 6. Stability and Overrides

Re-route only when new evidence materially changes scope, risk, architecture,
verification, or parallel structure.

Respect an explicit supported user configuration unless it violates the Safety Floor.
When a cheaper preference conflicts with the floor, state the conflict instead of
silently downgrading.

Use a Human Gate for material architecture, security, irreversible data, production
migration, major public API, or requirement decisions.

Set `Long-run Workflow: YES` when execution is likely to require multiple substantial
implementation/debug/verification cycles or a resumable session. This is only a
handoff to `codex-long-run`; do not reproduce that Skill's workflow.

## Output

For trivial work:

```text
TASK ROUTING

Route: LIGHT
Confidence: HIGH
Ultra: NO
Action: KEEP / SWITCH NOT WORTHWHILE
Reason: <1-2 sentences>
```

For non-trivial work:

```text
TASK ROUTING

Work Unit: <coherent outcome>
Route: LIGHT / STANDARD / DEEP / CRITICAL / PARALLEL COMPLEX
Complexity: LOW / MEDIUM / HIGH / VERY HIGH
Uncertainty: LOW / MEDIUM / HIGH
Risk: LOW / MEDIUM / HIGH / CRITICAL
Architecture Impact: NONE / LIMITED / SIGNIFICANT
Verification Difficulty: LOW / MEDIUM / HIGH
Parallelizability: LOW / MEDIUM / HIGH
Routing Confidence: LOW / MEDIUM / HIGH
Safety Floor: <route and dominant reason>
Recommended Model: <confirmed current model or UNKNOWN>
Recommended Reasoning: <confirmed current level or UNKNOWN>
Ultra: YES / NO
Current Configuration: <effective setting or UNKNOWN>
Action: KEEP / SWITCH RECOMMENDED / INVESTIGATE FIRST / SWITCH NOT WORTHWHILE
Human Gate: YES / NO - <reason>
Long-run Workflow: YES / NO
Why: <concise total-cost and quality rationale>
```

## Anti-patterns

Do not:

- route by file/line count
- use the strongest or cheapest model for everything
- equate difficulty with parallelism
- replace missing design with more reasoning
- route every microscopic subtask
- repeatedly rediscover the model catalog
- claim a configuration switch or delegation that was not actually applied
- start implementation from this Skill
