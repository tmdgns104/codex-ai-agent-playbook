# V8.4-EXPERT-CONTEXT-006 - Context Materializer and Launch Coordinator

상태: **COMPLETE**

## Problem

V8.4-001~005는 adapted context의 설계, 분리 transport 계약, schema/validator,
offline compiler, selector와 budget planner를 확정했다. 그러나 선택 결과를 다른
session과 섞이지 않는 artifact로 만들고, launch 직전에 source/definition/unit/hash/
permission/budget/backend capability를 다시 검증하며, 종료 시 해당 session만 정리하거나
격리하는 계층은 없었다.

이 Task는 실제 backend나 launcher에 연결하지 않는 순수 control-plane 구현으로 그 공백을
메운다. 여기서 `READY`와 `launch_allowed=true`는 fake backend 계약에 대한 pre-launch
검증 완료만 뜻하며 process spawn이나 context injection이 수행됐다는 의미가 아니다.

## Requirements

1. `ContextLaunchRequest v1`, approved Definition, V8.4-005 selection/budget/permission
   결과와 session ID만 입력 authority로 사용한다.
2. repository 내부의 dedicated sessions root와 고유 session directory만 사용한다.
3. path normalization, containment, symlink, duplicate session, source snapshot 경로와 hash를
   fail closed로 검증한다.
4. context JSONL, Runtime Context Envelope, manifest를 canonical UTF-8 bytes로 기록하고
   SHA-256 및 read-only mode로 고정한다.
5. request/task/context/source/definition/unit/budget/permission/probe/injection/freshness를
   launch 직전에 다시 검증한다.
6. lifecycle은 `CREATED`, `VALIDATED`, `MATERIALIZED`, `READY`, `CLEANUP_PENDING`,
   `CLEANED`, `INVALIDATED`, `QUARANTINED`만 허용하고 illegal transition을 거부한다.
7. 정상 cleanup은 manifest의 정확한 allowlist에 있는 context/envelope만 삭제하고 audit
   manifest/lifecycle/evidence는 남긴다. recursive session deletion은 하지 않는다.
8. 변조, stale, permission/path mismatch, unexpected file, malformed manifest, cleanup 실패는
   해당 session만 quarantine하며 자동 복구나 재사용을 허용하지 않는다.
9. optional adapted context의 `CURRENT_ONLY`는 injection attempt가 0인 경우에만 명시적으로
   기록한다. raw external Skill 또는 launcher v1 silent fallback은 금지한다.
10. 실제 backend, Codex, LLM, Ollama, benchmark, network/API/credential, hardware/cloud 동작은
    수행하지 않는다.

## Architecture impact

- 새 구현은 `evaluation/external-skills/context-materializer/` 아래의 독립 evaluation 계층이다.
- V8.4-003 canonical/hash/schema/permission/probe validator와 V8.4-005 selector output을
  import하여 재사용하되 기존 파일은 수정하지 않는다.
- `materializer.py`가 input validation, canonical envelope/manifest와 immutable artifact를
  소유한다.
- `coordinator.py`가 final pre-launch gates, explicit CURRENT_ONLY, failure classification을
  소유한다. backend/transport 호출 API는 존재하지 않는다.
- `lifecycle.py`가 허용 상태와 전이를 단일 표로 고정한다.
- `artifact_safety.py`와 `lifecycle_ops.py`가 containment, symlink 방어, cleanup과 quarantine을
  소유한다.
- Router/scoring, activation, Skill Materializer, Discovery Bridge, launcher, Registry,
  AGENTS/global policy는 변경하지 않는다.

## Deterministic flow

```text
ContextLaunchRequest + approved Definitions + selector/budget result
  -> session path and duplicate check
  -> CREATED
  -> schema/task/source/definition/unit/budget/permission validation
  -> VALIDATED
  -> canonical context + envelope + deterministic manifest
  -> read-only artifacts + MATERIALIZED
  -> fake probe + complete pre-launch revalidation
  -> READY (no backend execution)
  -> CLEANUP_PENDING -> CLEANED

Any integrity/safety failure
  -> INVALIDATED when stale
  -> QUARANTINED with session-scoped evidence
```

## Lifecycle transitions

| Current | Allowed next |
|---|---|
| `CREATED` | `VALIDATED`, `INVALIDATED`, `QUARANTINED` |
| `VALIDATED` | `MATERIALIZED`, `INVALIDATED`, `QUARANTINED` |
| `MATERIALIZED` | `READY`, `INVALIDATED`, `QUARANTINED` |
| `READY` | `CLEANUP_PENDING`, `INVALIDATED`, `QUARANTINED` |
| `CLEANUP_PENDING` | `CLEANED`, `QUARANTINED` |
| `INVALIDATED` | `QUARANTINED` |
| `CLEANED`, `QUARANTINED` | terminal |

## Files

```text
evaluation/external-skills/context-materializer/
  artifact_safety.py
  coordinator.py
  lifecycle.py
  lifecycle_ops.py
  materializer.py
  policy/context-materializer-policy-v1.json
  tests/fixture_factory.py
  tests/test_materializer.py
  tests/test_protected_artifacts.py
evaluation/external-skills/reports/v8.4-materializer-summary.json
tasks/V8_4-EXPERT-CONTEXT-006.md
```

## Acceptance matrix

| Acceptance | Status | Evidence |
|---|---|---|
| session isolation | PASS | duplicate and two-session quarantine tests |
| path containment | PASS | outside sessions root and envelope escape tests |
| symlink defense | PASS | deterministic symlink-component fixture |
| hash integrity | PASS | context/envelope/manifest/source/unit hash tests |
| strongest permission gate | PASS | downgrade fixture and both candidate gates |
| budget enforcement | PASS | required-only overflow returns `BUDGET_BLOCKED` |
| lifecycle transition | PASS | complete normal chain and illegal skip test |
| cleanup | PASS | exact allowlist cleanup and retained audit evidence |
| quarantine | PASS | mismatch, stale, extra file, malformed manifest, cleanup failure |
| deterministic rebuild | PASS | context/envelope/manifest byte identity |
| no raw fallback | PASS | raw fallback fixture rejected |
| no silent fallback | PASS | explicit pre-injection CURRENT_ONLY only |
| malformed/stale fail closed | PASS | schema/malformed/stale fixtures |

## Result

- New materializer/coordinator tests: 26 PASS, 0 FAIL.
- SymPy fixture: 4 required units, 1,202 UTF-8 bytes, `NETWORK_REVIEW`, `READY`.
- Citation fixture: 5 units, 1,670 UTF-8 bytes, `HUMAN_GATE_REQUIRED`, `READY`.
- Approved test-only composition: 8 required units, 2,562 UTF-8 bytes,
  `HUMAN_GATE_REQUIRED`, `READY`.
- Normal lifecycle is `CREATED -> VALIDATED -> MATERIALIZED -> READY ->
  CLEANUP_PENDING -> CLEANED`.
- Cleanup failure enters `QUARANTINED`; stale artifact records `INVALIDATED -> QUARANTINED`.
- Runtime/backend/transport/LLM/Ollama/benchmark/external access execution is zero.
- Final regression, protected hashes, JSON validity, diff and Git completion evidence are recorded in
  `evaluation/external-skills/reports/v8.4-materializer-summary.json`.
