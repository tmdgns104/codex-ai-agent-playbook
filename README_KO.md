# Codex AI Agent Playbook Kit

Codex를 여러 프로젝트에서 사용할 때 **고정 Context는 작게 유지하고**, 현재 작업에 필요한 Capability만 선택해서 사용하며, 완료 여부는 실제 Evidence로 검증하기 위한 전역 Playbook + Skills + Harness입니다.

> **현재 안정 버전: V8.2 (`main`)**
>
> **Experimental / Release Candidate: V8.4-001~006 (`v8.3-expert-skill-catalog`)**
>
> **Global rollout: NOT APPROVED**

처음 사용하는 경우에는 [빠른 시작](docs/QUICKSTART.md)부터 보는 것을 권장합니다.

[영문 README](README.md) · [빠른 시작](docs/QUICKSTART.md) · [동작 원리](docs/HOW_IT_WORKS.md) · [Skills 가이드](docs/SKILLS.md) · [V8.4 RC 상태](docs/V8.4_RELEASE_CANDIDATE_STATUS.md)

---

## 1. 현재 상태

```text
Stable branch        main
Stable version       V8.2
Experimental branch  v8.3-expert-skill-catalog
V8.3 benchmark       COMPLETE
V8.4 control plane   001~006 COMPLETE
V8.4-006A            NOT IMPLEMENTED
V8.4-007             NOT IMPLEMENTED
Codex transport      NOT VERIFIED
Global rollout       NOT APPROVED
Core Skills          7
Optional Skills      10
Wrapper Capabilities 2
Registry total       12 capabilities
Windows verification COMPLETE - VERIFIED
```

### Stable과 Experimental의 차이

| 구분 | 상태 | 의미 |
|---|---|---|
| V8.2 / `main` | **Stable** | 실제 전역 설치 및 일반적인 Codex 작업에 사용하는 검증된 경로 |
| V8.3 | **Benchmark complete** | pinned external Skill의 current/raw/adapted 비교 실험 완료 |
| V8.4-001~006 | **Experimental / RC** | Adapted Context control plane의 계약·compiler·selector·materializer를 fake backend로 검증 |
| V8.4-006A | **미구현** | 실제 Codex transport 검증 필요 |
| V8.4-007 | **미구현** | Native Codex vs Current Playbook vs Adapted Context 통제 비교 필요 |
| Global rollout | **NOT APPROVED** | 실제 transport와 일반화 Evidence가 아직 부족함 |

**중요:** 현재 전역 설치에는 `main`의 V8.2만 사용합니다. Experimental branch의 V8.4 구성요소를 `install.ps1`, `install.sh`, global AGENTS, Registry, 기존 launcher에 수동 연결하지 마세요.

---

## 2. 이 프로젝트가 해결하려는 문제

Playbook의 목적은 Skill을 무조건 많이 사용하는 것이 아닙니다.

```text
사용자 작업
    ↓
작업 복잡도/위험 판단
    ↓
필요한 Capability만 선택
    ↓
필요한 검증 Profile 적용
    ↓
Codex 실행
    ↓
Repository Verification / Quality Gate
    ↓
Evidence
    ↓
Cleanup
```

작은 작업에서는 **Skill 0개가 정상적인 결과**입니다.

```text
README 오타 수정
→ MINIMAL
→ optional Skill 0개

JWT 인증 오류 수정 + regression test
→ STRICT
→ security-review / testing / root-cause-debugging
```

목표는 매 작업마다 거대한 전역 Prompt와 모든 Skill을 읽게 만드는 것이 아니라, **현재 작업에 실제로 필요한 지식만 사용하도록 하는 것**입니다.

---

## 3. Stable V8.2 기능

V8.2는 다음을 실제 Windows 환경에서 검증했습니다.

- Context-aware Metadata Router
- MINIMAL / STANDARD / STRICT Verification Profile
- 필요한 Optional Skill만 session-scoped로 활성화
- Launcher + Cleanup
- Deterministic Quality Gate
- Harness Audit
- Self-Managing Skill Library
- 설치/업데이트/rollback 경계

### 전역 Skill 구성

**Core Skills 7개**

- `codex-skill-router`
- `ai-agent-development-playbook`
- `codex-long-run`
- `codex-task-router`
- `human-readable-code`
- `human-centered-project-builder`
- `guide-ppt-creator`

**Optional Skills 10개**

- `security-review`
- `testing`
- `root-cause-debugging`
- `code-review`
- `api-design`
- `sql-optimization`
- `docker-container`
- `dependency-upgrade`
- `performance-profiling`
- `resilient-error-handling`

**Wrapper 2개**

- `documentation-lookup`
- `github-ops`

전체 설명은 [docs/SKILLS.md](docs/SKILLS.md)를 참고합니다.

---

## 4. 설치 - Windows

준비물:

```cmd
git --version
python --version
codex --version
```

처음 설치:

```cmd
git clone https://github.com/tmdgns104/codex-ai-agent-playbook.git
cd codex-ai-agent-playbook
powershell -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

설치 후 주요 위치:

```text
%USERPROFILE%\.codex\AGENTS.md
%USERPROFILE%\.agents\skills\
%USERPROFILE%\.codex\capability-library\
%USERPROFILE%\.codex\playbook-harness\
%USERPROFILE%\.codex\.playbook-state\
```

설치가 끝나면 `verify-install.ps1`로 상태를 확인할 수 있습니다.

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\verify-install.ps1"
```

정상 예:

```text
PASS     global AGENTS.md playbook block
PASS     capability library
PASS     playbook harness
PASS     harness audit
RESULT   PASS
```

---

## 5. 가장 쉬운 사용법

실제로 작업할 Git Repository로 이동합니다.

```cmd
cd /d D:\my-project
```

작업 문장만 전달합니다.

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행"
```

선택 결과만 확인하려면:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행" --dry-run
```

`--dry-run`은 실제 작업을 수행하지 않습니다.

---

## 6. Self-Managing Skill Library

V8.2에서는 Skill이 늘어나도 매 작업마다 사람이 전체 Skill을 관리하지 않도록 Control Plane을 둡니다.

```text
Router
→ Event / Evidence
→ Gap detection
→ Proposal Queue
→ Lifecycle validation
→ Skill Audit
→ Protected Regression
→ Promotion Gate
→ Rollback metadata
```

Creator / Evolver / Curator는 일반 작업마다 실행되지 않으며, Candidate가 자동으로 ACTIVE Skill을 덮어쓰지 않습니다.

---

## 7. V8.3 External Skill Benchmark

V8.3에서는 pinned external Skill snapshot을 대상으로 current/raw/adapted 전략을 비교했습니다.

Wave 2 기준:

```text
전체       8 PASS / 12 FAIL
Adapted    5/5 PASS
Current    1/5 PASS
External   1/5 PASS
```

또한 adapted context는 raw external context보다 훨씬 작은 context로 동일 fixture를 처리하는 유망한 결과를 보였습니다.

단, 이 결과는 **단일 모델·고정 fixture·제한된 반복·validator/output contract 변화가 포함된 실험**이므로 일반적인 Codex 성능 향상으로 확정하지 않습니다.

별도로 수행한 DNN 실전 실험은 탐색적 보조 실험이며 V8.4 본선 acceptance Evidence가 아닙니다.

---

## 8. V8.4 Experimental / Release Candidate

V8.4의 목적은 pinned external Skill 전체를 runtime authority로 직접 사용하지 않고, 검증 가능한 **atomic knowledge unit**으로 변환하여 Task마다 필요한 context만 선택하는 것입니다.

현재 완료:

```text
V8.4-001  Adapted Context architecture             ✅
V8.4-002  Transport / Launch contract              ✅
V8.4-003  Schema + deterministic validator         ✅
V8.4-004  Offline compiler                         ✅
V8.4-005  Selector + budget planner                ✅
V8.4-006  Session materializer / coordinator       ✅
```

현재 미완료:

```text
V8.4-006A  실제 Codex transport verification       ❌
V8.4-007   Native vs Current vs Adapted benchmark  ❌
```

### 현재 승인 상태

- `kd-sympy` compiled Definition: `DRAFT`
- `kd-citation-management` compiled Definition: `DRAFT`
- 자동 Definition approval: **DISABLED**
- 실제 Codex context binding: **DISABLED / NOT VERIFIED**
- 기존 launcher v1: **UNCHANGED**
- Router / Registry / activation / global AGENTS: **UNCHANGED**
- Global rollout: **NOT APPROVED**

V8.4의 compiler/selector/materializer는 현재 repository 내부의 실험·검증 구성요소이며 기존 전역 launcher와 연결되어 있지 않습니다.

상세 내용과 rollback 방향은 [V8.4 Release Candidate Status](docs/V8.4_RELEASE_CANDIDATE_STATUS.md)를 참고하세요.

---

## 9. 왜 아직 전역 적용하지 않는가

현재까지의 테스트는 V8.4 내부 계약과 fail-closed 동작을 fake backend로 검증한 것입니다. 실제 Codex가 별도 context channel을 정확히 소비하는지는 아직 검증하지 않았습니다.

또한 다음 비교가 아직 없습니다.

```text
Native Codex
vs
Current Playbook
vs
Adapted Context Playbook
```

따라서 지금 V8.4를 전역에 연결하면 다음 위험이 있습니다.

- task/context concatenation
- duplicate injection
- unsupported backend에서의 fallback 문제
- DRAFT Definition의 사실상 자동 활성화
- 고정 benchmark 결과를 일반화된 성능으로 오인
- Stable V8.2와 Experimental control plane 혼합

결론: **현재 V8.4는 전역 적용 대상이 아닙니다.**

---

## 10. Experimental branch 확인 방법

코드와 Evidence 검토 목적으로만 별도 clone 또는 깨끗한 worktree에서 확인합니다.

```cmd
git fetch origin
git switch v8.3-expert-skill-catalog
```

현재는 다음을 실행해 전역에 적용하면 안 됩니다.

```cmd
install.ps1
install.sh
```

특히 global `AGENTS.md`, Registry, launcher를 수동 연결하지 마세요.

---

## 11. 다음 단계

현재 RC는 여기서 동결합니다.

다음 단계는 별도의 Human approval 이후 진행합니다.

1. V8.4-006A 실제 Codex transport conformance
2. V8.4-007 Native Codex / Current Playbook / Adapted Context 통제 비교
3. 반복 실행 / 복수 모델 / 실제 task generalization 검증
4. 결과에 따른 Definition approval 또는 V8.4 중단
5. 최종 rollout Human Gate

---

## 12. 현재 결론

현재 기준으로 **Stable V8.2는 실제 사용 가능한 전역 Playbook**입니다.

V8.4는 **설계와 내부 결정론적 검증을 완료한 Experimental / Release Candidate**입니다.

따라서 현재 권장 사용 방식은:

```text
실사용
→ V8.2 / main

연구·검증
→ V8.4 / v8.3-expert-skill-catalog
```

V8.4는 실제 transport 및 통제 비교 Evidence가 확보되기 전까지 전역 적용하지 않습니다.
