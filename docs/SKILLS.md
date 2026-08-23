# Skills 가이드 - V8.2

V8.2의 Capability 구성은 다음과 같습니다.

```text
Core Skills          7
Optional Skills     10
Wrapper Capabilities 2
Registry total      12 capabilities
```

핵심 원칙:

```text
Skill을 많이 가지고 있는 것 ≠ 매 작업에서 모두 읽는 것
```

현재 작업에 필요한 최소 Capability만 사용합니다.

---

## 1. Core Skills - 7개

설치 시 `%USERPROFILE%\.agents\skills\`에 관리되는 7개 Skill입니다.

| Core Skill | 대표 역할 | 사용 예 |
|---|---|---|
| `codex-skill-router` | 최소 Skill/Profile 추천 | 어떤 Skill이 필요한지 애매한 비단순 작업 |
| `ai-agent-development-playbook` | 복잡한 개발/Architecture/Agent/RAG/Tooling | Agent/RAG/Tool runtime 설계 |
| `codex-long-run` | 장기 작업 checkpoint/resume | 여러 구현·디버깅·검증 cycle |
| `codex-task-router` | Complexity/Risk/Reasoning/병렬성 판단 | 작업 topology 판단 |
| `human-readable-code` | 가독성/테스트성/유지보수성 | 사람이 읽고 학습해야 하는 코드 |
| `human-centered-project-builder` | 요구→설계→구현→검증 | 새 프로젝트 또는 비단순 프로젝트 |
| `guide-ppt-creator` | 기술/프로젝트 가이드 PPT Workflow | 학습자료/발표자료/프로젝트 설명 |

Core Skill도 항상 전부 사용할 필요는 없습니다.

---

# Core Skill 상세

## `codex-skill-router`

Skill 선택이 애매한 비단순 작업에서 **최소 Core Skill 집합과 검증 Profile**을 추천합니다.

주요 판단:

- 필요한 최소 Skill
- `MINIMAL / STANDARD / STRICT`
- long-run 필요 여부
- capability router 필요 여부
- Human Gate 필요 여부

단순 작업에는 과한 라우팅을 강제하지 않습니다.

## `ai-agent-development-playbook`

복잡한 소프트웨어/AI Agent 작업을 Repository의 승인된 요구사항과 Architecture 안에서 진행하도록 돕습니다.

주요 역할:

- Requirements / Architecture 확인
- Task Contract 기반 구현
- Agent / RAG / Tool runtime 설계
- State / Tool / Resource 계약
- Human Gate
- Evidence 기반 완료 판단

## `codex-long-run`

긴 Repository 작업을 여러 cycle/session에 걸쳐 안정적으로 이어가기 위한 Skill입니다.

주요 역할:

- minimum sufficient context
- stale state guard
- focused verification budget
- meaningful checkpoint
- repository-based resume

작은 수정에는 사용하지 않습니다.

## `codex-task-router`

하나의 작업에서 필요한 Codex capability 수준을 판단합니다.

대표 기준:

- Complexity
- Uncertainty
- Risk
- Architecture Impact
- Verification Difficulty
- Parallelizability
- Cost Sensitivity

실제 모델 이름을 전역 규칙에 영구 hardcode하지 않습니다.

## `human-readable-code`

사람이 읽고 배우고 유지보수하기 쉬운 코드에 집중합니다.

```text
Correctness
→ Understandability
→ Testability
→ Maintainability
→ Performance
→ Cleverness
```

## `human-centered-project-builder`

새 프로젝트나 비단순 프로젝트를 다음 흐름으로 진행할 때 사용합니다.

```text
Problem
→ Requirements
→ Architecture
→ Task
→ Implementation
→ Verification
→ Explanation
```

## `guide-ppt-creator`

기술 문서나 프로젝트를 사람이 이해할 수 있는 가이드 PPT로 만드는 Workflow입니다.

```text
Source Analysis
→ Audience / Goal
→ Storyboard
→ Slide Contract
→ Build
→ Render / Inspect
→ Visual QA
→ Content QA
```

---

## 2. Optional Skills - 10개

Optional Skill은 다음 위치의 Capability Library에 보관합니다.

```text
%USERPROFILE%\.codex\capability-library\skills\optional\
```

작업이 시작되면 Router가 `registry.json` metadata를 보고 필요한 것만 선택하고, session-scoped bridge로 Codex에 임시 노출합니다.

| Optional Skill | 대표 용도 | 대표 trigger 예 |
|---|---|---|
| `security-review` | 인증, 권한, secret, 외부 입력, 고위험 변경 보안 검토 | JWT, OAuth, token, 권한 |
| `testing` | 버그 재현, focused test, regression, acceptance verification | test, pytest, regression, 검증 |
| `root-cause-debugging` | 증상 수정 전 가설/Evidence 기반 root cause 추적 | bug, error, root cause, 재현 |
| `code-review` | 정확성, 회귀, 가독성, 계약 위반, 검증 누락 검토 | review, diff, refactor, 품질 |
| `api-design` | REST/GraphQL/OpenAPI/public API contract 설계 | API design, OpenAPI, endpoint |
| `sql-optimization` | execution plan 기반 SQL/index/N+1/scan 병목 진단 | explain analyze, slow query |
| `docker-container` | Dockerfile/image/cache/non-root/secret/reproducibility | Dockerfile, multi-stage |
| `dependency-upgrade` | package/framework upgrade, migration, lockfile, rollback | major version, dependency upgrade |
| `performance-profiling` | latency/throughput/CPU/memory profiling과 benchmark | p95, p99, flamegraph, benchmark |
| `resilient-error-handling` | retry/backoff/timeout/idempotency/circuit breaker | retry, timeout, circuit breaker |

---

# Optional Skill 상세

## `security-review`

인증/인가와 외부 입력 경계처럼 실패 비용이 큰 부분을 보안 관점에서 검토합니다.

주요 대상:

- JWT / OAuth
- password / token / secret
- authorization / permission
- 외부 입력 검증
- 권한 경계 변경

권장 Profile은 `STRICT`입니다.

## `testing`

변경을 실제 실행 Evidence로 검증하기 위한 테스트 전략에 집중합니다.

주요 역할:

- 실패 재현
- focused test
- regression test
- acceptance verification
- 최소한의 유효한 verification command 선택

## `root-cause-debugging`

증상만 임시로 막기보다 원인을 좁히는 절차를 사용합니다.

```text
Reproduce
→ Hypothesis
→ Evidence
→ Narrow scope
→ Fix root cause
→ Regression verification
```

## `code-review`

변경 코드의 정확성과 위험을 focused review합니다.

검토 대상:

- correctness
- regression risk
- contract violation
- missing verification
- readability / maintainability

## `api-design`

REST/GraphQL/OpenAPI와 public API contract를 resource-first로 설계합니다.

주요 관심사:

- endpoint/resource modeling
- request/response contract
- backward compatibility
- breaking change
- validation / error contract

## `sql-optimization`

느린 SQL을 추측이 아니라 execution plan과 실제 측정으로 진단합니다.

주요 관심사:

- `EXPLAIN` / `EXPLAIN ANALYZE`
- full table scan
- index usage
- join strategy
- N+1 query
- before/after measurement

## `docker-container`

Dockerfile과 container image의 품질/안전/재현성을 검토합니다.

주요 관심사:

- multi-stage build
- build cache
- image size
- non-root runtime
- secret leakage
- reproducible build

## `dependency-upgrade`

package/framework version upgrade를 단순 버전 변경으로 끝내지 않습니다.

주요 관심사:

- changelog / migration guide
- major version breaking change
- lockfile
- compatibility
- rollback
- upgrade verification

## `performance-profiling`

성능 문제를 profiler와 수치로 확인합니다.

주요 관심사:

- baseline
- latency / throughput
- CPU / memory
- p95 / p99
- profiler / flamegraph
- before/after benchmark

## `resilient-error-handling`

외부 시스템 실패가 전체 시스템 실패로 번지지 않도록 실패 경계를 설계합니다.

주요 관심사:

- bounded retry
- exponential backoff
- timeout policy
- idempotency
- circuit breaker
- graceful degradation

---

## 3. Wrapper Capabilities - 2개

Registry에는 Skill 외에도 wrapper가 있습니다.

| Capability | Type | 대표 용도 | Permission |
|---|---|---|---|
| `documentation-lookup` | `rest-wrapper` | 최신 공식 문서/API 확인 | `network` |
| `github-ops` | `cli-wrapper` | branch/commit/push/PR 작업 규율 | `process_exec`, `network`, `external_write` 등 |

`github-ops`처럼 민감 external write가 필요한 Capability는 자동 선택되더라도 Human Gate/permission policy를 우회하지 않습니다.

---

## 4. 자동 선택 예시

### 아주 작은 수정

```text
README 오타 한 줄 수정
```

대표 결과:

```text
PROFILE MINIMAL
SKILLS none
COUNT 0
```

Skill 0개도 정상입니다.

### 보안 + 테스트 + 디버깅

```text
JWT 인증 오류를 수정하고 regression test를 실행
```

실제 Windows 검증 결과:

```text
PROFILE STRICT
SKILLS security-review,testing,root-cause-debugging
COUNT 3
```

### 민감 external write

```text
GitHub에 commit push하고 PR 생성
```

권한 Gate가 필요한 경우:

```text
RESULT HUMAN_GATE_REQUIRED
```

Skill 자동 선택은 권한 자동 승인이 아닙니다.

---

## 5. 자동 Launcher 사용

실제 작업할 Git Repository에서:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행"
```

Skill 선택만 보고 싶다면:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행" --dry-run
```

일반 사용에서는 Optional Skill 이름을 직접 지정하지 않아도 됩니다.

---

## 6. Skill Router와 Capability Router 차이

```text
codex-skill-router
→ Core Skill / Verification Profile 선택 지원

V8.2 Capability Router
→ capability-library registry metadata를 보고 Optional Capability 자동 선택
```

평소 Launcher를 사용하면 Optional Skill은 Capability Router가 자동 처리합니다.

---

## 7. Self-Managing Skill 역할

V8.2의 Creator/Evolver/Curator는 일반 사용자 작업을 위한 Optional Skill이 아니라 **Skill Library 자체를 유지보수하기 위한 관리 계층**입니다.

### Creator

반복되는 Capability Gap에서 새 Skill Candidate를 제안합니다.

- one miss != auto create
- 반복 Evidence 필요
- Candidate only
- ACTIVE 자동 덮어쓰기 금지

### Evolver

반복 실패/수정 Evidence를 기반으로 기존 Skill의 다음 버전 Candidate를 만듭니다.

### Curator

Library의 비대화/중복/책임 혼합/routing collision을 감시합니다.

```text
성장은 AI가 하고
비대화 감시는 deterministic code가 한다
```

이 세 기능은 정상 task마다 상시 실행하지 않습니다.

---

## 8. 검증 Profile과 Skill 수는 별개

```text
MINIMAL
→ 작고 격리된 저위험 변경

STANDARD
→ 일반 비단순 개발

STRICT
→ 보안/권한/배포/마이그레이션/중요 Architecture 등 고위험 변경
```

Skill을 많이 선택했다고 STRICT가 되는 것도 아니고, 강한 모델을 사용했다고 STRICT 검증을 생략할 수도 없습니다.

---

## 9. 현재 Catalog 요약

```text
Core Skills: 7
Optional Skills: 10
Wrapper Capabilities: 2
Registry Capabilities: 12
Optional Skill selection cap: 0~3
Global AGENTS.md: 4579 bytes
```

V8.2의 목표는 Skill 수 자체를 늘리는 것이 아니라 **Library가 커져도 현재 Task의 Context는 작게 유지하는 것**입니다.

Repository의 승인된 Requirements, Architecture, Task Contract가 Skill보다 우선합니다.
