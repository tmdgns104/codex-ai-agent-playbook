---
name: codex-long-run
description: >-
  Use for substantial multi-cycle or multi-session repository work that needs
  repeated implementation, debugging, verification, checkpoint, or resume.
  Keep one coherent outcome evidence-based and context-efficient. Do not use for
  small isolated edits, simple questions, or directly completed fixes.
---

# Codex Long Run

This Skill owns long-running execution discipline only.
Project architecture, commands, scope, and technology stay in repository guidance.

## 1. Orient with Minimum Sufficient Context

Read in this order when present:

1. repository instructions
2. current status/task/outcome
3. relevant requirements, architecture, and decisions
4. directly related implementation
5. callers/interfaces/tests/evidence needed for the next reliable decision

Before loading more context, ask whether omitting it would materially raise the risk of
a wrong implementation or verification decision.

Prefer targeted search, relevant sections, current diffs, and concise summaries.
Avoid full-repository scans, repeated large-file reads, old logs, broad history, and
full test output without a concrete need.

Correctness takes priority over token reduction.

## 2. Establish One Outcome Contract

Before significant implementation, establish a compact working contract:

- desired outcome
- relevant requirements
- architecture/safety constraints
- exclusions
- likely affected areas
- acceptance evidence
- verification strategy

Investigation, reproduction, fixtures, tests, dependency tracing, and small supporting
refactors may stay inside the same outcome when they are necessary to complete it.

Do not start the next independent outcome automatically.

## 3. Use Durable State

Prefer repository artifacts over conversation history for resumable state.

When a status/task document conflicts materially with current code, diff, tests, or
recent evidence:

1. identify the inconsistency;
2. determine whether it affects the current outcome;
3. report stale-state risk;
4. use a Human Gate if requirements, architecture, scope, or completion meaning changes.

Resolve minor implementation drift autonomously when the approved outcome is unchanged.

## 4. Small Implementation Loop

Use:

`coherent change -> focused check -> inspect -> next coherent change`

Keep changes large enough to be meaningful and small enough to diagnose.

- preserve unrelated user changes
- avoid unrelated cleanup
- prefer the simplest sufficient implementation
- avoid speculative abstractions
- summarize successful logs instead of repeatedly injecting them

## 5. Verification Budget

Discover verification from repository instructions, task contracts, and existing
configuration.

During implementation:

- changed behavior -> focused related tests/checks
- changed interface -> related unit/integration checks
- bug fix -> reproduction/regression check when practical
- config change -> relevant validation
- performance change -> repeatable representative measurement

Do not run expensive full regression after every edit.

Before completion, run the repository-defined final verification appropriate to the
outcome and risk. If it fails, fix the cause, rerun focused checks, then rerun enough
invalidated final verification to establish trustworthy evidence.

Report unrelated/pre-existing failures separately.
Mark required checks that could not run as `UNVERIFIED`.

## 6. Evidence and Checkpoints

Map acceptance claims to evidence: tests, builds, exit codes, diffs, artifacts,
integration results, benchmarks, or runtime observations.

Checkpoint only at:

- a substantial milestone
- an important decision
- a session pause
- outcome completion

Use an existing repository state mechanism when available.
Do not invent a heavy checkpoint system merely because this Skill is active.

A useful checkpoint contains only:

- completed work
- key findings/decisions
- latest verification
- remaining work
- blocker/risk
- next action

## 7. Resume

Resume from:

`repository instructions -> current state/task -> relevant decisions -> current diff/code -> latest evidence`

Validate stale checkpoints against the current repository before trusting them.
Use chat history only as supplemental context.

## 8. Human Gate

Pause for material choices involving:

- architecture or requirements
- major dependency replacement
- security/permissions
- irreversible data loss
- production migration/deployment
- major public-interface compatibility
- significant cost/operational consequences

Proceed autonomously with routine supporting work inside approved scope.

## 9. Completion

For a completed outcome, report concisely:

- result/status
- changed files/artifacts
- acceptance PASS/FAIL
- verification actually run
- `UNVERIFIED` items
- remaining risks
- next independent task, if any

Then stop.

## Anti-patterns

Do not:

- scan broadly without a reason
- rerun expensive full regression unnecessarily
- minimize context at the expense of correctness
- rely on conversation as the only durable state
- blindly trust stale status documents
- mix unrelated cleanup into the outcome
- dump large successful logs into context
- checkpoint trivial edits
- request approval for every supporting subtask
- claim completion without evidence
