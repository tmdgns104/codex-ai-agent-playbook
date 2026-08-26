# V8.4-EXPERT-CONTEXT-002 - Context Transport and Architecture Boundary Decision

상태: **DECISION COMPLETE - IMPLEMENTATION NOT STARTED**

결정: **C. 기존 v1 launcher를 보존하는 versioned opt-in Context Launch Contract를 채택한다.** Backend가 별도 context channel을 실제로 지원하고 검증된 경우에만 B를 C의 backend binding으로 사용할 수 있다. A 방식의 task 문자열 결합은 금지한다.

## 현재 구조

현재 Repository에서 확인된 runtime 경로는 다음과 같다.

```text
task_text
  -> build_activation_plan(task_text, ACTIVE registry)
  -> permission/manual/network blocker 확인
  -> prepare_bridge(task_text)
  -> selected full Skill bundle을 session/cwd/.agents/skills로 이동
  -> bridge argv = [codex, -C, bridge_cwd, --add-dir, repository_root]
  -> launch argv = bridge argv 또는 [codex, -C, repository_root]
                   + [--, task_text]
  -> subprocess.run(argv, check=False)
  -> finally cleanup_bridge()
  -> best-effort privacy-safe event 기록
```

실제 코드 Evidence는 다음과 같다.

- `harness/activation/playbook_launch.py:77`은 ACTIVE registry로 activation plan을 만든다.
- `harness/activation/playbook_launch.py:94`는 기존 Discovery Bridge를 준비한다.
- `harness/activation/playbook_launch.py:111-113`은 option terminator 뒤에 exact `task_text`를 positional prompt로 정확히 한 번 추가한다.
- `harness/activation/playbook_launch.py:168`은 shell interpolation 없이 `subprocess.run(list(plan["argv"]))`을 호출한다.
- `harness/activation/playbook_launch.py:175-181`은 child 종료·오류 뒤 `finally`에서 bridge cleanup을 수행하고 cleanup 실패 시 성공을 FAIL로 바꾼다.
- `harness/activation/discovery_bridge.py:100-101`의 Codex argv는 `-C`와 `--add-dir`만 구성한다.
- `harness/activation/discovery_bridge.py:149-170`은 full Skill bundle을 `cwd/.agents/skills`에 배치하고 bridge manifest를 기록한다.
- `harness/activation/discovery_bridge.py:197-231`은 session path, materialized Skill set, manifest, launch argv drift를 검증한다.
- `harness/activation/skill_materializer.py`는 `AUTO_ALLOWED` 또는 profile을 충족한 `PROFILE_GATED` Skill bundle만 복사하고 source/destination SHA-256을 검증한다.
- `harness/activation/capability_manager.py:37-57`은 sensitive, MCP/agent, network, profile-gated permission을 결정하며, `build_activation_plan()`은 실행하지 않는 plan만 만든다.
- `harness/activation/test_playbook_launch.py:74-84`는 task가 option terminator 뒤에 정확히 한 번 존재함을 회귀 테스트한다.

현재 Repository에는 다음 기능이 없다.

- task와 분리된 arbitrary context attachment 입력 계약
- system/context role을 별도 인자로 전달하는 launcher 경로
- adapted runtime envelope을 읽는 backend adapter
- context artifact가 자동으로 모델 입력에 포함된다는 검증된 Codex CLI 계약
- Context Materializer 또는 transport capability probe

`--add-dir`는 repository directory 접근을 추가하고 Discovery Bridge는 `.agents/skills`를 노출하지만, 둘 중 어느 것도 임의 adapted context artifact를 task와 분리해 LLM에 주입하는 transport로 구현·검증돼 있지 않다. 따라서 B의 지원 여부를 현재 코드만으로 있다고 가정하지 않는다.

관련 Architecture Source of Truth는 다음 경계를 유지한다.

- V8.1: metadata-first Router, minimum selection, permission gate, task 종료 후 deactivate.
- V8.2: deterministic Control Plane과 optional Intelligence Plane 분리, normal critical path에 상시 LLM 비용 추가 금지.
- V8.3: ACTIVE plane과 external candidate/evaluation plane 분리, candidate 발견만으로 ACTIVE 변경 금지.
- V8.4-001: raw snapshot은 reference로 보존하고 approved adapted context만 session-local로 조립하며, Router와 기존 Skill Materializer를 변경하지 않는다.

Repository root에는 별도 `DECISIONS.md`가 없다. 이 Task와 JSON summary가 V8.4 transport에 대한 새 decision record 역할을 하며, 기존 승인 Architecture를 직접 수정하지 않는다.

## 문제 정의

Adapted context를 현재 positional `task_text`에 붙이면 task bytes와 의미 경계가 변하고, exact-user-task 회귀 invariant가 깨진다. 반대로 context 파일만 session에 두면 현재 Codex launch path가 그 파일을 모델 context로 읽는다는 근거가 없다. Full Skill discovery path에 adapted text를 Skill로 위장해 두는 것은 V8.4-001의 Router/Materializer boundary를 침범한다.

필요한 transport는 다음을 동시에 만족해야 한다.

1. 원래 task text의 bytes·순서·출현 횟수를 보존한다.
2. Adapted context를 별도 typed input으로 전달한다.
3. Child process spawn 직전에 source, envelope, budget, permission을 검증한다.
4. Context는 한 launch에 한 번만 주입한다.
5. Backend가 분리 입력을 지원하지 않으면 지원한다고 추측하지 않고 launch 전 중단한다.
6. 기존 v1 launcher와 회귀 테스트를 그대로 보존한다.
7. Context-enabled path를 끄면 즉시 기존 current-playbook path로 rollback할 수 있다.

## 후보 A/B/C 비교표

| 비교 기준 | A. Structured prompt segment | B. Supported context attachment/artifact | C. Versioned launcher contract 확장 |
|---|---|---|---|
| 현재 Architecture 정합성 | 낮음. 현재 launcher에는 별도 system/context segment 인자가 없다. Positional task에 합치면 기존 계약 변경 | 조건부. 별도 artifact 입력은 V8.4-001과 정합적이지만 현재 Repository 지원 Evidence 없음 | 높음. 기존 v1을 보존하고 opt-in orchestration/adapter 경계를 추가 가능 |
| exact-user-task invariant | Task 문자열 결합 시 위반 | 실제 별도 channel이면 보존 가능 | 계약상 `task_text`와 `context_ref`를 분리해 보존; non-compliant backend는 차단 |
| token/context 효율 | Inline context가 매번 prompt에 포함되며 측정은 쉬움 | Backend가 artifact를 어떻게 tokenize하는지에 의존 | Canonical envelope의 bytes/tokens를 사전 측정하고 backend consumption을 별도 기록 가능 |
| 구현 복잡도 | 겉보기에는 낮지만 role/escaping/security 문제 큼 | Backend 지원이 있으면 중간, 없으면 구현 불가 | 높음. schema, coordinator, adapter, capability probe, Evidence가 필요 |
| prompt injection 위험 | 높음. User task와 untrusted-derived context 경계가 문자열에서 약함 | 중간. Typed artifact와 trust label을 지원할 때 낮출 수 있음 | 가장 잘 통제 가능. 별도 field, adapter allowlist, integrity/permission gate를 강제 |
| permission propagation | 결합 후 별도 gate 추적이 어려움 | Manifest가 지원되면 가능 | Contract 필수 field로 current+adapted permission union과 strongest gate를 강제 |
| provenance/hash | Composed prompt hash는 가능하지만 task/context attribution이 약함 | Artifact hash로 강함 | Definition, envelope, artifact, backend receipt hash를 각각 기록 가능 |
| session isolation | 별도 artifact가 없으면 cleanup 대상은 적지만 prompt/log 잔존 경계 불명확 | Session artifact 지원 시 좋음 | Session-local Context Materializer와 adapter lifecycle을 계약으로 강제 |
| cleanup | 문자열 자체 cleanup 계약 없음 | Backend artifact lifecycle에 의존 | Extended coordinator가 `finally`에서 context cleanup을 소유하고 결과 집계 |
| failure/fallback | 결합 이후 부분 실패와 current fallback 구분이 어려움 | Spawn 전 attachment 실패면 fallback 가능 | 상태 전이와 pre-spawn-only fallback을 명시적으로 검증 가능 |
| Codex/OpenAI 환경 의존성 | Role/CLI/API semantics에 강하게 의존 | 가장 높음. 실제 supported attachment가 있어야 함 | 환경 차이는 backend adapter에 격리; current Codex adapter는 지원 입증 전 disabled |
| 다른 backend 지원 | Prompt 문자열은 넓게 동작하지만 role/security 의미가 달라짐 | Backend별 attachment 규격 차이 큼 | 공통 request/result contract와 backend-specific adapter로 확장 가능 |
| 테스트 가능성 | String test는 쉽지만 실제 role/security 의미 테스트가 약함 | 지원 API가 없으면 contract test 불가 | Fake adapter로 deterministic contract test, 실제 adapter별 conformance test 가능 |
| rollback 가능성 | Prompt composition 제거 필요, 기존 동작과 섞이면 회귀 위험 | Attachment path 비활성화 가능 | v2 opt-in을 끄면 untouched v1 current path로 즉시 rollback |

평가 결론:

- A는 구현이 단순해 보여도 현재 exact-user-task invariant와 trust boundary를 직접 깨므로 부적합하다.
- B는 이상적인 물리 transport가 될 수 있지만 현재 Repository에서 “supported”임이 입증되지 않았다. 독립 대안으로 지금 채택할 수 없다.
- C는 복잡도가 가장 높지만 현재 v1을 보존하고 검증되지 않은 backend 기능을 capability gate 뒤에 둘 수 있는 유일한 대안이다.

## 권장안

### 결정 C: Versioned opt-in Context Launch Contract

기존 `playbook_launch.py`의 v1 계약과 argv를 수정하지 않는다. 후속 구현에서는 별도 V8.4 Context Launch Coordinator와 versioned request/result contract를 추가하는 방향을 채택한다.

```text
Existing v1 path (unchanged)
  task_text -> current Router/Activation/Bridge -> [--, exact task_text]

V8.4 opt-in path (new, future implementation)
  exact task_text
  + verified context envelope reference
  + effective permission decision
  + backend capability Evidence
    -> Context Launch Coordinator
    -> compliant backend adapter
    -> one child spawn / one context injection
    -> context cleanup + existing bridge cleanup
```

선택된 Playbook-level transport mode는 `SEPARATE_VERIFIED_CONTEXT_V1`이다. 이 mode는 context를 task positional argument에 포함하지 않는다. Backend adapter는 task와 context를 구별하는 별도 supported channel을 제공해야 한다.

B는 다음 조건을 모두 만족할 때만 C의 adapter binding으로 허용한다.

1. Backend와 정확한 version에서 separate attachment/context 기능이 문서 또는 executable conformance test로 입증된다.
2. Attachment가 모델 입력에 실제 포함됨을 deterministic canary가 입증한다.
3. Original task bytes가 별도 field/argument에 정확히 한 번 유지된다.
4. Artifact content/hash/size/permission을 spawn 직전에 검증할 수 있다.
5. Session cleanup과 failure behavior를 통제할 수 있다.

현재 Codex CLI adapter는 위 Evidence가 없으므로 `supports_separate_verified_context = false`로 간주한다. V8.4 Context-enabled launch는 adapter conformance가 승인되기 전까지 실행 불가이며, 기존 v1 current path만 유지된다.

## 권장안의 이유

1. **기존 invariant 보존**: v1의 `argv[-2:] == ["--", task_text]` 계약과 테스트를 건드리지 않는다.
2. **명시적 trust boundary**: User task, adapted context, permissions, provenance, backend capability를 서로 다른 typed field로 유지한다.
3. **Fail closed**: Backend support가 불명확하면 prompt concatenation으로 우회하지 않고 `TRANSPORT_UNSUPPORTED`로 종료한다.
4. **Permission 보존**: Context에서 위험 문장을 제거했다는 이유로 permission을 낮추지 않고 current activation과 adapted definition의 union/strongest gate를 final check한다.
5. **검증 가능성**: Fake backend로 schema, hash, injection-count, fallback, cleanup을 LLM 없이 테스트할 수 있다.
6. **Backend 독립성**: Codex/OpenAI-specific 세부사항은 adapter 안에 격리하고 contract는 다른 backend에도 동일하게 적용한다.
7. **Rollback**: Context-enabled opt-in을 비활성화하면 기존 launcher와 current-playbook path가 그대로 남는다.
8. **Evidence attribution**: Task hash와 context hash를 분리해 acceptance, tokens, bytes, failure를 transport별로 비교할 수 있다.

## 권장하지 않는 대안과 이유

### A. Structured prompt segment를 권장하지 않음

- 현재 launcher에 별도 system/context role 전달 인자가 없다.
- Positional prompt에 delimiter와 context를 붙이면 전달되는 값이 더 이상 exact user task가 아니다.
- User task와 adapted context의 권한·provenance·hash·실패를 독립적으로 검증하기 어렵다.
- External-derived text가 user instruction과 같은 문자열 경계에 들어가 prompt injection surface가 커진다.
- A를 hidden fallback으로 사용하면 backend support 실패를 성공처럼 숨기게 된다.

따라서 `task_text + delimiter + context_text`, context를 앞뒤에 붙인 단일 문자열, task를 context 파일 읽기 지시로 재작성하는 방식은 모두 금지한다.

### B. Supported attachment를 독립 권장안으로 채택하지 않음

- 현재 Repository의 launcher와 tests에는 arbitrary context attachment argument/API가 없다.
- `--add-dir`가 artifact 내용을 자동으로 모델 context에 넣는다는 Evidence가 없다.
- `.agents/skills`를 attachment처럼 이용하면 기존 Skill discovery와 Materializer 책임을 침범한다.
- 지원 여부, token accounting, lifecycle, backend behavior를 추측하면 “실제 코드에서 확인된 구조만 기록”한다는 Task 조건을 위반한다.

B 자체를 영구 배제하지는 않는다. 검증된 backend attachment는 C의 `SEPARATE_VERIFIED_CONTEXT_V1` adapter implementation으로만 수용한다.

## Architecture boundary

### 소유권과 비소유권

| 구성요소 | 유지/신규 | 소유 책임 | 소유하지 않는 책임 |
|---|---|---|---|
| Existing Router | 유지 | ACTIVE registry metadata routing | Adapted catalog, context transport |
| Capability Manager | 유지 | 현재 selected capability permission/profile gate | Adapted definition materialization |
| Skill Materializer | 유지 | Full optional Skill bundle copy/hash/cleanup primitive | Adapted context, transport |
| Discovery Bridge | 유지 | `.agents/skills`, bridge cwd/argv/integrity | Arbitrary context attachment |
| v1 Launcher | 유지 | Exact task positional launch, existing bridge cleanup/event | Adapted context launch |
| Adapted Capability Catalog | 신규 | Approved definition의 authoritative runtime eligibility/source | Raw snapshot 실행, ACTIVE routing |
| Context Assembler/Materializer | 신규 | Approved units 조립, envelope/hash/budget, session artifact | Child spawn, permission 승인 |
| Effective Permission Verifier | 신규 | Current activation+adapted permission union과 strongest gate | 기존 gate 약화 |
| Context Launch Coordinator | 신규 | Contract orchestration, pre-spawn gates, exactly-once injection, cleanup 집계 | Backend-specific encoding |
| Backend Adapter | 신규 | Capability probe, separate context binding, spawn/result receipt | Candidate selection, permission 결정 |

### Authoritative source 결정

Adapted context의 authoritative runtime source는 **Approved Adapted Capability Catalog에 등록된 immutable Adapted Capability Definition version**이다.

- Pinned snapshot은 provenance root이자 untrusted reference source다.
- `evaluation/external-skills/adapted-contexts.json`은 V8.3 evaluation-only prototype Evidence이며 V8.4 runtime authority가 아니다.
- V8.3 benchmark와 adoption decision은 eligibility/quality Evidence다. Context body authority가 아니다.
- Runtime envelope과 cache는 approved definition에서 파생된 materialization이며 authority가 아니다.
- 현재 eligibility는 adoption decision에 따라 `kd-sympy`, `kd-citation-management` 두 candidate로 제한한다. 확장은 별도 Human Gate가 필요하다.

### 검증 지점 결정

```text
approved definition verification
  -> assembly/budget verification
  -> session materialization
  -> effective permission verification
  -> FINAL TRANSPORT GATE
       - re-read artifact from managed path
       - verify envelope/content/source/version hashes
       - verify session/path containment and no symlink
       - verify backend capability receipt
       - verify task hash and exact-once policy
       - verify effective permission/gate approval
       - verify size/token budget
  -> child spawn
```

Transport 직전 최종 integrity verification의 소유자는 **Context Launch Coordinator**다. Context Materializer의 earlier verification만 신뢰하지 않고, adapter에 넘길 동일 bytes를 spawn 직전에 다시 검증한다. 검증과 adapter 소비 사이에는 mutable rewrite를 허용하지 않는다.

Effective permission은 두 번 확인한다.

1. Selector/assembly 전 preflight: 차단될 candidate에 context 비용을 쓰지 않기 위한 early gate.
2. Transport 직전 final gate: current activation permissions, adapted `source_permissions`, `retained_permissions`, `effective_gate`, task/user approvals의 union에서 가장 강한 gate를 다시 계산.

두 결과가 다르면 더 강한 결과를 적용하고 `PERMISSION_DRIFT`로 중단한다.

### Task/context 경계 결정

- `task_text`는 원본 UTF-8 text와 별도 SHA-256을 가진다.
- `context_envelope_ref`는 session-relative path와 envelope/content SHA-256을 가진다.
- Task text는 context envelope 안에 복사하지 않는다.
- Adapted context는 task 의도나 user authority를 주장하지 않고 `untrusted-derived-approved-reference` trust label을 가진다.
- Backend adapter는 task와 context를 별도 input channel로 전달해야 한다.
- Logs/Evidence에는 raw task 대신 task fingerprint를 기본 기록하고 raw adapted context 대신 hash·unit IDs·byte/token count를 기록한다.

### Injection과 cleanup 결정

- 한 launch request에는 canonical envelope 하나만 허용한다. 여러 approved capability가 있더라도 assembler가 하나의 envelope로 만든다.
- `context_injection_attempt_limit = 1`, `context_injection_count`는 0 또는 1만 허용한다.
- Partial injection 또는 child spawn 뒤에는 current-playbook으로 fallback하거나 같은 process에 context를 재주입하지 않는다.
- Context Launch Coordinator가 top-level cleanup orchestration을 소유한다.
- Context Materializer는 자신이 생성한 managed context path만 안전하게 삭제하는 primitive를 소유한다.
- Existing bridge cleanup은 기존 Discovery Bridge가 계속 소유한다.
- Child 종료 후 context transport handle/artifact cleanup을 먼저 수행하고, 이어서 기존 bridge cleanup을 수행한다. 각 결과를 독립 기록한다.
- 하나라도 cleanup FAIL이면 전체 result는 FAIL이고 해당 managed path는 `QUARANTINED`로 기록한다. Broad recursive delete로 복구하지 않는다.

## Transport contract 초안

### ContextLaunchRequest v1

```text
schema_version: 1
contract_id: v8.4-context-launch-v1
session_id
mode: CURRENT_ONLY | SEPARATE_VERIFIED_CONTEXT_V1

task:
  text
  utf8_sha256
  occurrence_policy: EXACT_POSITIONAL_ONCE

current_plan:
  router_result
  selected_capability_ids[]
  profile
  permissions[]
  gates

adapted_context: null | {
  envelope_relative_path
  envelope_sha256
  content_sha256
  trust_label: untrusted-derived-approved-reference
  adapted_definition_ids[]
  adapted_definition_versions[]
  adapted_definition_hashes[]
  source_snapshot_hashes[]
  selected_unit_ids[]
  loaded_context_bytes
  prompt_token_count_or_null
  tokenizer_id_or_null
  budget_policy_version
}

permission_decision:
  current_permissions[]
  adapted_source_permissions[]
  adapted_effective_permissions[]
  effective_permissions[]
  strongest_gate
  approval_refs[]
  verified_at_utc

backend:
  adapter_id
  adapter_version
  capability_probe_id
  supports_separate_verified_context
  transport_binding

execution_policy:
  context_injection_attempt_limit: 1
  task_occurrence_limit: 1
  retry_count
  fallback_policy_id

cleanup_policy:
  coordinator_owner
  context_cleanup_required
  bridge_cleanup_required
  quarantine_on_failure
```

### ContextLaunchResult v1

```text
schema_version: 1
contract_id: v8.4-context-launch-result-v1
session_id
request_sha256
transport_status
backend_receipt
task_occurrence_count
context_injection_attempt_count
context_injection_count
child_spawned
child_exit_code_or_null
degraded_fallback_used
fallback_reason_or_null
integrity_result
permission_result
budget_result
context_cleanup_result
bridge_cleanup_result
quarantine_paths[]
execution_start_utc
execution_end_utc
failure_code_or_null
evidence_path
```

### Contract invariants

1. `CURRENT_ONLY`이면 `adapted_context=null`, injection count 0이다.
2. `SEPARATE_VERIFIED_CONTEXT_V1`이면 compliant adapter와 non-null context가 필수다.
3. Request canonical SHA-256은 child spawn 전에 고정한다.
4. Backend capability가 false/unknown이면 spawn하지 않는다.
5. Task occurrence count와 context injection count는 각각 정확히 1이어야 context-enabled execution이 valid하다.
6. Context bytes는 positional task argument, task text, `.agents/skills`, repository/global AGENTS에 포함되지 않는다.
7. Final integrity/permission/budget gate가 하나라도 FAIL이면 child를 spawn하지 않는다.
8. Result에는 실제 failure를 기록하며 missing/unknown을 PASS로 바꾸지 않는다.

### Transport Evidence metadata

최소 Evidence:

- contract/request/result schema version과 canonical hash
- session ID, mode, adapter ID/version, backend capability probe ID/hash
- task fingerprint/SHA-256, task occurrence policy와 실제 count
- adapted definition IDs/versions/hashes, source snapshot hashes, selected unit IDs
- envelope/content/artifact hash와 session-relative path
- loaded bytes, measured token count 또는 `null+reason`, tokenizer ID/version
- current/adapted/effective permissions, strongest gate, approval refs
- integrity/permission/budget verification 시각과 결과
- injection attempt limit, 실제 attempt/count, child spawn 여부
- execution start/end, child exit code, transport failure code
- fallback eligibility/decision/reason, degraded mode 여부
- context cleanup, bridge cleanup, quarantine 결과
- external access, credentials, external write, destructive action 발생 여부

Raw task text와 raw context body는 기본 transport Evidence에 중복 저장하지 않는다. 이미 managed artifact에 존재하는 동안 hash로 참조하고 cleanup 뒤에는 provenance/unit metadata를 유지한다.

## Failure / fallback policy

### Degraded current-playbook fallback 허용 조건

모든 조건을 충족할 때만 child spawn 전에 `DEGRADED_CURRENT_PLAYBOOK`으로 전환할 수 있다.

1. Context injection attempt가 0이고 child가 아직 spawn되지 않았다.
2. 기존 v1 Router/activation/current path가 독립적으로 `READY` 또는 안전한 `NO_ACTION`이다.
3. User가 adapted/external expert capability 사용을 명시적으로 요구하지 않았다.
4. Task acceptance가 adapted capability 없이는 충족 불가능하다고 정의되지 않았다.
5. 실패 원인이 transport availability, no approved match 또는 optional context materialization failure다.
6. Permission, integrity, provenance, source ambiguity, security violation이 실패 원인이 아니다.
7. Fallback 이유와 context 미사용을 Evidence와 사용자 결과에 명시한다.

Fallback 시 새 request를 `CURRENT_ONLY`로 canonicalize하고 기존 v1 path를 정확히 한 번 실행한다. 실패한 context request와 current request를 같은 성공 Evidence로 합치지 않는다.

### Fallback 금지 및 중단 조건

| Failure | 결과 | 이유 |
|---|---|---|
| Backend support unknown/false, adapted가 optional | 조건 충족 시 pre-spawn degraded fallback | 지원 추측 금지 |
| Backend support unknown/false, adapted가 required | `HUMAN_GATE_REQUIRED` | capability 의미 변경 |
| Definition/source/envelope hash mismatch | `INTEGRITY_BLOCKED` | provenance 불명확 |
| Permission drift/expansion | `HUMAN_GATE_REQUIRED` 또는 `PERMISSION_BLOCKED` | gate 우회 금지 |
| Context too large, optional units 존재 | Whole optional unit을 deterministic priority로 제외 후 한 번 revalidate | partial truncation 금지 |
| Required units만으로 budget 초과 | `BUDGET_BLOCKED`; larger tier Human Gate | correctness 손실 금지 |
| Injection attempt 후 failure | `TRANSPORT_FAILED`, fallback/retry 없음 | double execution/partial context 방지 |
| Child spawn 후 failure | 실제 child/transport failure 기록 | 결과 보간 금지 |
| Cleanup failure | `QUARANTINED`, 전체 FAIL | unmanaged residue 은폐 금지 |

Context size 처리 순서는 다음으로 결정한다.

1. Assembler가 optional unit을 whole-unit 단위, stable priority 순으로 제외한다.
2. Required correctness/verification/safety unit은 삭제·축약하지 않는다.
3. 다시 canonicalize/hash/tokenize하고 budget을 한 번 검증한다.
4. Required-only가 초과하면 `BUDGET_BLOCKED`다.
5. Raw external context, 임의 summarization, tokenizer 추정치로 gate 통과, hidden larger budget은 금지한다.

## Human Gate 요구사항

다음은 구현·실행 전에 Human Gate가 필요하다.

1. Context-enabled v2 path의 최초 활성화.
2. Context Launch Contract schema/version 또는 invariant 변경.
3. 새 backend adapter 등록, Codex/OpenAI transport support 승인, capability probe 방식 변경.
4. Structured prompt concatenation을 예외로 허용하려는 모든 제안.
5. Effective permission expansion, network/credential/external write/process/destructive/production gate 변화.
6. 현 `ADAPT_CANDIDATE` 두 개 외 candidate eligibility 확대.
7. Total/per-capability token·byte budget 또는 selected capability cardinality 확대.
8. Adapted capability가 required인데 transport가 unavailable하여 fallback이 capability를 제거하는 경우.
9. Integrity/provenance/source/license ambiguity.
10. Quarantined runtime artifact를 자동 복구·삭제하거나 재사용하려는 경우.

다음은 위 정책이 freeze된 후 자동 처리 가능하다.

- Approved definition 없음 → `NO_CONTEXT`와 기존 safe current path.
- Optional transport unavailable → 조건을 모두 만족한 pre-spawn degraded fallback.
- Budget 내 optional unit deterministic exclusion.
- Managed session artifact의 검증된 cleanup.
- Fake backend를 사용한 deterministic contract tests.

## 구현 전 금지사항

- 기존 `playbook_launch.py`, `capability_manager.py`, `skill_materializer.py`, `discovery_bridge.py`, Router scoring을 이 Task에서 수정하지 않는다.
- Task text에 adapted context, artifact read instruction, delimiter를 붙이지 않는다.
- `--add-dir`를 context attachment라고 가정하지 않는다.
- Adapted context를 `.agents/skills`, repository/global AGENTS 또는 ACTIVE registry에 기록하지 않는다.
- Backend support를 문서/테스트 없이 true로 표시하지 않는다.
- Raw snapshot 또는 V8.3 `adapted-contexts.json`을 runtime authority로 사용하지 않는다.
- Permission을 context 문장 삭제만으로 낮추지 않는다.
- Required unit을 budget에 맞추려고 truncate/summarize하지 않는다.
- Partial injection/child spawn 뒤 retry, current fallback, 다른 backend fallback을 하지 않는다.
- 실제 LLM/Ollama/Benchmark 실행이나 network/API/credential 사용을 하지 않는다.
- V8.3 Evidence, V8.4-001, Registry, Router, launcher, activation, Materializer, Bridge, AGENTS를 변경하지 않는다.

## 후속 구현 Task

다음 Task는 `V8_4-EXPERT-CONTEXT-003`으로 고정한다.

### V8_4-EXPERT-CONTEXT-003 - Contract Schema and Deterministic Validator

범위:

- Adapted Capability Definition, Runtime Envelope, `ContextLaunchRequest v1`, `ContextLaunchResult v1`, Backend Capability Probe JSON Schema 작성
- Canonical serialization/hash 규칙 작성
- exact task separation, injection count, path containment, hash, budget, permission union을 검증하는 deterministic validator 작성
- Fake compliant/non-compliant backend fixture와 contract unit test 작성
- 기존 launcher를 호출하거나 수정하지 않음
- 실제 backend, LLM, Ollama 실행 없음

Acceptance:

1. A 방식 prompt concatenation을 schema/validator가 거부한다.
2. Backend support unknown/false에서 context-enabled spawn plan을 거부한다.
3. Task와 context hash/field가 분리된다.
4. Effective permission strongest-gate가 deterministic하게 계산된다.
5. Injection attempt/count가 0 또는 1로 제한된다.
6. Required-only budget overflow가 `BUDGET_BLOCKED`다.
7. Existing v1 launcher/Router/Materializer regression과 source hash가 불변이다.

그 다음 순서는 별도 승인 후 진행한다.

1. `V8_4-EXPERT-CONTEXT-004`: Approved definition compiler/provenance verifier.
2. `V8_4-EXPERT-CONTEXT-005`: Approved-only selector/budget planner shadow mode.
3. `V8_4-EXPERT-CONTEXT-006`: Session-local Context Materializer와 Coordinator, fake adapter integration.
4. `V8_4-EXPERT-CONTEXT-006A`: 실제 Codex/backend capability probe와 adapter feasibility; 지원 Evidence 없으면 BLOCKED.
5. `V8_4-EXPERT-CONTEXT-007`: Controlled transport/quality benchmark policy와 holdout.

이 Task의 결정은 transport를 구현 가능하다고 선언하는 것이 아니다. **Playbook contract는 C로 결정됐고, 현재 Codex physical binding은 지원 Evidence가 없어 disabled**라는 것이 완료 상태다.
