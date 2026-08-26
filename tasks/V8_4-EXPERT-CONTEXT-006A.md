# V8.4-EXPERT-CONTEXT-006A - Transport Conformance Feasibility Simulation

상태: **COMPLETE - REAL TRANSPORT GATE STILL BLOCKED**

## 목적

V8.4-002에서 고정한 `C_VERSIONED_OPT_IN_LAUNCHER_CONTRACT` /
`SEPARATE_VERIFIED_CONTEXT_V1` 계약에 대해 adapter conformance 분류를
추론 없이 검증한다.

이번 Task는 실제 backend feasibility를 **시뮬레이션으로만** 점검한다.
실제 Codex child 실행, 모델 호출, API, network, credential, production integration은
수행하지 않는다. 따라서 시뮬레이션 PASS를 실제 transport conformance PASS로
승격하지 않는다.

## 보존 경계

- V8.4-001~006 파일은 수정하지 않는다.
- 기존 Router/scoring, launcher, activation, Skill Materializer, Discovery Bridge,
  Registry, AGENTS/global policy는 수정하지 않는다.
- user task를 context와 합치지 않는다.
- exact task positional-once invariant를 유지한다.
- `--add-dir`를 separate verified context transport라고 가정하지 않는다.
- backend support가 입증되지 않으면 fail closed 한다.

## 분류 계약

`compatible`:
1. separate verified-context channel 지원
2. exact task once 보존
3. deterministic context binding
4. spawn 직전 hash/size/permission 검증
5. cleanup 통제
6. failure 통제

`partial`:
- separate context channel은 있지만 필수 검증/통제 중 일부가 누락됨

`unsupported`:
- separate verified-context channel 자체가 입증되지 않음

## 결과

| Adapter | 판정 | 의미 |
|---|---|---|
| `codex-cli-current` | `unsupported` | exact task 전달은 보존되지만 별도 verified-context channel Evidence 없음 |
| `simulated-separate-context-complete` | `compatible` | 모든 필수 조건을 갖춘 positive control |
| `simulated-separate-context-partial` | `partial` | final pre-spawn hash/size/permission 검증 누락 |

현재 Codex CLI의 `transport_conformance` promotion gate는 **false 유지**다.
Positive/partial control은 classifier가 fail-closed로 분류되는지 확인하기 위한
시뮬레이션 fixture이며 실제 backend 지원 Evidence가 아니다.

## 검증

```text
python -m unittest -v tests/test_conformance.py
Ran 5 tests
OK
```

검증 항목:
- complete fixture -> compatible
- separate channel 미지원 -> unsupported
- final verification 일부 누락 -> partial
- current Codex adapter -> unsupported 유지
- simulation이 model/API/network/production approval을 주장하지 않음

## Promotion 영향

006A에서 새로 충족된 것은 **분류 로직의 deterministic simulation**뿐이다.

- classifier simulation: PASS
- real `transport_conformance`: BLOCKED / false
- production transport approval: false

따라서 기존 V8.4 promotion gate의 다음 미충족 항목은 그대로 남는다.

1. 실제 transport conformance Evidence
2. `native_vs_playbook_controlled_comparison`
3. `generalization_holdout`
4. `candidate_approval`

실제 backend가 별도 verified-context channel을 제공한다는 Evidence가 생기기 전에는
context-enabled production launch를 활성화하지 않는다.
