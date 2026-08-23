---
name: performance-profiling
description: latency, throughput, CPU, memory, hot path처럼 실제 성능 병목을 baseline과 profiler로 찾고 before/after 수치로 개선을 검증할 때 사용합니다.
---

# Performance Profiling

성능 개선은 **측정 없이 시작하지 않습니다.** 먼저 목표 metric과 baseline을 정하고 profiler로 가장 큰 병목을 찾은 뒤 한 가지씩 바꿉니다.

## 언제 사용

- endpoint/job/page가 느림
- CPU 또는 memory 사용량이 큼
- latency/p95/p99/throughput 개선
- memory leak / excessive allocation 조사
- 성능 회귀 확인
- benchmark/profiling이 필요한 최적화

## 기본 흐름

1. 사용자가 체감하거나 요구한 primary metric을 하나 정합니다.
2. 재현 가능한 input/data 규모와 실행 조건을 만듭니다.
3. 변경 전 baseline을 여러 번 측정합니다.
4. 언어/runtime에 맞는 profiler로 hot path를 찾습니다.
5. 가장 큰 비용 하나를 분류합니다.
   - 불필요한 작업
   - 알고리즘 복잡도
   - I/O / DB round-trip
   - allocation / memory pressure
   - lock/concurrency
   - serialization/network
6. 가장 작은 효과적인 변경 하나를 적용합니다.
7. 동일 조건으로 다시 측정하고 correctness test도 유지되는지 확인합니다.
8. 효과가 없으면 복잡한 최적화를 남기지 않고 다시 profile합니다.

## 최적화 우선순위

```text
불필요한 작업 제거
-> 알고리즘/자료구조
-> I/O/DB batching
-> allocation/memory
-> concurrency/parallelism
-> low-level micro optimization
```

병렬화는 잘못된 알고리즘을 숨기는 첫 수단이 아닙니다.

## 원칙

- 평균만 보지 말고 문제 성격에 따라 tail latency도 확인
- debug build 결과를 production 성능으로 단정하지 않음
- benchmark 조건을 before/after 동일하게 유지
- 한 번에 한 변수만 바꿔 attribution 가능하게 함
- 빠르지만 결과가 틀린 변경은 실패
- SQL이 실제 병목으로 확인되면 `sql-optimization`을 사용

## 하지 말 것

- profiler 없이 감으로 hot path 결정
- 단일 실행 시간 하나로 개선 주장
- 근거 없는 cache/parallelism 추가
- 미세 최적화 때문에 코드/계약을 불필요하게 복잡하게 만듦
- 측정되지 않은 퍼센트 개선을 보고

## Evidence

최소 기록:

```text
primary metric / 목표
baseline 조건과 수치
profiler 또는 측정 근거
변경한 병목
before -> after 수치
correctness verification
남은 성능 gap
```

## Stop / Handoff

- DB query가 병목이면 `sql-optimization`으로 좁힙니다.
- 외부 service latency가 원인이면 `resilient-error-handling`의 timeout/retry 정책과 혼동하지 않습니다.
- production profiling/credential/network 접근은 별도 Gate 대상입니다.

## Source

MIT 라이선스 `JayRHa/AgentSkills`의 `performance-profiler`에서 measure-first, hot-path profiling, one-change-at-a-time, before/after verification 패턴을 참고했습니다. 특정 profiler 도구를 강제하지 않고 Repository 실행 환경에 맞게 재작성했습니다.
