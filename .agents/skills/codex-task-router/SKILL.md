---
name: codex-task-router
description: >-
  Use to route a sufficiently defined Codex software-engineering work unit when
  the user asks to choose or compare a Codex model, reasoning level, or
  Ultra/subagent topology, or when a workflow reaches an explicit capability-
  allocation decision. Recommends the minimum sufficient current capability;
  it does not implement the task. Do not activate merely because engineering
  work was requested, or for small edits and simple questions unless routing
  is explicitly requested.
---

# Codex Task Router

## Responsibility

Route one defined implementation or investigation unit. Return a recommendation
only; do not implement, edit files, or execute the routed work.

Routing follows problem, requirements, architecture, decomposition, and scope.
If those are too vague for a reliable decision, return `INVESTIGATE FIRST` and
identify only the missing routing facts. Stronger reasoning is not a substitute
for design.

Keep these boundaries:

- Project instructions own architecture, scope, Human Gates, and verification.
- This skill allocates Codex capability for the current work unit; it does not
  design a general routing policy, model portfolio, evaluation, or fallback
  system.
- `codex-long-run` governs efficient long execution. Set `Long-run Workflow` and
  hand off; do not reproduce its context, checkpoint, or verification workflow.

## Routing Workflow

1. Define one coherent routing unit. Include necessary implementation, error
   handling, fixtures, tests, experiments, and small supporting refactors under
   one decision. Do not route every microscopic subtask.
2. Apply the trivial fast path before repository exploration. A task is trivial
   only when it is clear, isolated, deterministic, low-risk, architecture-neutral,
   and easy to verify. Hidden consequence severity disqualifies it.
3. For non-trivial work, classify the dimensions below. Use task interactions and
   consequences, not file or line counts.
4. Compute the serial Safety Floor, then select the least expensive currently
   supported configuration likely to finish correctly without costly failure or
   rework.
5. Evaluate `PARALLEL COMPLEX` only after the serial route. Compare current and
   recommended configurations, emit the compact result, and stop.

## Dimensions

| Dimension | Values | Judge from |
| --- | --- | --- |
| Complexity | LOW / MEDIUM / HIGH / VERY HIGH | algorithms, state, interactions, coupling |
| Uncertainty | LOW / MEDIUM / HIGH | clarity of scope, root cause, dependencies, approach |
| Risk | LOW / MEDIUM / HIGH / CRITICAL | consequence of error, irreversibility, security, data |
| Project Criticality | NORMAL / IMPORTANT / CRITICAL | actual delivery and operational context |
| Architecture Impact | NONE / LIMITED / SIGNIFICANT | boundaries, responsibilities, contracts, data flow |
| Breadth | NARROW / MODERATE / BROAD | logical subsystems and shared interfaces/state |
| Verification Difficulty | LOW / MEDIUM / HIGH | determinism, observability, environment, compatibility |
| Parallelizability | LOW / MEDIUM / HIGH | independent workstreams, not raw difficulty |
| Routing Confidence | LOW / MEDIUM / HIGH | completeness and stability of routing evidence |
| Cost Sensitivity | EFFICIENCY / BALANCED / QUALITY | explicit user priority and failure/rework cost |

Small code can have `CRITICAL` risk. Production context alone is not automatically
critical; use the stated consequences. Low routing confidence makes the route
provisional, not automatically Ultra.

## Serial Route and Safety Floor

Use logical routes so model names can evolve. Map each dimension to a minimum
serial route and take the strongest applicable minimum:

| Source | LIGHT | STANDARD | DEEP | CRITICAL |
| --- | --- | --- | --- | --- |
| Complexity | LOW | MEDIUM | HIGH | VERY HIGH |
| Uncertainty | LOW | MEDIUM | HIGH | - |
| Risk | LOW | MEDIUM | HIGH | CRITICAL |
| Project Criticality | NORMAL | IMPORTANT | - | CRITICAL |
| Architecture Impact | NONE | LIMITED | SIGNIFICANT | - |
| Verification Difficulty | LOW | MEDIUM | HIGH | - |

Broad, tightly coupled work may raise this result. Breadth, parallelizability,
confidence, cost sensitivity, and user preference never lower a required floor.
A significant architecture decision also requires a Human Gate and can rise to
`CRITICAL` when consequence, uncertainty, or verification warrants it.

Set `Safety Floor Applied: YES` when consequence, criticality, architecture, or
verification raises the route above the complexity/uncertainty baseline or
prevents a requested downgrade. State the dominant reason.

Route meanings:

- `LIGHT`: clear, isolated, low-risk, easy to verify.
- `STANDARD`: ordinary engineering in known architecture with normal coupling.
- `DEEP`: difficult investigation or interacting modules with high uncertainty.
- `CRITICAL`: strongest appropriate single-agent work for high consequence,
  architecture, migration, security, concurrency, or hard verification.
- `PARALLEL COMPLEX`: a DEEP/CRITICAL floor plus justified parallel topology;
  it is not a stronger ordinal Safety Floor.

## Resolve Current Codex Capability

Use already-observed runtime metadata first. When validity matters, query the
current Codex model catalog or official OpenAI documentation; do not rely on old
names, guessed prices, or a generic config schema when the model-specific catalog
is available. Do not repeat capability discovery for every supporting subtask.

As verified for the current Codex catalog, use this baseline only while each
combination remains supported:

| Route | Default recommendation |
| --- | --- |
| LIGHT | `gpt-5.6-luna` / `low` |
| STANDARD | `gpt-5.6-terra` / `medium` |
| DEEP | `gpt-5.6-sol` / `high` |
| CRITICAL | `gpt-5.6-sol` / `xhigh`; use `max` for the hardest quality-first single-agent work |
| PARALLEL COMPLEX | `gpt-5.6-sol` / `ultra`; use `gpt-5.6-terra` / `ultra` only when its capability is sufficient and efficiency matters |

Availability and account eligibility still require confirmation. If no adequate
supported combination can be confirmed, do not invent one: report `UNKNOWN`, the
Safety Floor, and a Human Gate or `INVESTIGATE FIRST` as appropriate.

## Ultra Guard

Default `Ultra: NO`. Select `PARALLEL COMPLEX` and recommend `ultra` only when all
are true:

1. The work is genuinely large or complex.
2. At least two meaningful workstreams are substantially independent.
3. Delegation materially improves quality, review breadth, or throughput.
4. Coordination and token overhead are acceptable.
5. The critical path is not fundamentally sequential.

One hard algorithm, one narrow race, or a sequential debugging chain uses strong
single-agent reasoning, not Ultra. If Ultra is unavailable, keep the serial Safety
Floor and report the limitation; do not pretend delegation occurred.

## Stability, Override, and Gates

Re-route only when new evidence materially changes scope, risk, architecture,
coupling, verification, or phase. Escalate when the Safety Floor rises. De-escalate
only when remaining work is durably simpler, risk is clarified, verification is
straightforward, and the lower route is likely to remain sufficient. Do not
oscillate after minor evidence or split one coherent unit merely to save usage.

Respect a supported explicit user configuration. An efficiency preference chooses
the least expensive option at or above the floor; balanced uses the baseline;
quality may raise it. Never hide a conflict between a cheaper request and critical
safety. Flag a Human Gate for material architecture, security, irreversible data,
production migration, major public API, or requirement decisions, not for ordinary
supporting details.

Compare total expected cost: capability usage plus failure, rework, verification,
context reconstruction, switching, and delegation overhead, not initial model cost
alone.

When current configuration is observable, compare the effective session setting,
not merely a default config file. Otherwise use `Current Configuration: UNKNOWN`.
Use only a switching surface confirmed in the active environment, such as the
interactive model/reasoning controls, CLI `--model` plus configuration/profile
overrides, or explicit subagent overrides. Never claim the parent session or a
subagent was switched unless it actually was.

Actions:

- `KEEP`: effective configuration matches the recommendation.
- `SWITCH RECOMMENDED`: a material mismatch exists, or an unknown configuration
  should be explicitly established and the switching cost is worthwhile.
- `INVESTIGATE FIRST`: missing facts prevent reliable routing.
- `SWITCH NOT WORTHWHILE`: trivial work where switching overhead exceeds benefit.

Set `Long-run Workflow: YES` only when execution likely needs multiple substantial
steps, repeated debug/verification cycles, repository-scale work, or another
session. This is a handoff flag, not permission to begin implementation.

## Output

For a clearly trivial unit, return only:

```text
TASK ROUTING

Route: LIGHT
Confidence: HIGH
Ultra: NO
Action: KEEP / SWITCH NOT WORTHWHILE
Reason: <one or two sentences>
```

For non-trivial work, keep every reason concise:

```text
TASK ROUTING

Work Unit: <defined coherent unit>
Route: LIGHT / STANDARD / DEEP / CRITICAL / PARALLEL COMPLEX
Complexity: LOW / MEDIUM / HIGH / VERY HIGH
Uncertainty: LOW / MEDIUM / HIGH
Risk: LOW / MEDIUM / HIGH / CRITICAL
Project Criticality: NORMAL / IMPORTANT / CRITICAL
Architecture Impact: NONE / LIMITED / SIGNIFICANT
Breadth: NARROW / MODERATE / BROAD
Verification Difficulty: LOW / MEDIUM / HIGH
Parallelizability: LOW / MEDIUM / HIGH
Routing Confidence: LOW / MEDIUM / HIGH
Cost Sensitivity: EFFICIENCY / BALANCED / QUALITY
Safety Floor Applied: YES / NO
Reason: <dominant floor reason>
User Override: NONE / EFFICIENCY / BALANCED / QUALITY / EXPLICIT
Effect: <effect without hiding safety conflicts>
Recommended Model: <confirmed current model or UNKNOWN>
Recommended Reasoning: <confirmed current level or UNKNOWN>
Ultra: YES / NO
Current Configuration: <effective model/reasoning or UNKNOWN>
Configuration Match: YES / NO / UNKNOWN
Action: KEEP / SWITCH RECOMMENDED / INVESTIGATE FIRST
Why: <concise total-cost and quality rationale>
Human Gate: YES / NO
Reason: <gate reason or none>
Long-run Workflow: YES / NO
```

## Anti-patterns

Do not route by file count, use the strongest or cheapest model for everything,
equate difficulty with Ultra, ignore small high-risk changes, replace design with
reasoning, run broad repository analysis for a trivial route, route every helper,
oscillate on noise, silently defeat a Safety Floor, or start implementation.
