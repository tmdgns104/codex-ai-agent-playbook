# V8.3-SKILL-001 - Batch 2 Candidate Review

상태: **COMPLETE - VERIFIED**

선행 조건:

- V8.2-SKILL-006 — COMPLETE - VERIFIED
- `V8_3_SKILL_LIBRARY_EXPANSION.md` — DESIGN BASELINE

## 목적

현재 Optional Skill 10개와 Wrapper 2개를 기준으로 V8.3 Batch 2 후보 20개의 중복, trigger 경계, 권한, utility를 검토하고 실제 구현 대상으로 사용할 12~16개 Candidate를 확정합니다.

이 Task에서는 Skill package를 대량 구현하거나 ACTIVE registry를 바로 변경하지 않습니다.

## 현재 기준

Core managed Skill 7개:

- ai-agent-development-playbook
- codex-long-run
- codex-skill-router
- codex-task-router
- guide-ppt-creator
- human-centered-project-builder
- human-readable-code

현재 Optional Skill 10개:

- api-design
- code-review
- dependency-upgrade
- docker-container
- performance-profiling
- resilient-error-handling
- root-cause-debugging
- security-review
- sql-optimization
- testing

현재 Wrapper 2개:

- documentation-lookup
- github-ops

## Candidate Pool

### Python / Runtime

- python-project-engineering
- python-typing
- async-python
- powershell-windows

### Backend / Integration

- fastapi-backend
- api-client-integration
- websocket-realtime
- configuration-management

### Data / Database

- data-analysis-pandas
- data-validation
- etl-data-pipeline
- database-schema-migration

### Delivery / Operations

- ci-cd-workflow
- observability-logging
- release-packaging
- git-conflict-resolution

### Code Quality / Architecture

- refactoring
- architecture-review
- cli-development
- documentation-maintenance

## 평가 규칙

각 후보는 다음 항목으로 평가했습니다.

```text
id
primary domains
positive triggers
negative / exclusion triggers
expected permissions
context cost
existing overlap
why existing Skill cannot cover it cleanly
likely frequency / utility
risk
candidate source references
license status
recommendation: ACCEPT / MERGE / DEFER / REJECT
```

별도 Skill로 ACCEPT하려면 다음 중 하나 이상이 명확해야 합니다.

1. 실행 절차가 기존 Skill과 실질적으로 다름
2. 필요한 evidence/verification이 다름
3. permission boundary가 다름
4. trigger를 명확하게 분리할 수 있음
5. 반복 사용 utility가 충분히 큼

## Source 정책

외부 Source는 자동 신뢰하지 않습니다.

- 공식 Agent Skills specification/examples
- Anthropic public Skills
- 명확한 MIT/Apache 등 license의 community repository
- 기존 ECC/JayRHa

를 참고할 수 있지만, 이번 Candidate Review의 ACCEPT 항목은 `internal-original`을 기본으로 했습니다.

외부 repository의 코드를 직접 복사하지 않았고 Agent Skills 표준은 형식/개념 참고에만 사용했습니다.

Deprecated catalog 또는 license가 불명확한 source는 직접 복사하지 않습니다.

## 산출물

완료:

```text
evaluation/v8_3/batch2-candidate-review.json
V8_3_SKILL_BATCH2_SELECTION.md
```

ACTIVE registry는 변경하지 않았습니다.

## 최종 Decision

```text
ACCEPT  16
MERGE    1
DEFER    3
REJECT   0
```

### ACCEPT 16

```text
python-project-engineering
python-typing
async-python
powershell-windows
fastapi-backend
api-client-integration
configuration-management
data-analysis-pandas
data-validation
etl-data-pipeline
database-schema-migration
ci-cd-workflow
observability-logging
git-conflict-resolution
refactoring
cli-development
```

### MERGE 1

```text
architecture-review
```

`ai-agent-development-playbook`의 Architecture 흐름과 강하게 겹쳐 별도 Optional Skill 대신 기존 Core reference 보강 후보로 분류했습니다.

### DEFER 3

```text
websocket-realtime
release-packaging
documentation-maintenance
```

- websocket-realtime: 먼저 async/reliability Gap Event를 확인
- release-packaging: external_write Human Gate 계약 선행 필요
- documentation-maintenance: 기존 documentation/readability 계열과 trigger 경계 추가 관찰 필요

## Verification Evidence

Candidate evidence JSON은 deterministic JSON 생성 후 parse 가능한 형태로 작성했습니다.

검증 결과:

```text
Candidate count                       20 PASS
Decision present                      20/20 PASS
ACCEPT count                          16 PASS
Candidate duplicate id               0 PASS
ACCEPT vs existing capability id      0 collision PASS
ACCEPT permission metadata            16/16 PASS
ACCEPT risk metadata                  16/16 PASS
ACCEPT context_cost metadata          16/16 PASS
ACCEPT source metadata                16/16 PASS
ACCEPT license metadata               16/16 PASS
ACCEPT unknown license                0 PASS
ACTIVE registry mutation              none PASS
Global AGENTS mutation                none PASS
Semantic Router addition              none PASS
External code copy                    none PASS
```

기존 protected routing fixture도 변경하지 않았습니다.

## 다음 구현 순서

### Batch 2A - 기반/고빈도

```text
python-project-engineering
powershell-windows
api-client-integration
configuration-management
data-analysis-pandas
data-validation
ci-cd-workflow
refactoring
```

### Batch 2B - 전문/중간 빈도

```text
python-typing
async-python
fastapi-backend
etl-data-pipeline
database-schema-migration
observability-logging
git-conflict-resolution
cli-development
```

다음 Task는 `V8.3-SKILL-002`입니다.

Batch 2A 8개를 Candidate package로 구현하고 기존 V8.2 Governance의 Candidate Audit, protected routing regression, STRICT Quality Gate를 통과한 항목만 ACTIVE로 승격합니다.

## 금지 유지

다음은 아직 하지 않습니다.

- 16개 Skill 동시 ACTIVE promotion
- Core Skill 추가
- semantic/embedding Router 도입
- 외부 script 자동 실행
- permission expansion 자동 승인
- Global AGENTS 비대화

## 완료 조건

**COMPLETE - VERIFIED.**

20개 후보의 Evidence 기반 리뷰와 16개 Batch 2 구현 대상 확정이 완료됐습니다.
