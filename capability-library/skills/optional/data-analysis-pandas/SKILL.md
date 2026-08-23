---
name: data-analysis-pandas
description: Pandas DataFrame과 CSV를 로드해 dtype, null, duplicate를 점검하고 재현 가능한 EDA·집계·정제를 수행할 때 사용합니다.
---

# Data Analysis with Pandas

원본 데이터를 보존하면서 DataFrame 기반 탐색·정제·집계 과정을 재현 가능하게 만듭니다.

## When to use

- Pandas/DataFrame으로 CSV 또는 표형 데이터를 분석할 때
- dtype, null, duplicate, 범주값을 먼저 점검해야 할 때
- EDA, groupby/aggregation, 요약 통계를 만들 때
- 분석용 transformation과 원본 파일을 분리해야 할 때

## Workflow

1. 원본 경로, row/column 수, dtype부터 확인합니다.
2. null/duplicate와 명백한 형식 이상을 요약합니다.
3. 질문에 필요한 최소 transformation만 단계적으로 적용합니다.
4. 집계 전후 row count와 key invariant를 확인합니다.
5. 코드/노트북으로 다시 실행 가능한 결과와 해석을 분리해 남깁니다.

## Boundaries

- production ETL orchestration은 별도 `etl-data-pipeline` 후보 영역입니다.
- DB 실행계획/인덱스 튜닝은 `sql-optimization` 영역입니다.
- 데이터 계약 자체를 엄격히 검증하는 작업은 `data-validation`과 구분합니다.

## Evidence

입력 shape/dtype, 품질 요약, transformation 단계, 핵심 집계 결과와 재현 방법을 기록합니다.

## Stop / Handoff

원본을 덮어써야 하거나 개인정보/민감 데이터 외부 전송이 필요하면 진행하지 않습니다.

## Source / Provenance

- source_id: `v8.3-internal`
- license: `repository`
- provenance: V8.3 Candidate Review의 Pandas 분석 경계를 기반으로 새로 작성한 internal-original Skill입니다.
