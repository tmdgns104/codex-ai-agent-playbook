# V8.1 아키텍처 - Dynamic Capability Library

상태: **Baseline implemented / CAP-001 ~ CAP-008 verified**

> 이 문서는 V8.1의 설계 기준입니다. 현재 자동 실행 경로는 optional Skill 중심이며 MCP/Agent 자동 spawn, optional LLM tie-break, project cache 등 일부 항목은 후속 확장 대상으로 남아 있습니다.

## 1. 목표 구조

```text
User Request
    ↓
Task Signals
    ↓
Capability Router
    ├─ Deterministic Filter
    ├─ Metadata Scoring
    └─ Optional Tie-break
    ↓
Minimum Capability Plan
    ↓
Risk / Permission Gate
    ↓
Activation Manager
    ↓
Implementation
    ↓
Repository Verification
    ↓
Quality Gate
    ↓
Deactivate / Project Cache
```

## 2. Repository 구조

초기 목표:

```text
capability-library/
├─ registry.json
├─ sources.json
├─ skills/
│  └─ optional/
├─ mcp/
│  └─ optional/
├─ agents/
│  └─ optional/
└─ wrappers/
   ├─ cli/
   └─ rest/

harness/
├─ router/
│  ├─ capability_router.py
│  └─ scoring.py
├─ activation/
│  └─ capability_manager.py
├─ security/
│  ├─ capability_policy.py
│  └─ harness_audit.py
├─ quality/
│  └─ quality_gate.py
└─ evaluation/
   └─ fixtures.json
```

기존 `.agents/skills/`는 V8 Core Skills를 유지합니다. Optional Capability 전체를 전역 활성 Skill 경로에 넣지 않습니다.

## 3. Capability Registry

Router가 먼저 읽는 것은 `registry.json`입니다.

본문 전체가 아니라 다음 수준의 짧은 metadata만 유지합니다.

```json
{
  "id": "security-review",
  "type": "skill",
  "summary": "인증, 권한, secret, 외부 입력 변경의 보안 검토",
  "domains": ["security", "auth", "api"],
  "triggers": ["jwt", "oauth", "password", "token"],
  "activation": "on_demand",
  "risk": "high",
  "recommended_profile": "strict",
  "permissions": ["local_read"],
  "context_cost": "medium",
  "dependencies": [],
  "source_id": "ecc-security-review",
  "license": "MIT",
  "path": "capability-library/skills/optional/security-review"
}
```

## 4. Router 계층

### 4.1 Deterministic Filter

입력 신호:

- 사용자 Task text
- changed/requested file extensions
- well-known files
- repository structure
- 현재 Verification Profile
- explicit user request

예:

```text
Dockerfile            -> docker
*.py                   -> python
package.json           -> javascript/typescript
.github/workflows/*    -> ci
migration / schema     -> database/migration
auth / jwt / oauth     -> security
playwright.config.*    -> e2e
```

이 단계에서는 LLM을 사용하지 않습니다.

### 4.2 Metadata Scoring

후보 점수 개념:

```text
score =
  task_domain_match
+ trigger_match
+ repository_signal
+ risk_relevance
+ explicit_request
- context_cost
- dependency_cost
- permission_risk
- overlap_penalty
```

정확한 가중치는 evaluation fixture로 조정합니다.

### 4.3 Optional Tie-break

다음 경우에만 LLM 판단을 허용합니다.

- 상위 후보 점수가 유사함
- Task 의미가 규칙만으로 불명확함
- Architecture/risk 의미 판별이 필요함

LLM에는 전체 Registry가 아니라 상위 3~5개 metadata만 제공합니다.

## 5. Selection Policy

기본 선택 상한:

```text
skills <= 3
mcp <= 1
agents <= 1
```

기본적으로 capability 0개도 유효합니다.

중복 Capability는 overlap penalty로 줄입니다.
예를 들어 일반 `code-review`와 언어별 review가 모두 후보일 때 둘 다 필요한 근거가 없으면 하나만 선택합니다.

## 6. Activation Manager

Activation Manager는 `available`과 `active`를 분리합니다.

상태:

- `available`: Library에 존재
- `selected`: Router가 현재 Task 후보로 선택
- `approved`: 권한 Gate 통과
- `active`: 현재 Task에서 사용 가능
- `cached`: project-scoped 재사용 후보

기본 수명:

```text
Task 시작 -> selected/approved/active
Task 종료 -> deactivate
```

Project cache는 반복 사용이 명확한 read-only/low-risk capability에만 허용하고, credential/external-write/destructive capability는 cache하지 않습니다.

## 7. Skill / Wrapper / MCP / Agent 선택 원칙

### Skill

가장 우선합니다.

적합한 경우:

- 절차/체크리스트/판단 규칙 제공
- 추가 runtime이 필요 없음
- repository/tool 사용법을 안내하는 역할

### CLI wrapper

이미 검증된 CLI가 있는 경우 MCP보다 우선 검토합니다.

예:

- GitHub -> `gh`
- E2E -> Playwright CLI
- Git -> `git`

### REST wrapper

간단한 최신 문서/API 조회처럼 stateful MCP가 필요 없는 경우 고려합니다.

### MCP

다음 조건을 모두 검토합니다.

- stateful interaction 가치
- CLI/REST/native tool보다 우수
- tool schema/context 비용 정당화
- permission risk 허용 가능

### Agent

가장 높은 임계값을 적용합니다.

- independent verification
- 고위험 리뷰
- 독립적 병렬 조사

이외에는 Main Codex가 직접 수행합니다.

## 8. V8 통합 지점

### `.codex/AGENTS.md`

새 상세 Capability 목록을 넣지 않습니다.
추가되더라도 짧은 원칙만 허용합니다.

### `codex-skill-router`

V8.1에서는 기존 Router가 Capability Router를 호출하거나 결과를 사용할 수 있도록 역할을 축소/연결합니다.

### Verification Profiles

Capability가 권장 Profile을 제시할 수 있으나 최종 Profile은 Task risk와 Repository 계약이 결정합니다.

Capability가 STRICT를 약화시킬 수 없습니다.

### Quality Gate

Quality Gate는 Capability 선택 성공 여부를 대신 판정하지 않습니다.
Repository Verification과 Evidence의 최종 보조 Gate 역할을 유지합니다.

### Harness Audit

V8.1에서는 다음 검사를 추가합니다.

- registry schema
- duplicate capability id
- invalid path
- source/license metadata
- permission enum
- activation policy enum
- optional capability가 active discovery path에 잘못 설치됐는지

## 9. 초기 P0 구현 순서

1. Registry schema + validator
2. 6개 sample capability metadata
3. deterministic filter
4. scoring
5. selection limits / overlap resolution
6. permission policy
7. dry-run capability plan CLI
8. Harness Audit 통합
9. evaluation fixtures
10. 실제 activation은 dry-run 검증 후 진행

## 10. 중요한 안전 제약

초기 P0에서는 Router가 다음을 자동 수행하지 않습니다.

- credential 사용
- external write
- database write
- production action
- destructive action
- MCP config 영구 변경
- Agent 자동 spawn

먼저 selection/dry-run correctness를 검증한 뒤 단계적으로 활성화합니다.
