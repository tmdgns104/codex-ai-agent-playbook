---
name: sql-optimization
description: 느린 SQL, execution plan, index, full scan, N+1처럼 데이터베이스 query 성능을 실제 측정과 plan 근거로 개선할 때 사용합니다.
---

# SQL Optimization

SQL 최적화는 추측이 아니라 **baseline → execution plan → 가장 큰 비용 → 한 가지 변경 → 재측정** 순서로 진행합니다.

## 언제 사용

- 느린 query / timeout / full table scan
- EXPLAIN / EXPLAIN ANALYZE 해석
- index 추가·변경 검토
- ORM N+1 또는 과도한 round-trip 분석
- query rewrite와 DB 성능 회귀 검토

## 기본 흐름

1. DB engine/version, query, schema, row 규모, 기존 index를 확인합니다.
2. 가능한 경우 실제 execution plan과 baseline timing을 수집합니다.
3. dominant cost와 estimated/actual row 차이를 찾습니다.
4. 원인을 분류합니다.
   - 불필요한 scan
   - 잘못된/누락된 index
   - non-sargable predicate
   - stale statistics
   - N+1 / excessive round-trip
   - sort/hash/spill
   - 과도한 result set
5. 가장 작은 변경 하나를 적용합니다.
6. 같은 조건으로 plan과 timing을 다시 측정합니다.
7. 개선이 없으면 변경을 유지하지 않고 원인을 재평가합니다.

## 원칙

- plan 없이 index부터 추가하지 않음
- query와 data 규모에 맞는 실제 Evidence를 우선
- composite index는 read 이득뿐 아니라 write/storage 비용도 검토
- `SELECT *`나 불필요한 row/column 이동을 hot path에서 피함
- ORM이면 SQL 횟수와 N+1 여부를 실제로 확인
- production write query의 `EXPLAIN ANALYZE`는 안전성을 확인하지 않고 실행하지 않음

## Database write 경계

Index 생성, schema 변경, statistics/config 변경은 단순 read-only 분석과 다릅니다.
이 Skill이 선택됐다는 이유만으로 DB write 권한이 생기지 않습니다.

## 하지 말 것

- 작은 개발 DB 결과만 보고 production 성능을 단정
- 모든 seq/full scan을 문제로 간주
- 근거 없이 index를 여러 개 추가
- 여러 최적화를 동시에 적용하고 어떤 변경이 효과였는지 잃어버림
- DB 변경을 Repository migration 계약 밖에서 수행

## Evidence

최소 기록:

```text
DB engine / query context
baseline timing 또는 plan
지배 비용 / root cause
적용한 단일 변경
before -> after 측정
write/storage/migration trade-off
```

## Stop / Handoff

- 실제 schema/index/database write가 필요하면 Human/Permission Gate를 확인합니다.
- 일반 애플리케이션 성능 문제라면 먼저 `performance-profiling`으로 병목 위치를 확정할 수 있습니다.
- 보안/권한이 query 조건에 포함되면 `security-review`로 넘깁니다.

## Source

MIT 라이선스 `JayRHa/AgentSkills`의 `sql-optimizer`에서 execution-plan-first, measure/change/re-measure, sargability와 index trade-off 패턴을 참고했습니다. V8.1의 권한 Gate와 최소 Evidence 흐름에 맞게 재작성했습니다.
