# Codex AI Agent Playbook

> **현재 안정 버전: V8.2 (`main`)**  
> 적은 고정 Context + 필요한 Skill만 자동 선택 + 실제 Evidence 기반 검증 + Self-Managing Skill Control Plane

Codex를 여러 프로젝트에서 사용할 때 **매 작업마다 거대한 지침과 모든 Skill을 읽게 하지 않고**, 현재 작업에 필요한 기능만 선택해 사용하는 경량 Playbook + Skills + Harness입니다.

V8.2는 Windows 실제 환경에서 설치, 자동 Skill 선택, 별도 Git Repository 실행, cleanup, 재설치 멱등성, Self-Managing Skill Lifecycle, STRICT Quality Gate까지 검증했습니다.

[상세 한글 가이드](README_KO.md) · [빠른 시작](docs/QUICKSTART.md) · [동작 원리](docs/HOW_IT_WORKS.md) · [Skills 가이드](docs/SKILLS.md) · [개발 기록](docs/history/README.md)

---

## 현재 상태

```text
Stable branch       main
Stable version      V8.2
Core Skills         7
Optional Skills     10
Capability wrappers 2
Registry total      12 capabilities
Global AGENTS.md    4579 bytes
Windows verification COMPLETE - VERIFIED
```

V8.2에서 추가된 핵심은 **Self-Managing Skill Library**입니다.

```text
정상 작업
→ Metadata Router
→ 필요한 Skill 0~3개 선택
→ Codex 실행
→ Verification
→ privacy-safe Event

유지보수 작업
→ Gap / Evidence 집계
→ Creator / Evolver / Curator Proposal
→ Candidate Audit
→ Protected Regression
→ Promotion / Human Gate
```

Creator/Evolver/Curator는 매 작업마다 실행되지 않습니다. 정상 작업 경로는 계속 가볍게 유지합니다.

---

## 30초 요약

```text
사용자 작업
   ↓
Deterministic Metadata Router
   ↓
필요한 optional Skill만 선택 (0~3개)
   ↓
Risk / Permission Gate
   ↓
선택된 Skill만 현재 작업에 임시 활성화
   ↓
Codex 실행
   ↓
Repository Verification / Quality Gate
   ↓
privacy-safe Event 기록
   ↓
Runtime Cleanup
```

작은 작업은 **Skill 0개**도 정상입니다.

```text
README 오타 한 줄 수정
→ MINIMAL / Skill 0개

JWT 인증 오류 수정 + regression test
→ STRICT
→ security-review
→ testing
→ root-cause-debugging
```

사용자가 평소 Skill 이름을 직접 고를 필요가 없습니다.

---

## 설치 - Windows CMD

필요한 프로그램:

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
%USERPROFILE%\.agents\skills\                 # 7 Core Skills
%USERPROFILE%\.codex\capability-library\      # Optional Skills + wrappers + governance
%USERPROFILE%\.codex\playbook-harness\        # Router / Activation / Quality / Lifecycle
%USERPROFILE%\.codex\.playbook-state\          # local runtime evidence / proposals
```

설치가 끝나면 verification도 자동 실행됩니다.

정상 예:

```text
PASS     global AGENTS.md playbook block
PASS     capability library
PASS     playbook harness
PASS     harness audit
RESULT   PASS
```

---

## 가장 쉬운 사용법

Playbook 설치 후 **실제로 작업할 Git Repository**로 이동합니다.

```cmd
cd /d D:\my-project
```

작업 문장만 전달합니다.

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행"
```

Launcher가 자동으로:

```text
Task 분류
→ Optional Skill 선택
→ MINIMAL / STANDARD / STRICT 결정
→ Permission Gate
→ 선택 Skill만 임시 노출
→ Codex 실행
→ Event 기록
→ Cleanup
```

을 수행합니다.

### 실제 Codex 실행 없이 선택 결과만 확인

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행" --dry-run
```

Windows 검증 결과:

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

`--dry-run`은 실제 task를 수행하지 않으므로 lifecycle Event도 기록하지 않습니다.

---

## Skill 구성

### Core Skills - 7개

전역 `%USERPROFILE%\.agents\skills\`에 설치되는 공통 Workflow입니다.

| Skill | 용도 |
|---|---|
| `codex-skill-router` | 애매한 비단순 작업에서 최소 Skill / Profile 추천 |
| `ai-agent-development-playbook` | 복잡한 개발, Architecture, Agent/RAG/Tooling |
| `codex-long-run` | 긴 구현/디버깅/검증 작업과 resume/checkpoint |
| `codex-task-router` | Complexity/Risk/Reasoning/병렬성 판단 |
| `human-readable-code` | 읽기 쉽고 유지보수하기 쉬운 코드 작성 |
| `human-centered-project-builder` | 요구→설계→구현→검증 프로젝트 흐름 |
| `guide-ppt-creator` | 기술/프로젝트 가이드 PPT 제작 |

### Optional Skills - 10개

Capability Library에 보관하고, 현재 작업에서 필요할 때만 임시 활성화합니다.

| Skill | 대표 용도 |
|---|---|
| `security-review` | 인증, 권한, secret, 외부 입력, 보안 검토 |
| `testing` | 재현, focused test, regression, acceptance verification |
| `root-cause-debugging` | 증상 수정 전 root cause 추적 |
| `code-review` | 정확성, 회귀, 계약 위반, 검증 누락 검토 |
| `api-design` | REST/GraphQL/OpenAPI/public API contract 설계 |
| `sql-optimization` | 실행계획 기반 SQL/index/N+1 병목 진단 |
| `docker-container` | Dockerfile, image, cache, non-root, secret 검토 |
| `dependency-upgrade` | package/framework upgrade, migration, rollback |
| `performance-profiling` | latency/throughput/CPU/memory profiling과 benchmark |
| `resilient-error-handling` | retry/backoff/timeout/idempotency/circuit breaker |

### Wrapper Capabilities - 2개

| Capability | 용도 |
|---|---|
| `documentation-lookup` | 최신 공식 문서/API 확인이 필요한 작업 |
| `github-ops` | branch/commit/push/PR 등 GitHub 작업 규율 |

`github-ops`처럼 external write가 필요한 Capability는 자동 선택되더라도 권한 Gate를 우회하지 않습니다.

전체 Skill 설명은 [docs/SKILLS.md](docs/SKILLS.md)를 참고하세요.

---

## Self-Managing Skill Library

V8.2에서는 Skill Library가 커져도 수동 관리 부담이 폭증하지 않도록 Control Plane을 추가했습니다.

### Control Plane - LLM 없이 동작

```text
Router
Event / Evidence
Gap detection
Proposal Queue
Lifecycle
Skill Audit
Protected Regression
Lock / Base Hash
Promotion Gate
Rollback metadata
```

### Intelligence Plane - 필요할 때만 사용

```text
Skill Creator
Skill Evolver
Skill Curator
```

중요한 안전 경계:

- 한 번의 Router miss만으로 Skill 자동 생성 금지
- Candidate가 ACTIVE Skill을 바로 덮어쓰지 않음
- permission/trigger 확대는 Human Gate
- split/merge/archive는 V8.2에서 자동 적용 금지
- raw task text는 lifecycle Event에 저장하지 않음
- target Git Repository에는 self-management telemetry를 만들지 않음

### 유지보수 CLI

설치형 Harness 기준:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" audit
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" gaps
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" proposals
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" curate
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" benchmark --repeats 20
```

Creator/Evolver의 semantic spec은 reviewed input을 전제로 하며, V8.2는 LLM provider를 필수 dependency로 만들지 않습니다.

---

## 검증 Profile

```text
MINIMAL
작고 격리된 저위험 변경

STANDARD
일반적인 비단순 개발

STRICT
보안 / 권한 / 배포 / 마이그레이션 / 중요한 Architecture 변경
```

Skill 수와 Profile은 별개입니다.

---

## Quality Gate

일반 작업:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\quality\quality_gate.py" --repo . --profile standard
```

STRICT + 실제 테스트:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\quality\quality_gate.py" --repo . --profile strict --verify "python -m pytest"
```

Exit code:

```text
0 = PASS
1 = FAIL
2 = UNVERIFIED
```

STRICT인데 실행 Evidence가 필요한 상황에서 `--verify`가 없으면 거짓 PASS 대신 `UNVERIFIED`를 반환합니다.

---

## 업데이트

이미 설치했다면 Playbook Repository에서:

```cmd
git switch main
git pull origin main
powershell -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

변경이 없는 동일 버전 재설치는:

```text
OK       capability library
OK       playbook harness
```

처럼 끝나며 불필요한 backup/재복사를 만들지 않습니다.

설치 상태만 확인:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\verify-install.ps1"
```

---

## 제거

Windows:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\uninstall.ps1"
```

Linux/macOS:

```bash
./uninstall.sh
```

Playbook marker 구간, Core managed Skills, Capability Library, Harness만 제거합니다. 사용자가 `AGENTS.md` marker 밖에 직접 작성한 내용과 backup은 보존합니다.

---

## V8.2 실제 Windows 검증 결과

2026-08-23 최종본에서 확인:

```text
Lifecycle Integration          11/11 PASS
Lifecycle Control Plane         4/4 PASS
Creator                        14/14 PASS
Evolver                        13/13 PASS
Curator                        12/12 PASS
Governance                     12/12 PASS
Event Store                     6/6 PASS
Proposal Queue                  7/7 PASS
Skill Audit                     9/9 PASS
Capability Router              28/28 PASS
Capability Manager             12/12 PASS
Skill Materializer             10/10 PASS
Discovery Bridge               10/10 PASS
Playbook Launcher              12/12 PASS
Installed Launcher              2/2 PASS
Harness Audit                  PASS / warnings 0
STRICT Quality Gate            PASS / exit 0
Global install/reinstall       PASS / idempotent
Arbitrary Git repo JWT routing STRICT / exact 3 skills
Final working tree             clean
```

Metadata Router synthetic benchmark, 20회 평균:

```text
10 skills      0.0586 ms
50 skills      0.2308 ms
100 skills     0.4712 ms
500 skills     2.3551 ms
1000 skills    5.0401 ms
```

현재 결과에서는 semantic/embedding Router를 상시 추가할 필요가 없어 V8.2에서는 metadata-first 방식을 유지합니다.

---

## 설계 원칙

```text
적은 영구 Context
+ 필요한 Capability만 선택
+ Metadata-first Routing
+ LLM-independent Control Plane
+ 위험도에 맞는 검증
+ Repository Source of Truth
+ 실제 Test / Diff / Artifact Evidence
- 모든 Skill 상시 로드
- 상시 Multi-Agent
- 자기보고 PASS
```

토큰을 줄이기 위해 정확성이나 검증 신뢰성을 희생하는 방식은 사용하지 않습니다.
