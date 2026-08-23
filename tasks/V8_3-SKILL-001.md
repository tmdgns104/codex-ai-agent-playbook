# V8.3-SKILL-001 - Batch 2 Candidate Review

상태: **READY FOR IMPLEMENTATION**

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

## 각 Candidate에 대해 작성할 Evidence

각 후보는 최소 다음 항목으로 평가합니다.

```text
id
summary
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

## 중복 판단 규칙

단순히 주제가 비슷하다는 이유로 새 Skill을 만들지 않습니다.

다음 중 하나 이상이 명확해야 별도 Skill로 ACCEPT할 수 있습니다.

1. 실행 절차가 기존 Skill과 실질적으로 다름
2. 필요한 evidence/verification이 다름
3. permission boundary가 다름
4. trigger를 명확하게 분리할 수 있음
5. 반복 사용 utility가 충분히 큼

예:

- `refactoring` vs `code-review`
  - review는 문제 탐지/검증 중심
  - refactoring은 behavior-preserving change workflow 중심일 때만 별도 유지

- `database-schema-migration` vs `sql-optimization`
  - migration은 schema evolution/rollback/data safety
  - optimization은 query plan/index/runtime performance

- `observability-logging` vs `root-cause-debugging`
  - observability는 telemetry 설계
  - debugging은 이미 발생한 failure의 원인 추적

## Source 검토 규칙

외부 Source는 자동 신뢰하지 않습니다.

- 공식 Agent Skills specification/examples
- Anthropic public Skills
- 명확한 MIT/Apache 등 license의 community repository
- 기존 ECC/JayRHa

을 참고할 수 있습니다.

각 후보는 실제 채택 전에 source URL, license, adaptation 방식을 기록합니다.

Deprecated catalog 또는 license가 불명확한 source는 직접 복사하지 않습니다.

## 산출물

이 Task 완료 시 다음 파일을 추가합니다.

```text
evaluation/v8_3/batch2-candidate-review.json
V8_3_SKILL_BATCH2_SELECTION.md
```

필요하면 `capability-library/sources.json`에 **reference-only** source metadata를 추가할 수 있지만, ACTIVE registry는 아직 변경하지 않습니다.

## Verification

최소 검증:

```text
1. JSON parse PASS
2. 20 Candidate 모두 decision 존재
3. ACCEPT 후보 12~16개
4. ACCEPT끼리 duplicate id 없음
5. 기존 12 capability와 id 충돌 없음
6. ACCEPT 후보마다 permission/risk/context_cost/source/license 상태 존재
7. ACCEPT 후보마다 overlap 설명 존재
8. license unknown인 후보는 ACTIVE 구현 대상으로 확정하지 않음
9. existing protected routing fixture 변경 없음
10. Global AGENTS 변경 없음
```

## 금지

이 Task에서 하지 않습니다.

- Skill package 12~20개 대량 생성
- registry ACTIVE entry 추가
- install.ps1 수정
- semantic Router 도입
- Core Skill 추가
- 외부 script 자동 실행
- permission expansion 자동 승인

## 완료 조건

20개 후보의 Evidence 기반 리뷰가 끝나고 12~16개 Batch 2 구현 대상이 확정되면 COMPLETE로 전환합니다.

그 다음 Task에서 선택된 Skill을 작은 묶음으로 구현/검증합니다.
