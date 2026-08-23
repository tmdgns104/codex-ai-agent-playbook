# Codex AI Agent Playbook Kit - V8.2

Codex를 **적은 고정 Context**, **필요한 Capability만 선택하는 구조**, **실제 Evidence 기반 검증**, **Self-Managing Skill Control Plane**으로 여러 프로젝트에서 일관되게 사용하기 위한 전역 Playbook + Skills + Harness입니다.

현재 안정 버전: **V8.2 (`main`)**  
2026-08-23 Windows 실환경 검증 완료 / PR #6 Merge 완료

> 처음 사용하는 경우에는 [빠른 시작 문서](docs/QUICKSTART.md)부터 보는 것을 권장합니다.

---

## 1. 현재 상태

```text
Stable branch         main
Stable version        V8.2
Core Skills           7
Optional Skills       10
Wrapper Capabilities  2
Registry total        12 capabilities
Global AGENTS.md      4579 bytes
Windows status        COMPLETE - VERIFIED
```

V8.2는 V8.1의 Dynamic Capability Library 위에 **Self-Managing Skill Library**를 추가했습니다.

```text
Skill Library는 커질 수 있음
        ↓
하지만 매 작업 Context는 커지지 않음
        ↓
필요한 Skill만 0~3개 선택
        ↓
사용 Evidence는 가볍게 기록
        ↓
필요할 때만 Creator / Evolver / Curator 유지보수
```

---

## 2. 이 프로젝트가 해결하려는 문제

Codex를 오래 사용하면서 규칙과 Skill을 계속 추가하면 다음 문제가 생길 수 있습니다.

- 모든 작업에서 큰 전역 Prompt를 반복해서 읽음
- Skill이 많아질수록 불필요한 Context까지 노출됨
- 작은 수정에도 복잡한 절차가 적용됨
- Agent 자기보고 `PASS`를 실제 검증으로 착각할 수 있음
- 긴 작업이 Chat history에 의존해 재시작/재개가 어려움
- 보안 작업과 README 오타에 같은 검증 비용을 씀
- Skill이 늘어날수록 사람이 직접 중복/노후/충돌을 관리해야 함

V8.2는 다음을 목표로 합니다.

```text
Library는 풍부하게
현재 Context는 작게
검증은 실제 Evidence로
Skill 유지보수는 deterministic Control Plane 중심으로
```

---

## 3. 전체 동작 흐름

### 일반 작업 경로

```text
사용자 작업
    ↓
Global Working Agreement
    ↓
Deterministic Metadata Router
    ↓
최소 Capability Plan
    ↓
Risk / Permission Gate
    ↓
필요한 optional Skill만 임시 활성화
    ↓
Codex 실행
    ↓
Repository Verification
    ↓
Quality Gate / Evidence
    ↓
privacy-safe lifecycle Event
    ↓
Runtime Cleanup
```

Skill 0개도 정상입니다.

```text
README 오타 한 줄 수정
→ MINIMAL
→ optional Skill 0개

JWT 인증 오류 수정 + regression test
→ STRICT
→ security-review
→ testing
→ root-cause-debugging
```

### Self-Managing 유지보수 경로

```text
Events / Gap / Failure / Correction
        ↓
Deterministic grouping / eligibility
        ↓
Creator / Evolver / Curator Proposal
        ↓
Candidate
        ↓
Skill Audit
        ↓
Protected Regression
        ↓
Promotion Gate / Human Gate
        ↓
ACTIVE Library
```

Creator/Evolver/Curator는 일반 task 시작 시 자동 실행되지 않습니다.

---

## 4. 설치 구조

Windows 설치 후:

```text
%USERPROFILE%\.codex\
├─ AGENTS.md
├─ capability-library\
│  ├─ registry.json
│  ├─ sources.json
│  ├─ governance\
│  └─ skills\optional\
├─ playbook-harness\
│  ├─ activation\
│  ├─ router\
│  ├─ quality\
│  ├─ security\
│  └─ skills\
├─ .playbook-state\
└─ playbook-backups\

%USERPROFILE%\.agents\skills\
├─ ai-agent-development-playbook\
├─ codex-long-run\
├─ codex-skill-router\
├─ codex-task-router\
├─ guide-ppt-creator\
├─ human-centered-project-builder\
└─ human-readable-code\
```

`~/.codex/AGENTS.md`에는 항상 필요한 최소 전역 운영 원칙만 유지합니다. V8.2 최종 Windows 검증 기준 Playbook 전역 영역은 **4579 bytes**입니다.

`~/.agents/skills/`에는 **7개 Core managed Skill**이 설치됩니다.

`~/.codex/capability-library/`에는 작업별로 선택할 Optional Skill, wrapper, governance metadata를 보관합니다.

`~/.codex/playbook-harness/`에는 Router, Activation, Launcher, Quality Gate, Audit, Self-Managing Control Plane이 들어 있습니다.

`~/.codex/.playbook-state/`에는 runtime Event, queue, Candidate 등 로컬 운영 상태를 저장합니다. raw task text를 저장하지 않는 방향으로 설계되어 있습니다.

---

## 5. 설치 - Windows

준비물:

```cmd
git --version
python --version
codex --version
```

### CMD

```cmd
git clone https://github.com/tmdgns104/codex-ai-agent-playbook.git
cd codex-ai-agent-playbook
powershell -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

### PowerShell

```powershell
git clone https://github.com/tmdgns104/codex-ai-agent-playbook.git
cd codex-ai-agent-playbook
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

설치 스크립트는 기존 사용자 설정을 무조건 덮어쓰지 않습니다.

- 전역 `AGENTS.md`는 Playbook marker 구간만 관리
- Core Skill은 managed Skill만 관리
- 변경된 managed 파일은 backup 생성
- Capability Library 설치
- Harness 설치
- 설치 직후 verification 자동 실행

정상 마지막 출력 예:

```text
PASS     global AGENTS.md playbook block
PASS     capability library
PASS     playbook harness
PASS     harness audit
RESULT   PASS
```

---

## 6. 기존 설치 업데이트

Playbook Repository에서:

```cmd
git switch main
git pull origin main
powershell -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

같은 버전을 다시 설치하고 내용이 동일하면:

```text
OK       capability library
OK       playbook harness
```

처럼 나오며 새 backup이나 불필요한 재복사가 발생하지 않습니다.

설치 상태만 다시 확인:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\verify-install.ps1"
```

---

## 7. 가장 쉬운 실제 사용법

설치가 끝났다면 Playbook Repository가 아니라 **실제로 수정할 프로젝트의 Git Repository**로 이동합니다.

```cmd
cd /d D:\my-project
```

작업 문장만 전달합니다.

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행"
```

Launcher가 자동으로 Task 분류 → Optional Skill 선택 → Profile 결정 → Permission Gate → 선택 Skill 임시 노출 → Codex 실행 → Event 기록 → Cleanup을 수행합니다.

---

## 8. 실제 Codex 실행 전에 결과만 확인

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행" --dry-run
```

실제 Windows 검증 결과:

```text
PROFILE     STRICT
SKILLS      security-review,testing,root-cause-debugging
COUNT       3
BRIDGE      true
DRY_RUN     true
RESULT      READY
CLEANUP     BRIDGE_CLEANED
EVENT       EVENT_SKIPPED
RESULT      DRY_RUN_COMPLETE
```

작은 작업:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "README 오타 한 줄 수정" --dry-run
```

대표 결과:

```text
PROFILE     MINIMAL
SKILLS      none
COUNT       0
BRIDGE      false
```

`--dry-run`에서는 실제 작업을 수행하지 않기 때문에 lifecycle Event도 기록하지 않습니다.

---

## 9. Core Skills - 7개

| Skill | 용도 | 언제 유용한가 |
|---|---|---|
| `codex-skill-router` | 최소 Skill/Profile 추천 | 어떤 Skill을 써야 할지 애매한 비단순 작업 |
| `ai-agent-development-playbook` | Architecture/Agent/RAG/Tooling 개발 규율 | 복잡한 AI/Agent 시스템 개발 |
| `codex-long-run` | 긴 작업의 checkpoint/resume | 여러 구현·디버깅·검증 cycle |
| `codex-task-router` | Complexity/Risk/Reasoning/병렬성 판단 | 모델/작업 topology 판단이 필요한 경우 |
| `human-readable-code` | 가독성/유지보수성 | 사람이 읽고 배워야 하는 코드 |
| `human-centered-project-builder` | Problem→Requirements→Architecture→Task→Verification | 새 프로젝트/비단순 프로젝트 시작 |
| `guide-ppt-creator` | 기술/프로젝트 가이드 PPT Workflow | 발표/학습/설명용 자료 제작 |

Core Skill도 모든 작업에서 전부 사용하지 않습니다.

---

## 10. Optional Skills - 10개

Optional Skill은 `%USERPROFILE%\.codex\capability-library\skills\optional\`에 보관합니다.

| Skill | 대표 용도 | 권장 상황 |
|---|---|---|
| `security-review` | 인증/권한/secret/외부 입력 보안 검토 | JWT, OAuth, 토큰, 권한 변경 |
| `testing` | 재현/focused test/regression/acceptance verification | 테스트 추가, 회귀 방지 |
| `root-cause-debugging` | 가설/Evidence 기반 root cause 추적 | 원인 불명 오류, 반복 장애 |
| `code-review` | 정확성/회귀/가독성/계약 위반 검토 | diff/refactor 품질 검토 |
| `api-design` | REST/GraphQL/OpenAPI/public API contract | endpoint/API 설계 |
| `sql-optimization` | 실행계획/index/N+1/scan 병목 진단 | 느린 SQL, DB 성능 문제 |
| `docker-container` | Dockerfile/image/cache/non-root/secret | container build 개선 |
| `dependency-upgrade` | changelog/migration/lockfile/rollback | package/framework 버전 업 |
| `performance-profiling` | latency/throughput/CPU/memory profiling | 성능 최적화와 benchmark |
| `resilient-error-handling` | retry/backoff/timeout/idempotency/circuit breaker | 외부 API/서비스 실패 경계 |

Optional Skill은 전역 discovery 경로에 전부 영구 설치하지 않습니다. Router가 현재 Task에 필요하다고 판단한 것만 session-scoped bridge로 노출합니다.

---

## 11. Wrapper Capabilities - 2개

| Capability | Type | 용도 | 주의 |
|---|---|---|---|
| `documentation-lookup` | REST wrapper | 최신 공식 문서/API 확인 | network permission 검토 |
| `github-ops` | CLI wrapper | branch/commit/push/PR 작업 규율 | external write Human Gate 가능 |

따라서 Registry 전체는 **12 capabilities = Optional Skill 10 + Wrapper 2**입니다.

---

## 12. 자동 Skill 선택은 자동 권한 승인이 아님

민감 권한 예:

```text
credential_access
external_write
database_write
destructive
production
network
browser_control
```

예:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "GitHub에 commit push하고 PR 생성" --dry-run
```

권한 Gate가 필요하면:

```text
RESULT      HUMAN_GATE_REQUIRED
```

으로 자동 진행을 차단합니다.

---

## 13. Self-Managing Skill Library

V8.2에서는 Skill Library가 커져도 사람이 모든 Skill을 매번 직접 점검하지 않도록 관리 계층을 추가했습니다.

### Control Plane - LLM 0-token 영역

```text
Capability Registry
Metadata Router
Event / Evidence Store
Gap Detection
Proposal Queue
Lifecycle validation
Skill Audit
Protected Regression
Base Hash / Locking
Promotion Gate
Rollback metadata
```

### Intelligence Plane

```text
Skill Creator
Skill Evolver
Skill Curator
```

#### Creator

반복되는 실제 Capability Gap에서 새 Skill Candidate를 제안합니다.

- Router miss 1회로 자동 생성하지 않음
- 반복 Evidence 필요
- 기존 Skill로 해결 가능한 경우 기존 Skill 우선
- Candidate만 만들고 ACTIVE를 바로 변경하지 않음

#### Evolver

ACTIVE Skill의 반복 실패/수정 Evidence를 바탕으로 다음 버전 Candidate를 제안합니다.

```text
ACTIVE vN
→ Evidence
→ Candidate vN+1
→ Audit
→ Regression
→ Promotion
```

#### Curator

Library의 비대화, 중복, 책임 혼합, routing collision을 감시합니다.

- 정상 작업마다 전체 Skill 본문을 읽지 않음
- metadata/statistics 중심
- low usage/time만으로 archive하지 않음
- split/merge/archive는 Human Gate 대상

### 유지보수 CLI

Repository source에서:

```cmd
python harness\skills\manage.py audit
python harness\skills\manage.py gaps
python harness\skills\manage.py proposals
python harness\skills\manage.py curate
python harness\skills\manage.py benchmark --repeats 20
```

설치형:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" audit
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" gaps
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" proposals
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" curate
```

V8.2 maintenance CLI는 LLM provider를 필수 dependency로 요구하지 않습니다.

---

## 14. Verification Profile

```text
MINIMAL  = 작고 격리된 저위험 변경
STANDARD = 일반적인 비단순 개발
STRICT   = 보안/권한/배포/마이그레이션/중요 Architecture 등 고위험 변경
```

Skill 수와 검증 Profile은 같은 개념이 아닙니다.

---

## 15. Deterministic Quality Gate

일반적인 작업:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\quality\quality_gate.py" --repo . --profile standard
```

STRICT + 실제 검증 명령:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\quality\quality_gate.py" --repo . --profile strict --verify "python -m pytest"
```

결과:

```text
0 = PASS
1 = FAIL
2 = UNVERIFIED
```

STRICT인데 필요한 실행 Evidence가 없으면 `PASS`라고 추측하지 않고 `UNVERIFIED`로 종료합니다.

---

## 16. Skill Audit와 Harness Audit

Skill Library 검사:

```cmd
python harness\quality\skill_audit.py --root .
```

Playbook 전체 검사:

```cmd
python harness\security\harness_audit.py --root .
```

Skill Audit의 broad-trigger/overlap WARN은 **검토 신호**이며 자동 merge/archive 근거로 단독 사용하지 않습니다.

Harness Audit 정상 마지막 출력:

```text
INFO       warnings: 0
RESULT     PASS
```

---

## 17. V8.2 실제 Windows 검증

2026-08-23 실제 Windows 환경에서 확인했습니다.

```text
Lifecycle Integration              11/11 PASS
Lifecycle Control Plane             4/4 PASS
Skill Creator                      14/14 PASS
Skill Evolver                      13/13 PASS
Skill Curator                      12/12 PASS
Governance                         12/12 PASS
Event Store                         6/6 PASS
Proposal Queue                      7/7 PASS
Skill Audit                         9/9 PASS
Installed Skill Audit             FAIL 0 / WARN 6
Capability Router                  28/28 PASS
Capability Manager                 12/12 PASS
Skill Materializer                 10/10 PASS
Discovery Bridge                   10/10 PASS
Playbook Launcher                  12/12 PASS
Installed Launcher                  2/2 PASS
Harness Audit                      PASS / warnings 0
STRICT Quality Gate                PASS / ERRORLEVEL 0
Global install                     PASS
Same-version reinstall             PASS / idempotent
Arbitrary Git repo JWT routing     STRICT / exact 3 skills
Working tree                       clean
```

Metadata Router synthetic benchmark, 20회 평균:

```text
10 skills      0.0586 ms
50 skills      0.2308 ms
100 skills     0.4712 ms
500 skills     2.3551 ms
1000 skills    5.0401 ms
```

V8.2에서는 이 결과를 근거로 semantic/embedding Router를 상시 추가하지 않았습니다.

---

## 18. 제거

Windows:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\uninstall.ps1"
```

Linux/macOS:

```bash
./uninstall.sh
```

Playbook AGENTS marker block, Core managed Skills, Capability Library, Harness를 제거합니다. 사용자가 marker 밖에 작성한 내용과 backup은 보존합니다.

---

## 19. 문제가 생겼을 때

Playbook Repository에서:

```cmd
git status --short
powershell -NoProfile -ExecutionPolicy Bypass -File ".\verify-install.ps1"
python harness\security\harness_audit.py --root .
```

설치형 Skill Control Plane 확인:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" audit
```

---

## 20. 관련 문서

- [빠른 시작](docs/QUICKSTART.md)
- [동작 원리](docs/HOW_IT_WORKS.md)
- [Skills 가이드](docs/SKILLS.md)
- [개발 가이드](docs/DEVELOPMENT.md)
- [V8.2 Self-Managing Requirements](V8_2_SELF_MANAGING_SKILLS_REQUIREMENTS.md)
- [V8.2 Self-Managing Architecture](V8_2_SELF_MANAGING_SKILLS_ARCHITECTURE.md)
- [V8.2 Self-Managing Policy](V8_2_SELF_MANAGING_SKILLS_POLICY.md)
- [V8.2 Self-Managing Evaluation](V8_2_SELF_MANAGING_SKILLS_EVALUATION.md)
- [V8.2 LLM-Independent Control Plane](V8_2_LLM_INDEPENDENT_CONTROL_PLANE.md)

---

## 최종 원칙

```text
Capability는 많이 보유할 수 있다.
하지만 현재 Task에는 필요한 최소 Capability만 노출한다.

Self-Managing 기능은 Library를 관리한다.
하지만 정상 작업마다 LLM 비용을 추가하지 않는다.

토큰을 줄인다.
하지만 정확성과 검증 신뢰성을 낮추지는 않는다.
```
