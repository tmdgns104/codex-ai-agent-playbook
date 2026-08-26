# V8.4-EXPERT-CONTEXT-003 - Contract Schema and Deterministic Validator

상태: **COMPLETE**

## Problem

V8.4-001의 Adapted Capability Definition/Runtime Envelope 설계와 V8.4-002의 versioned opt-in Context Launch Contract를 실제 backend에 연결하기 전에, typed document와 문서 간 invariant를 LLM·network·backend 없이 재현 가능하게 검증할 계층이 필요하다.

## Requirements

1. Adapted Capability Definition, Runtime Context Envelope, ContextLaunchRequest v1, ContextLaunchResult v1, Backend Capability Probe v1의 Draft 2020-12 JSON Schema를 추가한다.
2. JSON을 UTF-8, key sort, compact separator, explicit null 보존, float/NaN 금지 규칙으로 canonical serialize하고 SHA-256을 계산한다.
3. Validator는 schema, task/context 분리, exact task, injection 0/1, backend false/unknown, source/envelope/content hash, session path/symlink, byte/token budget, permission strongest gate, required unit completeness, cache freshness, missing/unknown fail-closed를 검증한다.
4. Required-only overflow는 `BUDGET_BLOCKED`, stale cache는 `INVALIDATED`, cleanup failure는 `QUARANTINED`, 정상 fake backend는 `PASS`를 반환한다.
5. Fake fixture는 compliant와 false/unknown capability, malformed request, concatenation, duplicate injection, hash mismatch, permission downgrade, overflow, path escape, stale cache, cleanup failure를 포함한다.
6. 기존 normal v1 path의 exact-task regression과 기존 validation tests를 유지한다.

## Architecture impact

- 승인된 V8.4-001/002 경계 안의 isolated evaluation/control-plane validation 계층만 추가했다.
- 기존 launcher, Router/scoring, activation/materialization/discovery, Registry와 실제 backend integration은 변경하지 않았다.
- 새 dependency 없이 Python 표준 라이브러리와 `unittest`만 사용했다.
- JSON Schema instance validation은 이 다섯 schema가 명시적으로 사용하는 Draft 2020-12 subset만 지원하며, 지원하지 않는 keyword/format은 schema load 단계에서 거부한다.
- Fake backend는 deterministic receipt를 만드는 pure function이며 process, backend, LLM, Ollama, network, API, credential을 사용하지 않는다.

## Implemented files

```text
evaluation/external-skills/context-contract/
  schema/
    adapted-capability-definition-v1.schema.json
    runtime-context-envelope-v1.schema.json
    context-launch-request-v1.schema.json
    context-launch-result-v1.schema.json
    backend-capability-probe-v1.schema.json
  validator/
    schema_validation.py
    context_contract.py
    fake_backend.py
  tests/
    fixtures/compliant.json
    fixtures/failure-cases.json
    build_fixtures.py
    fixture_factory.py
    test_context_contract.py
    test_protected_artifacts.py
evaluation/external-skills/reports/v8.4-schema-validator-summary.json
tasks/V8_4-EXPERT-CONTEXT-003.md
```

## Deterministic contract

- Canonical JSON: UTF-8, lexicographically sorted object keys, compact separators, explicit `null`, no floating-point values.
- Hashes: canonical document SHA-256, task/context raw UTF-8 SHA-256, definition/unit/cache self-consistency hashes.
- Context: required knowledge units are assembled whole and in definition order as canonical JSON lines. Required units may not be truncated.
- Transport: task is a separate exact value and occurs exactly once in the request. Context-enabled PASS requires one injection attempt and one injection; `CURRENT_ONLY` requires zero.
- Backend: only a non-expired `SUPPORTED` probe with explicit separate task/context channels can pass context mode. `false`, `null`, `UNKNOWN`, missing, and internally inconsistent capability evidence fail closed.
- Permissions: current permissions, original adapted source permissions, retained permissions, existing required gates, and adapted effective gate are combined without downgrade; deterministic strongest gate wins.
- Path: only normalized POSIX-relative paths below the session-local `contexts/` directory are accepted. Absolute, drive, backslash, traversal, forbidden discovery locations, symlink components, and resolved escape are blocked.
- Budget/cache: exact UTF-8 bytes are always enforced. Token counts may be null only with null tokenizer and a non-empty reason. Required-only overflow is `BUDGET_BLOCKED`; stale cache is `INVALIDATED`.
- Result: backend-declared non-PASS cannot be promoted to validator PASS. Cleanup failure must be quarantined.

## Protected baseline and post-verification

The following pre-task SHA-256 values equal the final values:

| Artifact | SHA-256 |
|---|---|
| `tasks/V8_4-EXPERT-CONTEXT-001.md` | `bea3db0a7351a10358290b603b3cfe329190c379c364983ed9b8e652521c58fd` |
| `tasks/V8_4-EXPERT-CONTEXT-002.md` | `fb4b1d474572e54e6b5c0cf413d9de9f32e1486d00e5325ef532e377bc7be572` |
| `evaluation/external-skills/reports/v8.4-design-summary.json` | `6d29f8ae11aac29a5fd8d5cb2b03299e6213a9d5fa8940705b6ea47e70960548` |
| `evaluation/external-skills/reports/v8.4-transport-decision-summary.json` | `4fceb162f54f229f4579052bb65390cc73f643d7316e06910ad6bb1e89c4e176` |
| `evaluation/external-skills/benchmark-results.json` | `21cb7165c4e02397fdafa9bc5d20f715e723ff351965cf71e00e42f6e7e80249` |
| `evaluation/external-skills/adoption-decisions.json` | `4078ba8597bc9483606c41dcae2a88d5096de13ce22cb6c1084665079433bbe3` |
| `evaluation/external-skills/adapted-contexts.json` | `f972f89a57dd853eaf7f88648e8a5ce9f6a26f9335e6f03131a48222246e9816` |
| `evaluation/external-skills/reports/stage-b-failure-analysis.json` | `22f590325b312ec52b9ab54e889eff7f6c23eb0c3064229d738a4dada307c692` |
| `evaluation/external-skills/reports/stage-b-wave2-comparison.json` | `7566322a62064797df4fefbf0319794aab40b1cd66df8cec77c934047f031a6e` |
| `evaluation/external-skills/reports/stage-b-wave2-execution-summary.json` | `48ba11e17931c406fc8c1026727bb6dbbce58c2c52652c16e895b15fff7f3c9b` |
| `harness/router/capability_router.py` | `f6897fa59fa02e6b2dc21bc3295e79f41c648b9c795bb5df03cb12ceb5b3f2b2` |
| `harness/router/scoring.py` | `80866867ba3997b537233b2d8134ace8504126c53a7804d03c94966a98f5bf0e` |
| `harness/activation/playbook_launch.py` | `7e53c79e40635bfc98b14fee77213051a0576a0f8e567a2fe36ea0fa5d19540d` |
| `harness/activation/capability_manager.py` | `05aa3e36c82e9cb0ac3baf661b05072d5962437ae1704035e0db013123f90b95` |
| `harness/activation/skill_materializer.py` | `ab211d9b0b956f15c29f8d391c6b5b2016c8450d08007a6f00b877547790dd0f` |
| `harness/activation/discovery_bridge.py` | `40d3ecf319998b5708d83d9de8d5acb993ab462856d95ec3c649210ca26c306f` |
| `capability-library/registry.json` | `2c2aec89ea40655d99497064c91d74b6c905bf0ce1d87bbbcdda2a071480a4a9` |
| `.codex/AGENTS.md` | `ebcd3c6627b4679101f98ce59897f528622db9f50d2cd601693f3940b968320c` |

The sorted 40-file V8.3 Stage-B Evidence aggregate is `001ed39bc3d95c8506b8ca98ec9d9aa792389a5e1361622fa4a81c6ca07f06ab` before and after this task. The aggregate input for each file is repository-relative POSIX path, NUL, lowercase per-file SHA-256 hex, and LF.

## Acceptance matrix

| # | Acceptance | Result | Evidence |
|---:|---|---|---|
| 1 | 모든 schema JSON valid | PASS | five schema parse/load and compliant instance tests |
| 2 | 동일 입력 → 동일 hash | PASS | reordered Unicode/null fixture hash equality |
| 3 | task/context 분리 위반 → FAIL | PASS | `task-context-concatenation` fixture |
| 4 | backend false/unknown → FAIL | PASS | two capability fixtures |
| 5 | injection 0/1 규칙 | PASS | context/current-only and duplicate tests |
| 6 | hash mismatch → FAIL | PASS | content, source, envelope artifact/hash tests |
| 7 | strongest permission deterministic | PASS | order/duplicate equivalence and downgrade fixture |
| 8 | required-only overflow → `BUDGET_BLOCKED` | PASS | `budget-overflow` fixture |
| 9 | path escape/symlink → FAIL | PASS | POSIX, Windows-style, and symlink tests |
| 10 | stale cache → `INVALIDATED` | PASS | `stale-cache` fixture |
| 11 | unknown/missing → PASS 금지 | PASS | result UNKNOWN and missing probe field tests |
| 12 | compliant fake backend → PASS | PASS | deterministic compliant fixture |
| 13 | 기존 normal-path regression 유지 | PASS | existing activation/router validation suites |

## Verification result

- New context-contract tests: 21 PASS, 0 FAIL.
- Existing external-skill validation tests: 39 PASS, 0 FAIL.
- Existing activation normal-path tests: 46 PASS, 0 FAIL.
- Existing router/Registry tests: 40 PASS, 0 FAIL.
- Total: 146 PASS, 0 FAIL.
- JSON parse/schema validity: PASS.
- Protected artifact hash regression: PASS.
- `git diff --check`: PASS.
- Change allowlist: PASS; only this task, new context-contract files, and new summary report are tracked changes.
- Actual backend/LLM/Ollama/benchmark/network/API/credential execution: 0.
- Dependency installation/download: 0.

## Result

Schema, canonical serialization/hash, validator, pure fake backend, fixtures, fail-closed tests, and immutable-artifact guards are complete. Runtime integration remains intentionally absent.
