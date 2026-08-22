# V8.1 평가 계획 - V8 vs V8.1

상태: **Integration verified / quantitative comparison pending**

> CAP-001 ~ CAP-008의 기능·Windows 통합 검증은 완료되었습니다. 아래의 대규모 fixture 기반 V8 대비 토큰/성공률 정량 비교는 후속 평가 단계입니다. 실행하지 않은 항목은 PASS로 간주하지 않습니다.

## 1. 목적

V8.1이 Capability 수를 늘리면서도 실제로 Context/토큰 효율과 품질을 유지하거나 개선하는지 V8과 비교합니다.

기능 수가 늘었다는 사실은 성공 기준이 아닙니다.

## 2. 주요 지표

### Context / Cost

- permanent global context bytes
- estimated permanent tokens
- registry metadata bytes loaded
- selected capability metadata count
- selected capability body count
- MCP tool schema exposure
- Agent spawn count

### Routing quality

- selected capability count
- false activation
- missed activation
- critical missed activation
- overlap/redundant activation
- Human Gate precision

### Task quality

- task success
- repository verification success
- Quality Gate result
- regression count
- evidence completeness

### Runtime

- routing latency
- total execution latency
- external process/tool calls
- MCP calls
- Agent calls

## 3. 초기 목표값

V8.1 Release Gate 목표:

```text
Global context increase        <= 5%
average selected skills        <= 2
median MCP count               = 0
median Agent count             = 0
false activation               < 10%
critical missed activation     < 5%
task success                   >= V8
verification success           >= V8
```

## 4. Task Fixture 구성

최소 30개 고정 fixture를 목표로 합니다.

### Trivial / low risk - 5

예:
- README typo
- 변수명 한 곳 수정
- 명확한 config 설명 변경
- 작은 isolated formatting
- 주석 수정

기대:
- Capability 0개 또는 최대 1개
- MINIMAL
- MCP/Agent 0

### Python / backend - 5

예:
- Python bug fix
- FastAPI validation 변경
- parsing logic refactor
- unit test 추가
- API response contract 변경

### Testing / debugging - 5

예:
- failing unit test 원인 분석
- flaky test 조사
- regression reproduction
- root cause analysis
- integration verification

### Security - 3

예:
- JWT auth 변경
- secret handling
- authorization boundary 변경

기대:
- security capability 선택
- 보통 STRICT

### Web / E2E - 3

예:
- browser-only reproduction
- form interaction E2E
- network/console debugging 필요 판단

### Database / migration - 2

예:
- read query tuning
- schema migration review

### DevOps - 3

예:
- Docker build failure
- CI workflow failure
- dependency upgrade

### Architecture / research - 4

예:
- architecture decision review
- dependency 선택 비교
- public API contract 변화
- 병렬 research 가능 작업

총 30개.

## 5. Fixture Schema

`harness/evaluation/fixtures.json` 초기 형태:

```json
{
  "id": "SEC-001",
  "task": "JWT 인증 로직 변경을 검토하고 테스트하라",
  "signals": {
    "files": ["app/auth.py", "tests/test_auth.py"]
  },
  "expected": {
    "must_include": ["security-review"],
    "may_include": ["testing", "code-review"],
    "must_exclude_types": ["mcp", "agent"],
    "profile": "strict"
  }
}
```

초기 P0에서는 실제 LLM Task 성공률보다 deterministic router selection correctness부터 검증합니다.

## 6. 단계별 Eval

### Eval A - Registry validation

- schema valid
- duplicate id rejection
- invalid enum rejection
- invalid path rejection
- source/license metadata 확인

### Eval B - Deterministic routing

- obvious domain match
- zero-capability task
- overlap resolution
- selection limit
- risk/profile recommendation

### Eval C - Negative cases

- irrelevant security trigger로 false activation 방지
- MCP가 단순 웹 작업에 자동 선택되지 않음
- Agent가 일반 code review에 자동 선택되지 않음
- credential/external-write capability가 자동 승인되지 않음

### Eval D - Windows integration

- V8 -> V8.1 install
- verify-install PASS
- Harness Audit PASS
- no-op reinstall
- uninstall preservation
- reinstall recovery

### Eval E - V8 vs V8.1

같은 fixture set에서 비교:

- fixed context
- routing selection
- capability count
- verification quality
- latency

## 7. Release 판단

다음 중 하나라도 발생하면 V8.1 main merge를 보류합니다.

- permanent global context > 5% 증가
- critical missed activation >= 5%
- security/credential capability 자동 활성화 오류
- trivial task에서 반복적으로 불필요한 MCP/Agent 선택
- V8보다 task/verification success 악화
- uninstall이 사용자 소유 설정을 훼손

## 8. Evidence 기록

실제 실행하지 않은 항목은 PASS로 기록하지 않습니다.

각 검증은 최소 다음을 남깁니다.

- command
- exit code
- observed output summary
- fixture id
- expected vs actual
- PASS / FAIL / UNVERIFIED
