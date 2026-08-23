---
name: resilient-error-handling
description: timeout, retry, backoff, idempotency, circuit breaker, graceful degradation처럼 외부 실패 경계를 견고하게 설계할 때 사용합니다.
---

# Resilient Error Handling

이 Skill은 일반 버그의 `오류`를 잡는 용도가 아닙니다. **network/DB/external API/process처럼 실패할 수 있는 경계에서 실패 의미와 복구 정책을 설계**할 때 사용합니다.

## 언제 사용

- retry/backoff/jitter 정책 설계
- timeout/deadline 누락
- transient/permanent failure 분류
- circuit breaker / graceful degradation
- 외부 write의 idempotency 검토
- 예외를 삼키거나 무한 retry하는 코드 검토

## 기본 흐름

1. operation이 실패할 수 있는 경계를 식별합니다.
2. failure mode를 transient / permanent / ambiguous로 분류합니다.
3. 각 failure의 owner를 정합니다: handle, transform, propagate 중 하나.
4. remote/IO call에는 합리적인 timeout 또는 deadline을 둡니다.
5. retry는 retryable failure에만, 횟수와 총 시간을 제한해 적용합니다.
6. retry 가능한 write는 idempotent인지 먼저 확인합니다.
7. dependency가 반복 실패할 때 circuit breaker/degradation이 필요한지 판단합니다.
8. error context와 원래 cause를 보존합니다.
9. timeout/5xx/connection failure 같은 실패 path를 focused test로 검증합니다.

## Retry 원칙

- validation/auth/permission 같은 permanent error를 반복 retry하지 않음
- exponential backoff + jitter를 기본 후보로 고려
- `Retry-After` 같은 server signal이 있으면 존중
- max attempts와 overall deadline 없이 retry loop를 만들지 않음
- timeout된 write는 실제 적용 여부가 불명확할 수 있으므로 idempotency/reconciliation 필요

## 원칙

- 빈 `except`/`catch`로 실패를 숨기지 않음
- user-facing error와 internal diagnostic을 분리
- error를 여러 layer에서 중복 log하지 않도록 owner를 명확히 함
- cleanup/resource release가 모든 path에서 일어나는지 확인
- resilience pattern을 단순 local validation 코드에 과도하게 적용하지 않음

## 하지 말 것

- 일반 `error`/`오류` 하나만 보고 이 Skill을 선택
- 모든 5xx를 무제한 retry
- non-idempotent external write를 근거 없이 재시도
- timeout을 임의 숫자로 hard-code하고 근거 없이 최적값이라고 주장
- circuit breaker를 필요성 없이 기본 구조로 추가

## Evidence

최소 기록:

```text
failure boundary
transient/permanent/ambiguous 분류
retry/timeout/idempotency 결정과 근거
실행한 failure-path test와 exit code
관찰 가능한 fallback/degradation 결과
남은 external dependency risk
```

## Stop / Handoff

- credential/external write/database write가 포함되면 Permission/Human Gate가 우선입니다.
- 실제 일반 버그의 root cause 조사라면 `root-cause-debugging`을 사용합니다.
- auth/authz 실패 정책은 `security-review`와 함께 검토합니다.

## Source

MIT 라이선스 `JayRHa/AgentSkills`의 `error-handling-patterns`에서 failure classification, bounded retry, timeout/deadline, idempotency, circuit breaker와 degradation 패턴을 참고했습니다. 일반 오류 trigger와 과도한 자동 resilience 도입을 제거하고 V8.1의 좁은 자동 선택 정책에 맞게 재작성했습니다.
