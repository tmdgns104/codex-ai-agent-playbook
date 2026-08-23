# V8.2-SKILL-006 - Self-Managing Lifecycle Integration

상태: **COMPLETE - VERIFIED**

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

Creator integration 검증 중 Governance의 stricter proposal contract와 Creator 사이의 불일치가 발견되어 수정했습니다.

- `create` Proposal에서 non-empty permission delta 또는 trigger delta가 있으면 Human Gate가 필요합니다.
- Candidate 생성 자체를 막는 것이 아니라 automatic application을 막습니다.
- 수정 후 Creator regression은 14/14 PASS입니다.

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

### 8. Installed Audit Layout Parity

실제 Global install smoke에서 Repository layout과 installed layout 차이 때문에 중앙 Router fixture를 찾지 못해 `routing-fixture` false WARN 10개가 발생했습니다.

수정 후 `skill_audit.py`는 두 layout을 모두 지원합니다.

```text
Repository: <root>/harness/router/...
Installed : <root>/playbook-harness/router/...
```

같은 수정에서 Curator low-risk package Candidate인 `compress` / `extract-reference`도 Candidate Audit가 검증할 수 있도록 계약을 일치시켰습니다.

회귀 테스트를 추가한 뒤 Skill Audit unit test는 9/9 PASS했고, installed `manage.py audit`는 false WARN이 제거되어 기존 trigger review WARN 6개만 남았습니다.

### 9. Scaling Check

`manage.py benchmark`는 deterministic metadata Router를 synthetic registry로 측정합니다.

Windows 20회 평균:

```text
10 skills    0.0586 ms
50 skills    0.2308 ms
100 skills   0.4712 ms
500 skills   2.3551 ms
1000 skills  5.0401 ms
```

전 구간 `selected_count=1`, `semantic_router_added=false`였습니다.

현재 단계에서 embedding/semantic Router를 추가할 성능 근거는 없습니다.

### 10. Integration Tests

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
harness/quality/skill_audit.py
harness/quality/test_skill_audit.py
harness/skills/creator.py
harness/skills/test_creator.py
harness/skills/promotion.py
harness/skills/lifecycle_integration.py
harness/skills/manage.py
harness/skills/test_lifecycle_integration.py
harness/skills/test_lifecycle_control_plane.py
MANIFEST.txt
tasks/V8_2-SKILL-006.md
```

Global `.codex/AGENTS.md`, Router scoring, ACTIVE registry, Optional Skill content는 변경하지 않았습니다.

## Windows Evidence

최종 Windows 검증 결과:

```text
Lifecycle Integration              11/11 PASS
Lifecycle Control Plane             4/4 PASS
Skill Creator regression           14/14 PASS
Skill Evolver regression           13/13 PASS
Skill Curator regression           12/12 PASS
Governance focused tests           12/12 PASS
Event Store tests                   6/6 PASS
Proposal Queue tests                7/7 PASS
Skill Audit unit tests              9/9 PASS
Real installed Skill Audit        FAIL 0 / WARN 6
Capability Router                  28/28 PASS
Capability Manager                 12/12 PASS
Skill Materializer                 10/10 PASS
Discovery Bridge                   10/10 PASS
Playbook Launcher                  12/12 PASS
Installed Launcher                  2/2 PASS
Harness Audit                      PASS / warnings 0
STRICT Quality Gate                PASS / ERRORLEVEL 0
Quality Gate changed/untracked      0
Global AGENTS.md                    4579 bytes unchanged
Global install                    PASS
Global verify                     PASS
Same-version reinstall            PASS / all managed roots OK
Arbitrary Git repo JWT dry-run     STRICT / 3 skills / DRY_RUN_COMPLETE
Benchmark 10..1000                RECORDED / semantic_router_added=false
```

Installed Skill Audit의 WARN 6개는 기존 review signal입니다.

```text
trigger '재현' overlap: root-cause-debugging / testing
testing: test
documentation-lookup: api, latest, version
github-ops: git, pr
root-cause-debugging: bug, error
code-review: quality
```

이 WARN은 자동 merge/narrow/archive의 단독 근거로 사용하지 않습니다.

### Windows에서 발견하고 수정한 두 계약 문제

1. Creator가 permission delta를 만들면서 Human Gate를 false로 둘 수 있던 문제
   - Governance contract에 맞춰 수정
   - Creator 14/14, Control Plane 4/4 PASS

2. installed Skill Audit가 Repository-only Router test path를 사용해 false `routing-fixture` WARN 10개를 만들던 문제
   - dual-layout lookup으로 수정
   - Audit unit 9/9 PASS
   - installed audit WARN 16 -> 6, FAIL 0

둘 다 safety boundary를 완화하지 않고 기존 Governance를 더 정확히 적용하는 수정입니다.

## Acceptance Criteria

1. Existing V8.1 normal task flow remains backward-compatible — PASS
2. Global AGENTS does not meaningfully grow for self-management — PASS, 4579 bytes
3. Normal path does not invoke Creator/Evolver/Curator automatically on every task — PASS
4. Gap Event integration works — PASS
5. Creator Candidate integration works — PASS
6. Evolver Proposal integration works — PASS
7. Curator Proposal integration works — PASS
8. Failed validation preserves ACTIVE hash/content — PASS
9. Low-risk validated promotion atomic PASS — PASS
10. Human Gate scenarios block auto promotion — PASS
11. protected routing regressions PASS — PASS
12. all V8.1 router tests PASS — PASS
13. all V8.1 activation/materializer/discovery/launcher tests PASS — PASS
14. new governance/creator/evolver/curator tests PASS — PASS
15. Skill Audit PASS/WARN-only with no FAIL — PASS
16. Harness Audit PASS — PASS
17. STRICT Quality Gate PASS — PASS
18. install/verify/reinstall Windows PASS — PASS
19. arbitrary target Git repository behavior PASS — PASS
20. final working tree clean — PASS, Quality Gate changed/untracked 0
21. raw task text is not persisted in lifecycle events — PASS
22. lifecycle Event failure cannot change normal Codex task exit result — PASS
23. no-skill normal task creates Gap Event only, never Candidate automatically — PASS
24. global installed control plane can load protected regression without repository evaluation tree — PASS
25. scaling measurement records 10/50/100/500/1000 without adding semantic router — PASS

## V8.2 완료 후

이 Task까지 COMPLETE - VERIFIED가 되었으므로 Optional Skill Batch 2 이상의 대량 확장은 별도 후속 버전에서 진행합니다.

V8.3+ 후보:

- semantic/embedding candidate retrieval — 성능 Evidence가 필요할 때만
- background maintenance scheduling
- automated external source ingestion
- richer utility/cost dashboard
- multi-agent evolution experiments

## 완료 조건

**COMPLETE - VERIFIED.**

구현, Windows regression, Global install/reinstall, installed maintenance smoke, arbitrary Git repository dry-run, Harness Audit, STRICT Quality Gate까지 실제 Evidence로 확인했습니다.
