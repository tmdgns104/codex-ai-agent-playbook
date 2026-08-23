# V8.3 Skill Batch 2 Selection

상태: **CANDIDATE REVIEW COMPLETE**

## 결론

20개 후보를 현재 Core 7개, Optional Skill 10개, Wrapper 2개와 비교했습니다.

결과:

- ACCEPT: 16
- MERGE: 1
- DEFER: 3
- REJECT: 0

이 단계에서는 ACTIVE registry를 변경하지 않았고, Global AGENTS / installer / semantic Router도 변경하지 않았습니다.

## Batch 2 구현 대상 16개

### Python / Runtime

1. `python-project-engineering`
   - Python 프로젝트 구조, pyproject, venv, package boundary, entry point
   - `dependency-upgrade`와 분리

2. `python-typing`
   - mypy/pyright/type hint/Protocol/TypedDict 등 타입 시스템 전문 workflow
   - `code-review`의 범용 검토와 분리

3. `async-python`
   - asyncio, cancellation, timeout, blocking boundary, task lifecycle
   - `resilient-error-handling`의 retry/fault tolerance와 분리

4. `powershell-windows`
   - Windows path, quoting, execution policy, CMD/PowerShell exit-code 규율
   - `github-ops`와 분리

### Backend / Integration

5. `fastapi-backend`
   - FastAPI/Pydantic/Uvicorn/framework-specific implementation
   - `api-design`은 계약 설계, 이 Skill은 구현 workflow

6. `api-client-integration`
   - 외부 REST/HTTP client, auth, pagination, timeout, schema drift
   - `documentation-lookup` / `resilient-error-handling`과 조합 가능

7. `configuration-management`
   - env/config/default/secret boundary를 runtime 공통 관점에서 관리
   - `security-review`와 역할 분리

### Data / Database

8. `data-analysis-pandas`
   - DataFrame/CSV/EDA/정제/집계 중심
   - `sql-optimization`과 분리

9. `data-validation`
   - schema/range/null/unique/invariant 기반 데이터 품질 검증
   - 범용 `testing`과 분리

10. `etl-data-pipeline`
    - extract/transform/load, checkpoint, idempotent load, lineage
    - ad-hoc 분석과 분리

11. `database-schema-migration`
    - schema evolution, backward compatibility, rollback, data migration
    - `sql-optimization`과 명확히 분리

### Delivery / Operations

12. `ci-cd-workflow`
    - GitHub Actions 등 CI graph, cache, artifact, deploy gate
    - `testing` / `github-ops`와 분리

13. `observability-logging`
    - structured logging, metrics, tracing, correlation id
    - `root-cause-debugging`은 진단, 이 Skill은 telemetry 설계

14. `git-conflict-resolution`
    - merge/rebase conflict의 semantic resolution과 test preservation
    - normal Git delivery인 `github-ops`와 분리

### Code Quality / Tooling

15. `refactoring`
    - behavior-preserving change sequencing + regression evidence
    - `code-review`는 탐지, `refactoring`은 실제 변경

16. `cli-development`
    - command/subcommand, stdout/stderr, exit code, scriptability, CLI tests
    - PowerShell 사용법 자체와 분리

## MERGE 1개

### `architecture-review`

현재는 별도 Optional Skill로 만들지 않습니다.

이유:

- `ai-agent-development-playbook`의 문제정의 → 요구사항 → 아키텍처 → Task 흐름과 강하게 겹침
- 별도 Skill을 추가하면 `code-review`와도 trigger overlap이 커질 가능성이 있음

후속으로 Core playbook의 reference 보강 후보로 둡니다.

## DEFER 3개

### `websocket-realtime`

전문성은 있으나 범용 빈도가 상대적으로 낮습니다.

먼저 `async-python` + `resilient-error-handling`을 사용한 뒤 실제 Gap Event가 반복될 때 별도 Skill로 승격합니다.

### `release-packaging`

독립적인 가치가 있지만 `network` + `external_write` 위험이 있습니다.

`ci-cd-workflow`와 `github-ops`를 먼저 안정화한 뒤 Human Gate를 포함한 별도 release contract로 다룹니다.

### `documentation-maintenance`

유용하지만 현재 `documentation-lookup`, `human-readable-code`, `guide-ppt-creator`와 trigger 경계가 넓습니다.

실제 Gap Event를 보고 README/runbook/migration-note 중심으로 범위를 좁힌 뒤 재평가합니다.

## Source / License 정책

이번 16개 ACCEPT 후보는 **internal-original**을 기본으로 합니다.

외부 repository에서 코드를 그대로 복사하지 않습니다.

Agent Skills open standard는 package 형식과 progressive-disclosure 개념 참고에 사용합니다.

외부 Skill repository를 참고할 경우에는 구현 Task에서 각 Skill별로:

- source URL
- license
- adaptation 방식
- script/assets 포함 여부

를 별도로 기록합니다.

license가 불명확하면 ACTIVE로 구현하지 않습니다.

## 구현 순서

16개를 한 번에 구현하지 않습니다.

### Batch 2A - 기반/고빈도

- python-project-engineering
- powershell-windows
- api-client-integration
- configuration-management
- data-analysis-pandas
- data-validation
- ci-cd-workflow
- refactoring

### Batch 2B - 전문/중간 빈도

- python-typing
- async-python
- fastapi-backend
- etl-data-pipeline
- database-schema-migration
- observability-logging
- git-conflict-resolution
- cli-development

각 sub-batch마다 Candidate Audit + protected routing regression + STRICT Quality Gate를 통과한 뒤 다음 묶음으로 넘어갑니다.

## 다음 Task 제안

`V8.3-SKILL-002`에서 Batch 2A 8개 Skill package와 registry metadata를 구현합니다.

단, 처음부터 ACTIVE promotion을 묶어 처리하지 않고 8개 Candidate를 생성한 뒤 audit/regression을 통과한 항목만 ACTIVE로 승격하는 기존 V8.2 Governance를 그대로 사용합니다.
