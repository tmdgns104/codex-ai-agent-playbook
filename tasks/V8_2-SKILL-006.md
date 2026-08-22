# V8.2-SKILL-006 - Self-Managing Lifecycle Integration

상태: **IMPLEMENTED - WINDOWS VERIFICATION PENDING**

선행 조건:

- V8_2-SKILL-005 — COMPLETE - VERIFIED

## 목적

Governance, Creator, Evolver, Curator를 기존 V8.1 Router/Activation/Launcher와 연결해 Self-Managing Skill Lifecycle을 실제 Windows workflow에서 검증합니다.

## 최종 흐름

```text
User Task
  |
  v
V8.1 Metadata Router
  |
  +--> Skill found --> Gate --> Activation --> Codex --> post-task Event
  |
  +--> No suitable Skill --> Codex --> Gap Event only

Maintenance Entry Point
  |
  +--> gaps / create
  +--> evolve
  +--> curate
  +--> proposals / validate / promote
           |
           v
      Candidate Audit
           |
           v
    Protected Regression
           |
           v
   Promotion / Human Gate
           |
           v
   Capability Library
```

## 구현 내용

### 1. Normal Path는 Lightweight 유지

`harness/activation/playbook_launch.py`는 기존 Router / Gate / Activation / Codex 실행 흐름을 유지합니다.

Self-Managing 계층은 정상 task 시작 시 import/실행하지 않습니다.

Task 종료 후에만 lazy-load하여 privacy-safe Event 1건을 best-effort 기록합니다.

```text
selected Skill + exit 0  -> verified_usage
selected Skill + exit !=0 -> verification_failure
no Skill                  -> capability_gap
--user-correction         -> user_correction
```

저장되는 것은:

- task fingerprint
- selected Skill ids
- verification outcome
- explicit correction marker
- timestamp / issue code

raw task text는 저장하지 않습니다.

Event 저장 실패는 Codex exit/result를 변경하지 않습니다.

### 2. Event State 위치

Event/Proposal/Candidate runtime state는 target Git repository가 아니라 **catalog root의 `.playbook-state`**에 저장합니다.

Repository 개발 환경:

```text
<playbook-repo>/.playbook-state
```

Global installed 환경:

```text
%USERPROFILE%\.codex\.playbook-state
```

따라서 임의 target Git repository에 Self-Managing telemetry 때문에 untracked 파일을 만들지 않습니다.

### 3. Maintenance CLI

추가:

```text
harness/skills/manage.py
```

지원 command:

```cmd
python harness\skills\manage.py audit
python harness\skills\manage.py gaps
python harness\skills\manage.py proposals
python harness\skills\manage.py create --spec <json>
python harness\skills\manage.py evolve --spec <json> [--issue-code <code>]
python harness\skills\manage.py validate <proposal-id>
python harness\skills\manage.py promote <proposal-id>
python harness\skills\manage.py curate
python harness\skills\manage.py benchmark
```

CLI는 LLM provider를 요구하지 않습니다.

Creator/Evolver의 semantic spec 작성은 reviewed input으로 받고, deterministic code는 eligibility / candidate / audit / regression / promotion만 담당합니다.

### 4. Lifecycle Integration Helper

추가:

```text
harness/skills/lifecycle_integration.py
```

담당:

- post-task Event build/record
- Candidate discovery
- Candidate validation
- protected Router regression
- low-risk promotion
- installed/repository catalog layout resolution
- scaling size contract

### 5. Promotion 계약

`modify` Candidate는 기존 Evolver promotion wrapper를 그대로 재사용합니다.

따라서:

- ACTIVE base hash
- one-writer lock
- protected regression
- Candidate metadata 제거
- atomic replacement
- promotion history

계약을 유지합니다.

Curator의 low-risk package-only:

```text
compress
extract-reference
```

만 generic atomic package promotion 대상입니다.

다음은 자동 promotion하지 않습니다.

```text
create
split
merge
archive
trigger-expand
permission-expand
registry trigger/permission delta
```

### 6. Human Gate

다음은 approval 전:

```text
HUMAN_GATE_REQUIRED
```

- permission expansion
- split
- merge
- archive
- trigger expansion

approval 후에도 V8.2에서 구조/registry mutation을 자동 수행하지 않는 항목은 `MANUAL_ONLY`입니다.

즉 Human Gate approval 자체가 silent mutation 권한이 되지 않습니다.

### 7. Installed Protected Regression

Repository Source of Truth:

```text
evaluation/self-managing/protected-routing.json
```

Global install 시 별도 installer branch를 추가하지 않고 기존 capability-library 설치 경로에 snapshot을 포함합니다.

```text
capability-library/governance/protected-routing.json
```

`load_protected_regressions()`는:

1. Repository evaluation fixture 우선
2. installed governance snapshot fallback
3. 둘 다 있으면 JSON object equality 검증

을 수행합니다.

따라서 기존 install/reinstall/uninstall 구조를 변경하지 않고 installed maintenance control plane을 사용할 수 있습니다.

### 8. Scaling Check

`manage.py benchmark`는 deterministic metadata Router를 synthetic registry로 측정합니다.

```text
10
50
100
500
1000
```

Skill metadata에서 runtime을 기록하고 semantic/embedding Router를 자동 추가하지 않습니다.

### 9. Integration Tests

추가:

```text
harness/skills/test_lifecycle_integration.py
harness/skills/test_lifecycle_control_plane.py
```

검증 범위:

- Event privacy / best-effort
- Gap Event only / no auto-create
- target repo no telemetry mutation
- Creator repeated-gap gate
- Evolver Candidate integration
- Curator package Candidate validation
- failed regression -> ACTIVE unchanged
- low-risk atomic promotion + history
- permission/split/merge/archive Human Gate
- installed protected snapshot fallback
- normal Launcher has no Creator/Evolver/Curator direct invocation
- 10/50/100/500/1000 scaling

## 변경 파일

```text
capability-library/governance/protected-routing.json
harness/activation/playbook_launch.py
harness/skills/promotion.py
harness/skills/lifecycle_integration.py
harness/skills/manage.py
harness/skills/test_lifecycle_integration.py
harness/skills/test_lifecycle_control_plane.py
MANIFEST.txt
tasks/V8_2-SKILL-006.md
```

Global `.codex/AGENTS.md`, Router scoring, ACTIVE registry, Optional Skill content는 변경하지 않았습니다.

## Windows Verification

먼저 SKILL-006 focused tests:

```cmd
python harness\skills\test_lifecycle_integration.py
python harness\skills\test_lifecycle_control_plane.py
```

그 다음 Self-Managing regressions:

```cmd
python harness\skills\test_curator.py
python harness\skills\test_evolver.py
python harness\skills\test_creator.py
python harness\skills\test_governance.py
python harness\skills\test_events.py
python harness\skills\test_queue.py
python harness\quality\test_skill_audit.py
python harness\quality\skill_audit.py --root .
```

Router / Activation regressions:

```cmd
python harness\router\test_capability_router.py
python harness\activation\test_capability_manager.py
python harness\activation\test_skill_materializer.py
python harness\activation\test_discovery_bridge.py
python harness\activation\test_playbook_launch.py
python harness\activation\test_installed_launcher.py
```

Maintenance CLI / scaling:

```cmd
python harness\skills\manage.py audit
python harness\skills\manage.py gaps
python harness\skills\manage.py proposals
python harness\skills\manage.py curate
python harness\skills\manage.py benchmark --repeats 20
```

Global install E2E:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
powershell -ExecutionPolicy Bypass -File .\verify-install.ps1
powershell -ExecutionPolicy Bypass -File .\install.ps1
powershell -ExecutionPolicy Bypass -File .\verify-install.ps1
```

Installed maintenance smoke:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" benchmark --repeats 2
```

Installed arbitrary Git repository dry-run:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root <another-git-repo> --task "JWT 인증 오류를 수정하고 regression test를 실행" --dry-run
```

Final:

```cmd
python harness\security\harness_audit.py --root .
python harness\quality\quality_gate.py --repo . --profile strict --verify "python harness\security\harness_audit.py --root ."
echo %ERRORLEVEL%
git status --short
```

## Acceptance Criteria

1. Existing V8.1 normal task flow remains backward-compatible
2. Global AGENTS does not meaningfully grow for self-management
3. Normal path does not invoke Creator/Evolver/Curator automatically on every task
4. Gap Event integration works
5. Creator Candidate integration works
6. Evolver Proposal integration works
7. Curator Proposal integration works
8. Failed validation preserves ACTIVE hash/content
9. Low-risk validated promotion atomic PASS
10. Human Gate scenarios block auto promotion
11. protected routing regressions PASS
12. all V8.1 router tests PASS
13. all V8.1 activation/materializer/discovery/launcher tests PASS
14. new governance/creator/evolver/curator tests PASS
15. Skill Audit PASS/WARN-only with no FAIL
16. Harness Audit PASS
17. STRICT Quality Gate PASS
18. install/verify/reinstall Windows PASS
19. arbitrary target Git repository behavior PASS
20. final working tree clean
21. raw task text is not persisted in lifecycle events
22. lifecycle Event failure cannot change normal Codex task exit result
23. no-skill normal task creates Gap Event only, never Candidate automatically
24. global installed control plane can load protected regression without repository evaluation tree
25. scaling measurement records 10/50/100/500/1000 without adding semantic router

## V8.2 완료 후

이 Task까지 COMPLETE - VERIFIED가 된 뒤 Optional Skill Batch 2 이상의 대량 확장을 진행합니다.

V8.3+ 후보:

- semantic/embedding candidate retrieval
- background maintenance scheduling
- automated external source ingestion
- richer utility/cost dashboard
- multi-agent evolution experiments

## 완료 조건

구현은 완료했습니다. 실제 Windows Evidence 확인 전 `COMPLETE - VERIFIED`로 표시하지 않습니다.
