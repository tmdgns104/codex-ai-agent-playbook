# V8.1 요구사항 - Dynamic Capability Library

상태: **Baseline implemented / CAP-001 ~ CAP-008 verified**

현재 안정 브랜치: `main`

부모 버전: V8

> 아래 문서는 V8.1 설계 기준 요구사항입니다. MCP/Agent 확장과 정량 토큰/성공률 비교 항목 일부는 후속 평가 대상으로 남아 있습니다.

## 1. 목적

V8.1의 목적은 Skill, MCP, Agent를 많이 보유하더라도 매 작업마다 전부 로드하지 않고, 현재 작업에 필요한 최소 Capability만 선택해 사용하는 구조를 만드는 것입니다.

핵심 목표:

```text
많이 보유
!=
많이 활성화
```

Capability 전체 본문은 기본 Context에 넣지 않습니다. Router는 짧은 metadata/index를 먼저 사용하고, 실제 선택된 Capability의 본문만 필요 시 로드합니다.

## 2. V8에서 유지할 원칙

- Global `.codex/AGENTS.md`는 짧게 유지
- Repository가 durable Source of Truth
- Agent 자기보고가 아니라 Evidence 기반 완료
- MINIMAL / STANDARD / STRICT 검증 Profile 유지
- deterministic `quality_gate.py` 유지
- `harness_audit.py` 유지
- 정확성/검증 신뢰성을 토큰 절감보다 우선
- 작은 작업에는 불필요한 Router/MCP/Agent를 사용하지 않음

## 3. 기능 요구사항

### R1. Capability Registry

Repository는 사용 가능한 Capability를 짧은 metadata로 등록할 수 있어야 합니다.

최소 타입:

- `skill`
- `mcp`
- `agent`
- `cli-wrapper`
- `rest-wrapper`

각 항목은 최소 다음 정보를 가져야 합니다.

- `id`
- `type`
- `summary`
- `domains`
- `triggers`
- `activation`
- `risk`
- `recommended_profile`
- `permissions`
- `cost`
- `dependencies`
- `source`
- `license`

### R2. Metadata-first routing

Router는 Capability 본문 전체를 먼저 읽지 않습니다.

기본 순서:

```text
Task
-> deterministic filter
-> metadata scoring
-> top candidates
-> optional tie-break
-> minimum selection
```

### R3. Zero-capability 허용

단순 작업은 Capability를 하나도 활성화하지 않고 진행할 수 있어야 합니다.

예:

- 오타 수정
- 단순 README 수정
- 명확한 한 줄 코드 수정

### R4. 기본 선택 한도

기본 목표:

```text
Skill: 0~3
MCP: 0~1
Agent: 0~1
```

한도를 초과할 때는 이유를 Evidence에 남겨야 합니다.

### R5. 활성화 임계값

Capability 타입별 기본 임계값은 다릅니다.

```text
Skill < CLI/REST < MCP < Agent
```

MCP 또는 Agent는 Skill보다 명확한 추가 가치가 있을 때만 선택합니다.

### R6. Risk / Permission Gate

Capability는 권한 특성에 따라 자동 활성화 가능 여부가 달라야 합니다.

최소 권한 범주:

- local read
- local write
- process execution
- network
- browser control
- credential access
- external write
- database write
- destructive/production

### R7. Project-scoped activation state

V8.1은 `available`과 `active`를 구분해야 합니다.

- Library에 존재하는 것 자체는 활성화가 아님
- 현재 Task 또는 Project에 필요한 Capability만 active
- Task 종료 후 deactivate가 기본
- 반복 사용 가치가 확인된 경우 project-scoped cache 가능

### R8. MCP 최소화

MCP는 다음 조건을 만족할 때 우선 고려합니다.

- stateful interaction의 가치가 큼
- CLI/REST/native tool보다 명확히 유리함
- tool schema/context 비용을 감수할 가치가 있음
- 권한/보안 요구를 충족함

### R9. Agent 최소화

별도 Agent는 다음 경우에만 고려합니다.

- 독립 검증이 품질을 실질적으로 높임
- 서로 독립적인 병렬 workstream이 존재함
- 보안/고위험 변경에서 independent reviewer가 필요함
- 추가 Context/토큰 비용보다 이득이 큼

### R10. External source provenance

외부 Skill/Agent/MCP 아이디어는 source와 license를 기록합니다.

기본 정책:

```text
원본 확인
-> 아이디어/패턴 추출
-> Codex/V8 원칙에 맞게 재작성
-> source/license 기록
```

라이선스가 불명확하거나 Claude 전용 동작에 강하게 의존하면 원문 복사보다 재작성 또는 제외를 우선합니다.

## 4. 비기능 요구사항

### N1. Context budget

V8.1의 permanent global context는 V8 대비 크게 증가하지 않아야 합니다.

목표:

- Global AGENTS 증가: `<= 5%`
- Registry 검색은 전체 Capability 본문을 로드하지 않음

### N2. Deterministic first

가능한 판단은 Python/규칙 기반으로 먼저 수행합니다.
LLM Router는 모호한 tie-break 또는 고수준 의미 판별에만 제한적으로 사용합니다.

### N3. Cross-platform

최종 설치/검증 구조는 Windows와 Linux/macOS 의미가 일치해야 합니다.

### N4. Idempotent install

동일 V8.1 재설치는 불필요한 backup/copy를 만들지 않아야 합니다.

### N5. Reversible

Uninstall은 사용자 소유 전역 설정을 보존해야 하며 V8에서 검증한 marker 기반 보존 동작을 유지해야 합니다.

## 5. 초기 Capability 범위

P0 검증용 최소 Capability:

- `security-review`
- `testing`
- `documentation-lookup`
- `github-ops`
- `root-cause-debugging`
- `code-review`

P1 후보:

- Python/backend review
- TypeScript/JavaScript review
- database/SQL review
- Docker/container debugging
- CI failure analysis
- dependency upgrade
- migration review
- E2E testing
- accessibility review
- performance/profiling
- architecture/system design

선택 MCP 후보:

- Chrome DevTools 계열 browser debugging MCP

조건부 Agent 후보:

- security verifier
- final verifier
- research worker

## 6. 제외/보류

초기 V8.1 Core에는 다음을 넣지 않습니다.

- 상시 Multi-Agent topology
- 모든 MCP 기본 연결
- 모든 Skill 전역 활성화
- 자동 학습 결과의 전역 Skill 승격
- Human 승인 없는 credential/external-write/destructive capability 활성화
- LangChain/LlamaIndex/AutoGen 같은 별도 Agent runtime의 Core dependency화

## 7. 성공 기준

V8.1은 기능 개수가 많아졌다는 이유로 성공이 아닙니다.

최소 성공 조건:

- 평균 활성 Skill 수 `<= 2`
- 대부분의 Task에서 MCP `0`
- 대부분의 Task에서 Agent `0`
- false activation `< 10%`
- critical missed activation `< 5%`
- task success와 verification success가 V8 이상
- permanent context 증가 `<= 5%`
- 실제 Windows install/update/uninstall/reinstall PASS
