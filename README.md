# Codex AI Agent Playbook

A context-efficient **Codex engineering harness** built around repository truth, progressive-disclosure Skills, evidence-based verification, and safe global installation.

> Current development branch: **V8 Candidate — `v8-harness-core`**

한국어 상세 가이드: [README_KO.md](README_KO.md)

## What it optimizes

```text
less permanent context
+ fewer unnecessary Skills
+ verification proportional to risk
+ deterministic quality checks
+ repository-based evidence
```

The project does **not** try to replace Codex with another agent framework. Patterns from popular harnesses such as Everything Claude Code and Claude Code are translated only when they improve Codex operation without adding unnecessary runtime layers.

## V8 flow

```text
User Request
  -> minimum Skill selection
  -> MINIMAL / STANDARD / STRICT profile
  -> Repository Context
  -> Implementation
  -> Repository Verification
  -> Deterministic Quality Gate
  -> Evidence
```

## Structure

```text
.codex/AGENTS.md
  short global working agreement

.agents/skills/
  ai-agent-development-playbook/
  codex-long-run/
  codex-task-router/
  codex-skill-router/
  guide-ppt-creator/
  human-centered-project-builder/
  human-readable-code/

harness/
  profiles/
  quality/quality_gate.py
  security/harness_audit.py

install.ps1 / install.sh
verify-install.ps1
uninstall.ps1 / uninstall.sh
```

## V8 P0 additions

### Context-aware Skill Router

`codex-skill-router` is used only when the minimum useful Skill set is materially ambiguous. Obvious or trivial work bypasses the router.

### Risk-based profiles

- `MINIMAL` — isolated, low-risk, easy to verify
- `STANDARD` — normal non-trivial engineering
- `STRICT` — security, permissions, migrations, deployment, destructive behavior, significant architecture/public-contract changes, or other high-consequence work

### Deterministic Quality Gate

```powershell
python "$HOME\.codex\playbook-harness\quality\quality_gate.py" --repo . --profile standard
```

Checks Git diff hygiene, unresolved conflicts, conflict markers, suspicious secret material when appropriate, and optionally explicit repository verification commands.

A STRICT gate without required execution evidence returns `UNVERIFIED`, not a false PASS.

### Harness Audit

```powershell
python .\harness\security\harness_audit.py --root .
```

Audits global-context size, Skill metadata, duplicate/discovery hazards, profile JSON, Python syntax, MANIFEST coverage, and reusable-content hygiene.

## Windows candidate install

From CMD:

```cmd
git fetch origin
git switch v8-harness-core
git pull origin v8-harness-core
powershell -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

From PowerShell:

```powershell
git fetch origin
git switch v8-harness-core
git pull origin v8-harness-core
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

Installed managed content:

```text
~/.codex/AGENTS.md
~/.agents/skills/<managed-skill>/
~/.codex/playbook-harness/
```

Backups are stored outside Skill discovery:

```text
~/.codex/playbook-backups/<timestamp>/
```

Unchanged reinstallations are designed to be no-ops.

## Design rules

- Repository state is the durable Source of Truth.
- Work on one coherent outcome at a time.
- Permanent global context must stay small.
- Load detailed Skills only when they materially help.
- A stronger model never substitutes for stronger verification.
- Agent confidence is not evidence.
- Do not automatically begin the next independent task.
- Do not add heavy agent frameworks to the core without measured benefit.

## Documentation

- [Korean Guide](README_KO.md)
- [V8 Changes](V8_CHANGES_KO.md)
- [V7 Changes](V7_CHANGES_KO.md)
- [Quick Start](docs/QUICKSTART.md)
- [How It Works](docs/HOW_IT_WORKS.md)
- [Skills](docs/SKILLS.md)
- [Development](docs/DEVELOPMENT.md)
