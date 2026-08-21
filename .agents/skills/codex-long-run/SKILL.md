---
name: codex-long-run
description: >-
  Always use as the orchestration skill for substantial multi-cycle or multi-session
  software engineering work, alongside specialized skills when relevant. Applies
  to repository-level features, difficult bug investigations, migrations,
  refactors, performance experiments, or other work requiring repeated
  implementation, debugging, or verification. Keep one coherent outcome
  resumable, evidence-based, and context-efficient. Do not use for small isolated
  edits, typos, simple questions, short explanations, or directly completed fixes.
---

# Codex Long Run

Use this thin workflow for substantial repository work. Keep project architecture,
technologies, commands, and scope in the repository.

## RESPONSIBILITY BOUNDARY

Follow actual Codex instruction precedence. Treat these as responsibility layers:

- Global instructions define persistent user-wide principles.
- This skill defines long-running execution, verification, checkpoint, and resume.
- Repository instructions define project-specific architecture, tools, commands,
  scope, and restrictions.

Never use this skill to replace repository rules or choose project technology.

## ORIENT WITH MINIMUM SUFFICIENT CONTEXT

Locate the repository root and check which guidance exists. Prefer this order:

1. Repository instructions
2. Current formal project state, if present
3. Current requested outcome
4. Relevant requirements, architecture, and decisions
5. Directly related implementation
6. Callers, interfaces, fixtures, tests, dependencies, and evidence needed for a
   reliable decision

Do not assume particular filenames or a formal state system exists. Use the request
and repository structure when equivalents are absent. Before loading more, ask:

> Would omitting this materially increase the risk of a wrong implementation or
> verification decision?

If yes, read it. If no, do not. Optimize for minimum sufficient context, not the
fewest files; correctness takes priority. Prefer targeted search, relevant sections,
the current diff, and concise summaries. Avoid full-repository scans, all tests,
complete history, old results, or repeated large-file output without a concrete need.

## DURABLE STATE AND STALE STATE GUARD

Prefer repository requirements, architecture, decisions, status, task contracts,
tests, and evidence over conversation history as durable state. Within actual
instruction precedence, use this conceptual order:

`current explicit user instruction -> repository instructions and specifications -> current outcome contract -> current implementation and evidence -> conversation history`

Trust state documents only while they remain consistent with the repository. When
they materially conflict with code, the current diff, tests, recent evidence, or
generated artifacts:

1. Identify the inconsistency.
2. Decide whether it affects the current outcome.
3. Report the stale-state risk.
4. Use a Human Gate if requirements, architecture, scope, or completion is affected.

Resolve minor, unambiguous implementation drift inside the approved outcome without
unnecessary interruption. Never silently reinterpret accepted requirements or
decisions.

## ONE COHERENT OUTCOME AND PROPORTIONAL PLAN

Before significant implementation, establish a compact contract: problem,
requirements, architecture constraints, outcome and exclusions, likely affected
areas, acceptance evidence, and verification strategy.

Allow investigation, debugging, tracing, caller and interface inspection, fixtures,
reproduction tests, dependency investigation, experiments, related tests, and small
supporting refactors needed for that outcome. Do not treat each as a separate task or
approval gate.

Keep planning proportional. Create formal planning artifacts only when the repository
requires them. Record useful out-of-scope findings, but do not implement them or
start the next independent outcome.

## SMALL IMPLEMENTATION LOOP

Use this loop:

`reasonably sized coherent change -> focused check -> inspect -> next coherent change`

Prefer the simplest sufficient change. Avoid large mixed changes and tool-heavy
micro-edits. Preserve unrelated user changes; exclude unrelated cleanup and
speculative abstraction.

## VERIFICATION BUDGET AND FINAL GREEN STATE

Discover verification from repository instructions, task contracts, and existing
configuration. Use the project's existing mechanisms.

During implementation:

- Changed module: run related focused tests or checks.
- Changed interface: run related unit and integration checks.
- Bug fix: run a reproduction or regression check.
- Configuration change: run its relevant validation.
- Performance change: run the relevant repeatable measurement.

Do not run expensive full regression after every coherent change. Before completion,
run the repository-defined final verification appropriate to the outcome and risk.
This may include required tests, lint, type checking, integration, end-to-end, or build.

If final verification fails, investigate, fix, run focused verification, then rerun
enough invalidated final verification to establish a trustworthy green state. Never
impose a fixed run count or let a budget prevent necessary reruns. Report unrelated
or pre-existing failures and the exact verified scope; do not overstate green status.

Do not add a verification framework for convenience. Mark required checks that could
not run as `UNVERIFIED` with the reason.

## EVIDENCE AND MEANINGFUL CHECKPOINTS

Map acceptance claims to evidence such as tests, builds, exit codes, reviewed diffs,
artifacts, integration or reproduction results, benchmarks, or runtime evidence.
Never treat confidence language as proof. Summarize successful logs; store detail
only where the repository already defines it.

Checkpoint only at a substantial milestone, important decision, session pause, or
outcome completion. Use existing conventions to record completed work, findings,
verification, blockers, and next action. Do not checkpoint trivial edits or invent
a heavy state-management system.

## REPOSITORY-BASED RESUME, PAUSE, AND STOP

Resume from:

`repository instructions -> current state -> current outcome -> relevant decisions -> implementation and diff -> latest evidence`

Validate the checkpoint against current code and evidence. Use conversation history
only as supplementary context.

For an incomplete outcome that must pause, preserve or report: completed so far,
findings, remaining work, last verification, next action, and blockers. Use a concise
handoff when no repository mechanism exists.

For a completed outcome, report: result, acceptance status, verification, evidence,
remaining risks, possible next task, and any human decision. Then stop; do not begin
another independent outcome automatically.

## HUMAN GATE

Pause for high-impact choices: architecture change, major dependency addition or
replacement, requirements conflict, potential data loss, security impact, material
public-interface change, material cost or operational change, or substantial
long-term consequences. Follow stricter repository gates.

Proceed autonomously with routine supporting work inside the approved outcome.

## ANTI-PATTERNS

Do not:

- scan broadly without reason or minimize files at the expense of correctness
- rerun expensive full regression without need or block necessary final reruns
- rely on conversation alone or blindly trust stale state documentation
- silently change accepted architecture, requirements, or decisions
- mix unrelated cleanup into the outcome or start the next outcome automatically
- claim completion without evidence or dump large successful logs into context
- checkpoint every trivial change or invent a heavy project-state framework
- add frameworks for convenience or request approval for every supporting subtask
