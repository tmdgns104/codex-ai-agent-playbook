# V8.4-EXPERT-CONTEXT-007 - Controlled Benchmark Policy and Frozen Holdout

상태: **POLICY COMPLETE - EXECUTION BLOCKED BY REAL TRANSPORT**

## 목적

V8.4 RC promotion gate에서 아직 비어 있는
`native_vs_playbook_controlled_comparison`과 `generalization_holdout`을
검증하기 위한 benchmark 정책과 holdout을 실행 전에 고정한다.

이 Task는 **모델 benchmark를 실행하지 않는다.**
V8.4-006A에서 current Codex CLI의 separate verified-context transport가
`unsupported`로 판정됐으므로 `adapted-on-demand` 실제 실행은 아직 허용되지 않는다.

## Frozen experiment

Variants:

1. `native-no-playbook`
2. `current-playbook`
3. `raw-reference-diagnostic` - 진단 전용, promotion 판정 직접 사용 금지
4. `adapted-on-demand`

Promotion 비교의 핵심은 같은 backend/model/runtime에서
`native-no-playbook`, `current-playbook`, `adapted-on-demand`를 비교하는 것이다.

## Holdout

- 12 frozen tasks
- 4 categories
- 2 approved candidates only
  - `kd-sympy`
  - `kd-citation-management`
- variant당 3 repeats
- 기존 development fixture `bench004-*`와 다른 `v84007-h*` ID 사용
- 각 task text SHA-256 고정
- freeze 이후 holdout 결과를 보고 context/selector/prompt/policy를 튜닝하면 해당 holdout은 무효

공개 Repository에 fixture가 있기 때문에 “비밀 test set”이라고 주장하지 않는다.
대신 결과를 보기 전에 정책·task·hash를 고정한 **pre-registered holdout**으로 사용한다.

## Promotion thresholds

기존 `evaluation/promotion/promotion_policy_v1.json`을 변경하지 않고 그대로 따른다.

- adapted quality delta vs native >= 0
- adapted latency / native <= 1.15
- adapted prompt tokens / native <= 1.15
- adapted context bytes / current <= 0.75
- holdout tasks >= 12
- task categories >= 4
- repeats per variant >= 3
- safety / permission / integrity hard gate = 100%

추가 V8.4 설계 조건:
- adapted는 candidate별 current-playbook 대비 non-inferior여야 함
- missing/invalid metric은 PASS로 보간하지 않음
- 같은 비교 안에서 backend/model/runtime를 바꾸지 않음
- raw-reference는 diagnostic 전용

## Preflight result

```text
fixture_count: 12
category_count: 4
candidate_count: 2
repeats_per_variant: 3
policy_frozen: true
holdout_frozen: true
preflight: PASS
execution_state: EXECUTION_BLOCKED_BY_TRANSPORT
```

Unit tests: **5/5 PASS**

검증:
- minimum holdout shape 충족
- transport false에서 실제 execution 차단
- task hash tamper 차단
- 승인되지 않은 candidate 차단
- development fixture ID overlap 차단

## 현재 gate 상태

이 Task 완료로 benchmark **정책과 holdout 준비**는 끝났지만 실제 결과 Evidence는 아직 없다.

- `transport_conformance = false`
- `native_vs_playbook_controlled_comparison = false`
- `generalization_holdout = false`
- `candidate_approval = false`

따라서 main promotion은 계속 `NOT_READY`다.

## 다음 실행 조건

실제 controlled benchmark는 다음 조건이 모두 충족된 후에만 시작한다.

1. `SEPARATE_VERIFIED_CONTEXT_V1`을 실제 지원하는 backend adapter Evidence
2. transport conformance gate PASS
3. 동일 backend/model/runtime를 세 variant에 고정
4. frozen holdout과 policy hash 확인
5. 외부 network/API/credential 없이 승인된 runtime 사용
6. 결과 실패/누락을 그대로 기록

Candidate approval은 benchmark 결과와 별개의 Human promotion gate로 유지한다.
