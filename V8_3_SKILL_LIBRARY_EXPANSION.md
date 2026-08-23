# V8.3 Skill Library Expansion

상태: **DESIGN BASELINE**

## 1. 출발점

V8.2 완료 시점의 설치/라이브러리 구조는 다음과 같습니다.

- Core managed Skill: 7개
- Optional Skill: 10개
- Wrapper capability: 2개
- Router benchmark: 10 / 50 / 100 / 500 / 1000 capability 규모에서 deterministic metadata routing 유지
- 1000개 synthetic registry에서도 semantic/embedding router 도입 근거 없음

V8.3의 목표는 Core를 비대하게 만들지 않고 Optional Capability Library를 체계적으로 확장하는 것입니다.

## 2. 핵심 원칙

### Core는 작게 유지

항상 전역에 노출되는 Core Skill은 현재 7개를 기본값으로 유지합니다.

새 Skill은 특별한 근거가 없으면 Core가 아니라 Optional Library로 들어갑니다.

### 많이 보관하고 적게 활성화

Optional Library에는 수십~수백 개 Skill을 보관할 수 있습니다.

하지만 한 Task에서 Codex에 실제 materialize/activate하는 Skill은 Router가 고른 소수만 사용합니다.

즉 목표는:

```text
Large Library
    ↓
Metadata Router
    ↓
Small Selected Set
    ↓
Materialize / Activate
    ↓
Codex
```

입니다.

### Skill 수보다 품질과 경계가 우선

새 Skill은 다음을 통과해야 합니다.

- 명확한 trigger
- 중복/충돌 검사
- 최소 권한
- context cost 기록
- source / license 기록
- Candidate Audit
- protected routing regression
- 기존 STRICT Quality Gate

## 3. 외부 Source 정책

외부 Skill 저장소는 그대로 대량 복사하지 않습니다.

허용 원칙:

1. 공식/표준 문서를 우선 참고
2. 저장소/개별 Skill의 license 확인
3. 현재 Playbook 구조에 맞게 재작성
4. source_id와 adaptation 방식을 registry/sources에 기록
5. trigger/permission을 원본보다 넓히지 않음
6. 검증되지 않은 script/assets는 자동 도입하지 않음

참고 우선순위:

- Agent Skills open standard / examples
- Anthropic public Skills implementation
- MIT 등 명확한 재사용 조건을 가진 community Skill repositories
- 기존 ECC / JayRHa reference

OpenAI의 과거 `openai/skills` catalog는 deprecated 상태이므로 신규 Source of Truth로 사용하지 않습니다. 최신 Codex Skill/Plugin 구조와 충돌하지 않는 개념 참고에만 사용합니다.

## 4. Batch 2 후보 Taxonomy

V8.3 첫 확장에서는 현재 10개 Optional Skill과 직접 겹치지 않는 범용 개발 능력을 우선합니다.

### A. Python / Runtime

1. `python-project-engineering`
2. `python-typing`
3. `async-python`
4. `powershell-windows`

### B. Backend / Integration

5. `fastapi-backend`
6. `api-client-integration`
7. `websocket-realtime`
8. `configuration-management`

### C. Data / Database

9. `data-analysis-pandas`
10. `data-validation`
11. `etl-data-pipeline`
12. `database-schema-migration`

### D. Delivery / Operations

13. `ci-cd-workflow`
14. `observability-logging`
15. `release-packaging`
16. `git-conflict-resolution`

### E. Code Quality / Architecture

17. `refactoring`
18. `architecture-review`
19. `cli-development`
20. `documentation-maintenance`

이 목록은 구현 확정 목록이 아니라 Candidate pool입니다.

각 Candidate는 기존 Skill과 trigger overlap 및 실제 utility를 평가한 뒤 Batch 2 ACTIVE 후보로 승격합니다.

## 5. Batch 규모

첫 구현 Batch는 한 번에 20개를 모두 ACTIVE로 만들지 않습니다.

권장 순서:

```text
20 Candidate
  ↓ overlap / utility / permission review
12~16 selected
  ↓ Candidate package
Audit + routing regression
  ↓
ACTIVE Optional Library
```

필요하면 나머지는 Batch 3로 넘깁니다.

## 6. V8.3에서 하지 않는 것

아래는 이번 Skill 확장의 기본 범위 밖입니다.

- Core Skill 무분별한 증가
- semantic/embedding Router 도입
- raw task text 저장
- 외부 Skill 자동 다운로드/자동 실행
- license 불명확한 코드 복사
- 새 Skill을 정상 task마다 전부 읽기
- Human Gate 없이 permission expansion
- external script의 silent execution

## 7. 목표 규모

V8.3 Batch 2 완료 후 1차 목표:

- Core managed Skill: 7개 유지
- Optional Skill: 10개 → 약 22~26개
- Wrapper: 필요한 경우에만 별도 추가
- 전체 Capability: 약 31~35개 수준

이후 실제 Gap Event와 usage evidence를 보고 50+, 100+ Library로 확장합니다.

## 8. 성공 조건

V8.3 Skill expansion은 다음을 만족해야 합니다.

1. Core 7개 기본 구조 유지
2. Optional Library 확장
3. 한 Task 활성 Skill 수는 기존처럼 제한
4. trigger overlap WARN/FAIL을 측정
5. permission expansion은 Human Gate 적용
6. source/license metadata 보존
7. 기존 V8.1/V8.2 routing regression PASS
8. STRICT Quality Gate PASS
9. Windows install/verify/reinstall PASS
10. arbitrary Git repository dry-run에서 불필요한 mutation 없음
11. Global AGENTS 크기 의미 있는 증가 없음
12. 성능 Evidence 없이 semantic Router를 추가하지 않음

## 9. 다음 Task

첫 실행 Task는 `tasks/V8_3-SKILL-001.md`입니다.

목적은 20개 Candidate를 자동 추가하는 것이 아니라, 기존 10개 Optional Skill과의 중복/경계를 검토하여 Batch 2 구현 대상을 확정하는 것입니다.
