# V8.1 Capability Policy

상태: **Draft for implementation**

## 1. 목적

Capability Library가 커져도 Skill/MCP/Agent가 임의로 활성화되거나 과도한 권한을 갖지 않도록 selection, activation, permission, lifetime 정책을 정의합니다.

## 2. Capability 기본 등급

### Level 0 - Metadata only

예:
- registry entry
- source/license 정보

자동 허용.

### Level 1 - Local read-only

예:
- security review Skill
- code review Skill
- architecture checklist

기본적으로 자동 선택/활성화 가능.

### Level 2 - Local execution / write

예:
- test runner wrapper
- formatter/linter 실행
- repository file 수정 절차

Repository scope와 Profile을 확인해야 합니다.

### Level 3 - Network / browser

예:
- documentation REST lookup
- browser debugging
- external API read

네트워크 사용 목적과 대상이 명확해야 합니다.

### Level 4 - Credential / external write

예:
- GitHub PR/Issue write
- authenticated cloud operation
- external service write

자동 활성화 금지. Human approval 또는 이미 명시적으로 승인된 현재 Task 계약이 필요합니다.

### Level 5 - Destructive / production

예:
- production deployment
- database destructive migration
- irreversible delete
- permission/security boundary expansion

STRICT + Human Gate 필수.

## 3. Type별 기본 정책

### Skill

- read-only procedure/checklist는 자동 선택 가능
- Skill 자체가 권한을 확장하지 않음
- Skill이 요구하는 도구 권한은 별도 Gate 대상

### CLI wrapper

- read-only 명령은 자동 실행 후보 가능
- write/delete/push/deploy 명령은 Repository Task 계약과 Profile에 따름

### REST wrapper

- public read-only lookup은 낮은 위험
- 인증/개인 데이터/외부 write는 높은 위험

### MCP

기본 정책은 `disabled until selected`입니다.

MCP 선택 조건:

1. stateful interaction이 실제로 필요
2. CLI/REST/native tool 대안보다 유리
3. tool schema/context 비용 정당화
4. 필요한 권한이 허용됨

영구 전역 MCP config 변경은 초기 P0에서 금지합니다.

### Agent

기본 정책은 `not spawned automatically`입니다.

조건부 허용:

- independent verification
- high-risk security review
- 독립 병렬 research workstream

Main Codex가 직접 수행 가능한 일반 작업에는 사용하지 않습니다.

## 4. 자동 활성화 정책

자동 활성화 허용 기본 범위:

```text
Level 0
Level 1
일부 Level 2 read/focused verification
```

자동 활성화 금지 기본 범위:

```text
credential
external write
browser write automation
DB write
production
irreversible/destructive
```

## 5. Verification Profile 연계

### MINIMAL

- Capability 0개 우선 허용
- read-only Skill 0~1개 수준 권장
- MCP/Agent 기본 금지

### STANDARD

- 일반 Skill 0~3개
- read-only CLI/REST 가능
- MCP는 명확한 필요가 있을 때만
- Agent는 기본 사용 안 함

### STRICT

- security/reviewer capability 권장 가능
- explicit verification evidence 요구
- credential/external write/destructive capability는 Human Gate와 별개로 자동 허용되지 않음

STRICT는 더 많은 Capability를 사용한다는 뜻이 아니라 더 강한 검증/권한 통제를 뜻합니다.

## 6. Allowlist / Denylist

Registry는 다음 정책 필드를 지원할 수 있어야 합니다.

```text
allow_auto_select
deny_auto_activate
requires_human_gate
```

초기 deny 대상:

- credential access
- external write
- database write
- production deployment
- destructive operation
- untrusted executable download

## 7. Source / License / Integrity

각 외부 유래 Capability는 최소 다음을 기록합니다.

- source project
- source URL 또는 repository
- license
- adaptation strategy
- local path

권장 adaptation strategy:

- `original`: 라이선스가 명확하고 원문 사용이 의도된 경우
- `adapted`: 일부 구조/아이디어를 수정하여 사용
- `rewritten`: 아이디어만 참고하고 Codex/V8용으로 재작성

기본값은 `rewritten`입니다.

향후 P1에서 registry와 capability 파일의 hash/fingerprint를 저장할 수 있습니다.
초기 P0에서는 Harness Audit으로 path/schema/provenance drift부터 검사합니다.

## 8. Capability Lifetime

### Task-scoped 기본

Task 종료 시 deactivate.

### Project-scoped cache

다음 조건을 모두 만족하는 경우만 허용 후보:

- 반복 사용성이 명확
- read-only 또는 low-risk
- repository domain과 안정적으로 연결
- Context 비용이 낮음

cache 금지:

- credential
- external write
- production
- destructive
- 일회성 browser session

## 9. Conflict Resolution

두 Capability가 중복되면 다음 순서를 적용합니다.

1. explicit user request
2. Repository-specific rule
3. 더 좁고 직접적인 Capability
4. lower permission risk
5. lower context/runtime cost
6. 일반 fallback Capability

예:

```text
code-review + python-review
```

둘 모두 필요하다는 근거가 없으면 더 직접적인 하나만 선택합니다.

## 10. 실패 시 Fallback

Router가 확신하지 못하면 Capability를 무리하게 활성화하지 않습니다.

가능한 결과:

- `NONE_REQUIRED`
- `SELECTED`
- `NEEDS_TIE_BREAK`
- `HUMAN_GATE_REQUIRED`
- `BLOCKED`

critical capability miss가 의심되면 더 약한 Profile로 내리지 않고 재분류 또는 Human Gate로 이동합니다.
