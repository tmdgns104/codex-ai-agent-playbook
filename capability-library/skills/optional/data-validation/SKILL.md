---
name: data-validation
description: schema, nullable, range, uniqueness, categorical domain과 cross-field invariant로 데이터 품질 계약을 검증할 때 사용합니다.
---

# Data Validation

일반 unit test보다 데이터 자체의 계약과 품질 invariant를 명시하고 잘못된 sample을 Evidence로 남기는 데 집중합니다.

## When to use

- schema/type/nullability 규칙 정의
- 범위, uniqueness, categorical domain 검증
- 여러 column 사이의 cross-field invariant 검증
- invalid row/sample을 재현 가능한 형태로 분리해야 할 때

## Workflow

1. 데이터가 만족해야 할 계약을 schema와 invariant로 적습니다.
2. null/range/unique/domain 규칙을 각각 독립적으로 검사합니다.
3. 실패 row 수와 대표 sample을 민감정보 없이 보존합니다.
4. transform 전후 같은 invariant를 필요한 지점에서 재검사합니다.
5. 전체 PASS가 아니라 어떤 규칙이 몇 건 실패했는지 보고합니다.

## Boundaries

- 일반 application unit/integration test 전체를 대신하지 않습니다.
- 탐색·통계 중심 작업은 `data-analysis-pandas` 영역입니다.
- API request validation만 필요한 경우 서버 framework 계약을 우선합니다.

## Evidence

검증 규칙, 실패 count, 안전하게 축약한 invalid sample, 실행 command와 결과를 기록합니다.

## Stop / Handoff

검증을 통과시키기 위해 데이터를 조용히 삭제·수정하거나 민감 row를 그대로 로그에 출력하지 않습니다.

## Source / Provenance

- source_id: `v8.3-internal`
- license: `repository`
- provenance: V8.3 Candidate Review의 데이터 품질 경계를 기반으로 새로 작성한 internal-original Skill입니다.
