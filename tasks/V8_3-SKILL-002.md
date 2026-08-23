# V8.3-SKILL-002 - Batch 2A Optional Skill Implementation

상태: **READY FOR IMPLEMENTATION**

선행 조건:

- V8.3-SKILL-001 — COMPLETE - VERIFIED
- `V8_3_SKILL_BATCH2_SELECTION.md` — CANDIDATE REVIEW COMPLETE

## 목적

Batch 2A의 고빈도 Optional Skill 8개를 V8.2 Capability Library 계약에 맞는 Candidate package로 구현하고, Audit / Router regression / STRICT Quality Gate를 통과한 항목만 ACTIVE registry에 승격합니다.

## 구현 대상 8개

```text
python-project-engineering
powershell-windows
api-client-integration
configuration-management
data-analysis-pandas
data-validation
ci-cd-workflow
refactoring
```

## 구현 위치

각 Skill은 기본적으로 다음 구조를 사용합니다.

```text
capability-library/skills/optional/<skill-id>/
  SKILL.md
  references/      # 필요한 경우만
  scripts/         # deterministic helper가 꼭 필요한 경우만
```

script가 없어도 충분한 Skill은 SKILL.md + references만 사용합니다.

## 공통 metadata 계약

각 Skill은 registry에 최소 다음 정보를 가져야 합니다.

```text
id
type=skill
summary
domains
triggers
activation=on_demand
risk
recommended_profile
permissions
context_cost
dependencies
source_id
license
path
```

## Skill별 경계

### python-project-engineering

포함:

- pyproject.toml / package layout
- venv / interpreter consistency
- entry point
- src layout 여부 판단
- test/lint/type tool placement
- 작은 프로젝트에서 과도한 구조화 금지

제외:

- dependency version upgrade 자체
- FastAPI framework 세부 구현
- type checker 전문 수정

### powershell-windows

포함:

- CMD vs PowerShell 차이
- quoting / escaping
- Windows path
- execution policy
- ERRORLEVEL / exit code
- UTF-8 / BOM 주의

제외:

- GitHub workflow 자체
- 일반 Linux shell skill

### api-client-integration

포함:

- HTTP client boundary
- auth injection
- timeout
- retry는 resilient-error-handling과 연결
- pagination
- response schema drift
- mock/fake/test boundary

제외:

- server-side API contract 설계
- 공식 문서 조회 그 자체

### configuration-management

포함:

- environment variables
- config files
- defaults/override precedence
- secret value를 문서/로그에 남기지 않는 경계
- dev/test/prod 차이

제외:

- secret rotation 전문 보안 작업

### data-analysis-pandas

포함:

- CSV/DataFrame load
- dtype/null/duplicate 점검
- summary/aggregation
- reproducible transformation
- 분석 결과와 원본 분리

제외:

- 생산 ETL orchestration
- SQL runtime tuning

### data-validation

포함:

- schema
- nullable
- range
- uniqueness
- categorical domain
- cross-field invariant
- invalid sample evidence

제외:

- 일반 unit test 전체

### ci-cd-workflow

포함:

- build/test job
- cache
- artifact
- least privilege
- secret masking
- branch/PR gate
- deploy는 명시적 gate 뒤에만

제외:

- Git commit/push/PR 조작 자체
- release publication 자동화

### refactoring

포함:

- behavior-preserving change
- characterization/focused regression
- small-step change
- rename/extract/move/simplify
- before/after evidence

제외:

- feature scope expansion
- review-only task

## Source 정책

이번 Batch 2A는 `internal-original` 구현을 기본으로 합니다.

Agent Skills 표준은 package 형식 참고만 합니다.

외부 repository에서 구체적인 문장/코드/script를 가져오는 경우에만 별도 source_id와 license를 추가합니다.

license가 불명확한 외부 code/assets는 사용하지 않습니다.

## Trigger 품질

기존 installed audit WARN을 늘리지 않는 것이 목표입니다.

각 Skill에 대해:

- broad token 하나만으로 trigger하지 않기
- 가능한 phrase trigger 우선
- negative/exclusion intent를 SKILL.md에 명시
- `testing`, `code-review`, `root-cause-debugging`, `github-ops`와 경계 확인

## 구현 순서

1. 8개 Candidate package 작성
2. registry Candidate metadata 작성
3. Skill Audit
4. Router fixture 추가/갱신
5. protected routing regression
6. materializer/discovery/launcher regression
7. STRICT Quality Gate
8. Candidate validation
9. PASS 항목만 ACTIVE promotion
10. Windows install / verify / reinstall

## 필수 테스트

최소:

```text
Capability Router
Capability Manager
Skill Materializer
Discovery Bridge
Playbook Launcher
Skill Audit
V8.2 Governance tests
Creator/Evolver/Curator regression
Lifecycle integration/control-plane tests
Harness Audit
STRICT Quality Gate
```

추가로 Batch 2A routing fixture를 만들어 각 신규 Skill이 최소:

```text
positive case 2개
negative / overlap case 1개
```

이상을 가져야 합니다.

8개 Skill이면 신규 routing case 최소 24개입니다.

## Acceptance Criteria

1. 8개 package 존재
2. 8개 SKILL.md metadata parse PASS
3. registry id/path 일치
4. duplicate id 0
5. permission expansion Human Gate 위반 0
6. 신규 routing positive case PASS
7. 기존 routing regression PASS
8. Skill Audit FAIL 0
9. 기존 WARN을 무근거로 숨기지 않음
10. STRICT Quality Gate PASS
11. Global AGENTS 의미 있는 증가 없음
12. install PASS
13. verify PASS
14. same-version reinstall PASS
15. arbitrary Git repository dry-run에서 불필요 mutation 없음
16. final working tree clean

## 금지

- Batch 2B까지 같이 구현
- Core 7개 변경
- semantic/embedding Router 추가
- 외부 Skill bulk copy
- raw task text 저장
- release-packaging 구현
- WebSocket 전용 Skill 구현
- documentation-maintenance 구현
- Human Gate 완화

## 완료 후

`V8.3-SKILL-003`에서 Batch 2B 8개를 같은 방식으로 구현합니다.
