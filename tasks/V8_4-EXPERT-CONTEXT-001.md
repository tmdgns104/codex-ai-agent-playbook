# V8.4-EXPERT-CONTEXT-001 - Task-Scoped Adapted Capability Context Design

상태: **DESIGN PROPOSED - IMPLEMENTATION NOT STARTED**
범위: 설계 문서와 설계 요약 Evidence만 작성한다. 코드, Skill, Registry, Router, AGENTS, global policy는 변경하지 않는다.

## Problem

V8.3은 pinned external Expert Skill 원문 전체를 넣는 것보다 task에 필요한 workflow·검증·안전 지식만 압축한 adapted context가 더 유망하다는 단일 모델·고정 fixture Evidence를 만들었다. 그러나 현재 runtime은 두 가지 단위만 안다.

- Router는 ACTIVE registry metadata를 점수화해 capability ID를 선택한다.
- Skill Materializer는 선택된 Skill bundle 전체를 session-local discovery 경로로 복사한다.

이 구조에는 external snapshot을 참조용으로 보존하면서 승인된 지식 조각만 선택하고, 크기·권한·출처를 검증한 뒤 LLM에 전달하는 중간 단위가 없다. External Skill 원문을 Skill로 활성화하면 불필요한 예시, provider 지시, 설치·network·credential 지시와 context 비용이 함께 유입될 수 있다. 반대로 압축률만 최적화하면 필수 절차·검증·안전 조건이 사라져 acceptance가 하락할 수 있다.

V8.4의 문제는 “context를 최소화”하는 것이 아니라 다음 제약을 동시에 만족하는 것이다.

1. acceptance와 verification을 유지하거나 향상한다.
2. task와 무관한 external context는 로드하지 않는다.
3. 원문 provenance와 permission을 잃지 않는다.
4. runtime artifact를 session 종료 후 제거하거나 격리한다.
5. 현재 Router, activation gate, Skill Materializer의 책임을 침범하지 않는다.

## V8.3 Evidence

V8.3-1과 V8.3-2는 서로 다른 Wave이며 역사적 결과를 소급 변경하지 않는다.

| 항목 | V8.3-1 | V8.3-2 validator-postfix |
|---|---:|---:|
| 전체 PASS / FAIL | 2 / 18 | 8 / 12 |
| baseline-no-optional PASS | 0/5 | 1/5 |
| current-playbook PASS | 0/5 | 1/5 |
| external-expert PASS | 0/5 | 1/5 |
| adapted-playbook PASS | 2/5 | 5/5 |
| external loaded context | 54,704 bytes | 54,704 bytes |
| adapted loaded context | 2,799 bytes | 2,799 bytes |
| external prompt tokens | 20,351 | 20,607 |
| adapted prompt tokens | 7,130 | 7,386 |
| external failed hard checks | 9 | 6 |
| adapted failed hard checks | 3 | 0 |

고정된 5-slot 합계에서 adapted context는 raw external보다 51,905 bytes, 94.883% 작았다. Prompt token 감소는 V8.3-1에서 13,221개, 64.965%, V8.3-2에서 13,221개, 64.158%였다. V8.3-2 adapted는 current-playbook보다도 prompt token이 595개, 7.455% 적었다.

해석 제한은 다음과 같다.

- 각 슬롯은 Qwen `qwen3.5:9b`의 고정 seed 단일 실행이므로 반복 실행이나 다른 모델에 대한 인과성을 입증하지 않는다.
- V8.3-2는 validator semantics와 명시적 output contract를 함께 바꿨다. 6개 slot의 FAIL→PASS 전체를 context 효과로만 귀속할 수 없다.
- Wave 1 출력의 읽기 전용 postfix 진단은 semantic false-negative 4건을 확인했고, SymPy·Citation·DOCX output contract check에서는 10건의 FAIL→PASS 전이가 관찰됐다.
- V8.3-1 adoption decision은 그대로 유지된다. 현재 `ADAPT_CANDIDATE`는 `kd-sympy`, `kd-citation-management` 두 개뿐이다. Wave 2의 5/5 결과는 나머지 세 candidate를 자동 승인하지 않는다.
- Failure analysis에서 18개 FAIL의 주원인 중 13개는 `MODEL_CAPABILITY`였다. Compact context는 모델의 input-reading, 사실성, 일관성 오류를 제거한다고 가정할 수 없다.

설계 근거 Source와 SHA-256은 다음과 같다.

| Source | SHA-256 |
|---|---|
| `benchmark-results.json` | `21cb7165c4e02397fdafa9bc5d20f715e723ff351965cf71e00e42f6e7e80249` |
| `adoption-decisions.json` | `4078ba8597bc9483606c41dcae2a88d5096de13ce22cb6c1084665079433bbe3` |
| `adapted-contexts.json` | `f972f89a57dd853eaf7f88648e8a5ce9f6a26f9335e6f03131a48222246e9816` |
| `stage-b-failure-analysis.json` | `22f590325b312ec52b9ab54e889eff7f6c23eb0c3064229d738a4dada307c692` |
| `stage-b-wave2-comparison.json` | `7566322a62064797df4fefbf0319794aab40b1cd66df8cec77c934047f031a6e` |
| `stage-b-wave2-execution-summary.json` | `48ba11e17931c406fc8c1026727bb6dbbce58c2c52652c16e895b15fff7f3c9b` |

## Requirements

### Functional requirements

1. Pinned external `SKILL.md` 원문은 immutable evaluation/reference source로 보존한다.
2. Runtime selector는 별도 승인된 adapted capability만 고려하며, 미승인 candidate를 Wave 2 결과만으로 활성화하지 않는다.
3. Selector는 task applicability, exclusion, overlap, permission, risk, context budget을 순서대로 평가한다.
4. Adaptation은 원문 전체가 아니라 독립적으로 선택 가능한 knowledge unit을 만든다.
5. 각 unit은 절차, 전제조건, verification, failure mode, safety constraint 중 해당 요소를 명시한다.
6. Runtime assembler는 선택된 unit만 canonical order로 조립하고 실제 byte/token 수를 기록한다.
7. LLM에는 조립된 context envelope만 전달하며 raw snapshot이나 전체 external Skill은 전달하지 않는다.
8. Runtime artifact는 session-scoped 경로에만 존재하고 정상·실패·중단 종료에서 managed cleanup한다.
9. Cache hit도 source, policy, schema, validator, permission hash를 다시 검증한다.
10. 모든 선택·제외·budget·permission·materialization·cleanup 결과를 Evidence로 남긴다.

### Quality requirements

- Context 감소는 non-compensable acceptance/safety gate를 통과한 뒤에만 이점으로 인정한다.
- Missing metric은 0이나 PASS로 보간하지 않고 `null`과 사유를 기록한다.
- 동일 task 비교는 fixture, runtime, model, generation config, output contract, slot order를 고정한다.
- Development fixture와 release/holdout fixture를 분리하고 V8.3 5개 fixture에 대한 과적합을 검사한다.
- Runtime adaptation을 위해 추가 LLM call을 요구하지 않는다. Model-assisted extraction이 허용되더라도 offline compile Evidence로만 사용하고 deterministic validation과 human approval을 거친다.

### 구현 전 반드시 승인할 결정

1. Adapted context를 Codex/LLM에 전달할 transport: structured prompt segment, 별도 supported context attachment, 또는 새로운 launcher contract 중 하나.
2. 초기 eligibility를 현 `ADAPT_CANDIDATE` 2개로 고정할지, Wave 2 Evidence에 대한 별도 adoption review 후 확장할지.
3. Tokenizer identifier/version과 byte fallback 기준, total/per-capability hard budget.
4. Offline extraction에서 LLM 보조를 허용할지와 reviewer/adjudicator 책임.
5. Cache 저장 위치, 보존 기간, task fingerprint의 privacy 처리.
6. Selector ambiguity, budget overflow, cleanup failure 시 current-playbook fallback 또는 Human Gate 조건.
7. Holdout dataset, KPI threshold, non-inferiority margin과 반복 실행 수.
8. 새 Context Materializer와 launch integration이 Architecture 변경으로 승인되는 범위.

## Architecture

### 유지하는 기존 Architecture

- `capability-library/registry.json`과 Router scoring은 ACTIVE capability 선택의 Source of Truth로 유지한다.
- Router의 metadata-first scoring, 최대 선택 수, risk/profile 결과는 변경하지 않는다.
- `capability_manager.py`의 permission 분류와 Human/Network/Profile gate를 약화하지 않는다.
- 기존 `skill_materializer.py`는 ACTIVE optional Skill bundle을 복사하는 기존 역할만 유지한다.
- Discovery Bridge와 launcher의 session-local staging, integrity verification, managed cleanup 개념을 유지한다.
- External snapshot, V8.3 benchmark result, adoption decision은 immutable evaluation Evidence로 유지한다.

### 새로 필요한 구성요소

1. **Adapted Capability Catalog**: ACTIVE registry와 분리된 승인 목록. Applicability/exclusion, source snapshot hash, adoption status, permission envelope, knowledge-unit index, budget metadata를 가진다.
2. **Adaptation Compiler**: pinned snapshot을 data로 읽어 knowledge unit draft를 만들고 forbidden instruction을 제거한다. Runtime에는 참여하지 않는다.
3. **Adaptation Verifier**: source alignment, omission, permission propagation, schema, forbidden action, acceptance fixture와 holdout을 검증한다.
4. **Adapted Context Selector**: Router 결과를 덮어쓰지 않고 task와 승인 catalog를 비교해 0~N개 adapted capability를 제안한다.
5. **Budget Planner / Context Assembler**: 필수 safety·verification unit을 우선해 canonical context를 만들고 budget 초과 시 자르지 않고 중단한다.
6. **Adapted Context Materializer**: context envelope와 manifest만 session-local 전용 경로에 기록하고 hash verification과 cleanup을 담당한다.
7. **Context Transport Adapter**: 검증된 envelope를 한 번만 LLM 실행 입력에 연결한다. 기존 launcher의 “user task를 정확히 한 번 전달” invariant를 바꾸므로 구현 전에 별도 Architecture 승인이 필요하다.
8. **Evidence Recorder**: selection, exclusion, cache, tokens, bytes, permissions, lifecycle, task result를 append-only record로 남긴다.

### Adaptation pipeline

Pipeline은 offline compile과 runtime assembly를 분리한다.

**Offline compile**

1. `SOURCE_PINNED`: snapshot path/revision/license/SHA-256을 확인한다.
2. `SOURCE_INSPECTED`: text를 untrusted data로 취급하고 command, provider governance, network/credential 요구를 분류한다.
3. `UNITS_EXTRACTED`: task-specific procedure, prerequisite, verification, failure mode, safety를 atomic unit으로 추출한다.
4. `UNITS_NORMALIZED`: 중복 예시와 설명을 제거하고 canonical terminology/output contract로 정규화한다.
5. `PROVENANCE_BOUND`: 각 unit을 source section 또는 source hash와 transformation record에 연결한다.
6. `POLICY_VERIFIED`: permission, forbidden action, dependency, prompt-injection scan을 통과한다.
7. `QUALITY_VERIFIED`: deterministic tests, frozen fixture, 별도 holdout에서 acceptance 비열화를 확인한다.
8. `APPROVAL_PENDING`: reviewer가 source fidelity와 과도한 생략 여부를 확인한다.
9. `APPROVED`: immutable adapted capability version을 catalog에 게시할 수 있다.

**Runtime assembly**

1. 기존 Router와 activation plan을 읽되 수정하지 않는다.
2. Approved Adapted Capability Catalog에서 task match 후보를 만든다.
3. 기존 선택과 중복되는 후보, exclusion match, 미승인·stale·permission-blocked 후보를 제거한다.
4. 점수, specificity, context cost, risk, stable ID 순으로 deterministic rank한다.
5. 기본 1개, 명시적 multi-domain task만 승인된 상한 내에서 추가 선택한다.
6. Required unit과 task-relevant optional unit을 budget plan에 배치한다.
7. Context envelope를 canonical serialize하고 hash/token/byte를 검증한다.
8. Session-local로 materialize하고 transport 직전에 다시 integrity를 확인한다.
9. LLM 실행 후 acceptance와 KPI Evidence를 기록한다.
10. `finally` cleanup을 수행하고 실패 시 quarantine Evidence를 남긴다.

### Candidate selection

Candidate는 다음 gate를 모두 순서대로 통과해야 한다.

1. `approval_gate`: 현 adoption decision이 `ADAPT_CANDIDATE`이거나 후속 Human Gate에서 V8.4 eligibility가 별도 승인됨.
2. `freshness_gate`: source snapshot, adaptation policy, schema, validator hash 일치.
3. `task_match_gate`: 하나 이상의 explicit applicability trigger/domain match와 exclusion 0개.
4. `overlap_gate`: 기존 Router가 이미 동등 지식을 선택한 경우 capability delta가 입증되지 않으면 제외.
5. `permission_gate`: source/effective permission의 strongest gate 충족. Deny가 allow보다 우선.
6. `quality_gate`: 해당 adapted version의 frozen/holdout acceptance Evidence 존재.
7. `budget_gate`: required unit 전체가 손실 없이 budget 안에 들어감.
8. `cardinality_gate`: 기본 최대 1개. Composite task는 승인된 최대치와 결합 테스트가 있을 때만 2개 이상.

동점은 specificity, 낮은 context cost, 낮은 risk, stable ID 순으로 결정한다. 품질 Evidence가 다른 후보보다 약하면 작은 context라는 이유로 선택하지 않는다.

### Context extraction

- 원문의 imperative text를 실행 지시로 취급하지 않고 후보 지식으로만 분석한다.
- Preserve 대상은 correctness-critical procedure, prerequisite, verification, safety constraint, known failure mode이다.
- Remove 대상은 provider self-governance, install/bundled script, credential/network 요구, reference inventory, 반복 예시, 현재 task와 무관한 domain 설명이다.
- Unit에는 source claim과 변환 후 문장을 함께 두어 reviewer가 의미 손실을 검사할 수 있게 한다.
- Fixture 정답값이나 특정 benchmark label을 일반 지식처럼 삽입하는 것을 금지한다.
- Semantic normalization은 허용된 용어 mapping으로만 수행하고 무제한 fuzzy matching이나 사실 추가를 금지한다.
- Extraction 결과가 원문으로부터 입증되지 않거나 안전상 필요한 제약을 생략하면 reject한다.

### Adapted context schema

Versioned definition의 최소 schema는 다음과 같다.

```text
schema_version
adapted_capability_id
version
status: DRAFT | VERIFIED | APPROVED | REVOKED
candidate_id
applicability: {domains, triggers, exclusions, prerequisites}
source: {snapshot_path, snapshot_revision, snapshot_sha256, license, inspection_evidence}
transformation: {policy_version, method, tool_or_model_id_or_null, reviewer, created_at_utc}
permissions: {source_permissions, retained_permissions, removed_permissions, removal_justification, forbidden_actions, effective_gate}
knowledge_units[]: {
  unit_id, kind, priority, task_tags, prerequisites,
  content, source_locator, source_claim_sha256,
  verification_requirements, failure_modes, safety_constraints
}
budget: {utf8_bytes, tokenizer_id_or_null, token_count_or_null, unavailable_reason_or_null}
verification: {schema_pass, provenance_pass, safety_pass, fixture_evidence, holdout_evidence}
content_sha256
cache_key
```

Runtime envelope는 definition을 복사하지 않고 다음 최소 정보와 선택된 `content`만 가진다.

```text
schema_version
session_id
task_fingerprint
selected_capabilities[]
selected_unit_ids[]
source_snapshot_hashes[]
adaptation_versions[]
effective_permissions
required_gates
context_text
context_sha256
loaded_context_bytes
prompt_token_count_or_null
tokenizer_id_or_null
cache_key_or_null
materialized_at_utc
cleanup_required
```

### Context size / token budget policy

- Gate 순서는 `quality/safety completeness -> token budget -> byte budget -> cost preference`이다.
- Required safety·verification·correctness unit은 절대 자동 truncate하지 않는다.
- 초기 pilot 권고치는 total 1,024 measured tokens, capability당 768 tokens, UTF-8 4,096 bytes, 기본 선택 1개이다. 이는 구현 전 Human Gate에서 tokenizer와 holdout 결과를 근거로 freeze해야 한다.
- Runtime context의 최소 80%는 system/user task, working data, output reserve를 위해 남긴다. Adapted context가 runtime context의 10%를 넘으면 별도 approval 없이는 block한다.
- Tokenizer가 없으면 token은 `null`과 사유를 기록하고 byte hard gate를 적용한다. 추정 token을 실제 token으로 기록하지 않는다.
- Required unit이 budget을 넘으면 `BUDGET_BLOCKED`로 종료한다. Raw external fallback, 임의 요약, unit 일부 절단은 금지한다.
- 품질이 동등할 때만 bytes/tokens가 작은 candidate를 우선한다.

### Provenance, cache, invalidation

- 모든 adapted version은 exact snapshot SHA-256, revision, license, inspection Evidence, transformation policy version을 포함한다.
- Compiled adapted definition cache는 허용한다. Key는 `source_sha256 + schema_version + policy_version + extractor_version + validator_version + permission_policy_version + knowledge_unit_hashes`의 canonical hash다.
- Runtime envelope는 session-local cache만 기본 허용한다. Raw task text와 사용자 data의 cross-task cache는 기본 금지한다.
- 다음 중 하나가 바뀌면 cache는 즉시 stale이다: source hash/revision/license, schema, transformation policy, selector, tokenizer, validator, permission policy, knowledge unit, adoption/eligibility status, relevant acceptance contract.
- Hash mismatch, revoked status, missing Evidence, clock/TTL ambiguity는 cache miss가 아니라 `INVALIDATED`로 기록한다.
- Invalidation 후 자동으로 raw snapshot을 로드하지 않는다. Recompile/review 전에는 current path 또는 block으로 간다.

### 기존 Router와 Skill Materializer 경계

- Router는 ACTIVE registry capability만 선택하며 V8.4 catalog를 읽거나 점수를 변경하지 않는다.
- Adapted Context Selector는 Router output을 입력 Evidence로 사용할 수 있지만 선택을 삭제·재점수화·위장하지 않는다. 별도 `adapted_selected`와 이유를 기록한다.
- Capability Manager의 permission gate가 authoritative lower bound다. Adaptation은 permission을 누락해 gate를 낮출 수 없다.
- Skill Materializer는 full Skill bundle용이다. Adapted context를 `.agents/skills`에 Skill처럼 기록하지 않는다.
- 새 Context Materializer는 session-local `contexts/`와 manifest만 관리하며 기존 materializer의 안전한 session ID, path containment, hash verification, managed cleanup 패턴만 재사용한다.
- Discovery Bridge/launcher와의 결합은 context transport contract 승인 후 별도 Task에서 수행한다.

## Data flow

```text
Pinned external snapshot (immutable, untrusted text)
  -> hash/license/inspection verification
  -> offline Adaptation Compiler
  -> atomic knowledge units
  -> provenance + permission + safety verification
  -> fixture/holdout quality verification
  -> Human approval
  -> Approved Adapted Capability Catalog (immutable version)

User task
  -> existing Router + Capability Manager (unchanged)
  -> Adapted Context Selector (approved catalog only)
  -> overlap/permission/freshness/quality/cardinality gates
  -> Budget Planner + Context Assembler
  -> canonical runtime envelope
  -> Context Materializer (session-local)
  -> integrity check
  -> approved Context Transport Adapter
  -> one task LLM execution
  -> acceptance/KPI Evidence
  -> managed cleanup or quarantine
```

`NO_MATCH`, `NOT_APPROVED`, `STALE`, `PERMISSION_BLOCKED`, `BUDGET_BLOCKED`는 context를 만들지 않는다. 이 경우 기존 current-playbook path가 독립적으로 안전하고 충분하다고 정책에 명시된 경우에만 degraded fallback을 허용한다.

## State transitions

### Offline adaptation state

| Current | Event / gate | Next | Checkpoint |
|---|---|---|---|
| `SOURCE_PINNED` | hash/license 확인 | `SOURCE_INSPECTED` | source manifest |
| `SOURCE_INSPECTED` | unit 추출 | `UNITS_EXTRACTED` | draft units + locators |
| `UNITS_EXTRACTED` | normalize/deduplicate | `UNITS_NORMALIZED` | canonical unit hash |
| `UNITS_NORMALIZED` | provenance/permission/safety PASS | `POLICY_VERIFIED` | verifier Evidence |
| `POLICY_VERIFIED` | fixture/holdout PASS | `QUALITY_VERIFIED` | evaluation Evidence |
| `QUALITY_VERIFIED` | reviewer 승인 대기 | `APPROVAL_PENDING` | review packet |
| `APPROVAL_PENDING` | Human Gate 승인 | `APPROVED` | signed approval record |
| any non-terminal | 검증 실패 | `REJECTED` | immutable failure Evidence |
| `APPROVED` | invalidation input 변화 | `REVOKED` | invalidation reason |

### Runtime state

| Current | Event / gate | Next |
|---|---|---|
| `TASK_RECEIVED` | 기존 route 완료 | `ROUTED` |
| `ROUTED` | 승인 match 없음 | `NO_CONTEXT` |
| `ROUTED` | 승인 candidate 있음 | `CANDIDATE_SELECTED` |
| `CANDIDATE_SELECTED` | stale/hash 실패 | `INVALIDATED` |
| `CANDIDATE_SELECTED` | permission 승인 필요 | `PERMISSION_BLOCKED` 또는 `HUMAN_GATE` |
| `CANDIDATE_SELECTED` | permission PASS | `BUDGET_PLANNED` |
| `BUDGET_PLANNED` | required unit 초과 | `BUDGET_BLOCKED` |
| `BUDGET_PLANNED` | budget PASS | `MATERIALIZED` |
| `MATERIALIZED` | integrity PASS | `READY_TO_INJECT` |
| `READY_TO_INJECT` | transport 성공 | `ACTIVE` |
| `ACTIVE` | task 종료 | `CLEANUP_PENDING` |
| any runtime state | 오류/중단 | `FAILED_CLEANUP_PENDING` |
| cleanup pending | managed cleanup PASS | `CLEANED` |
| cleanup pending | cleanup FAIL | `QUARANTINED` |

장기 실행은 state별 manifest를 atomic write하고 이전 verified checkpoint hash를 연결한다. Resume은 마지막 verified checkpoint 이후 단계만 수행하며 동일 compile/extraction/LLM call을 암묵 재실행하지 않는다. Runtime checkpoint에는 raw task/data 대신 최소 task fingerprint와 selected IDs만 저장한다. `CLEANED` 또는 명시적 `QUARANTINED`가 terminal state다.

## Safety boundaries

- External snapshot은 instruction이 아니라 untrusted reference data다. 포함된 install, script, network, credential, self-modification 지시는 실행하지 않는다.
- Effective permission은 기존 activation gate와 source permission 중 더 강한 제한을 따른다. Permission 제거는 명시적 delta, 근거, reviewer 승인이 없으면 금지한다.
- Sensitive permission, network, credential, external write, destructive, production 요구는 기존 Human/Network gate를 우회할 수 없다.
- Context content는 shell, URL fetch, credential placeholder, hidden prompt instruction, governance override, filesystem traversal을 deterministic scan한다.
- Source/hash/schema/provenance가 불완전하면 fail closed한다.
- Raw external context는 어떤 실패에서도 자동 fallback으로 사용하지 않는다.
- Adapted context는 task data와 분리하며 cross-task user-data cache를 만들지 않는다.
- Session target은 repository 내부 dedicated runtime directory여야 하며 symlink, path escape, unmanaged cleanup을 거부한다.
- Cleanup 실패는 성공으로 숨기지 않고 path/hash를 기록해 격리한다. 자동 destructive cleanup 범위를 넓히지 않는다.
- Adapted context가 잘못된 답을 유도할 수 있으므로 final acceptance는 context 자체의 self-report가 아니라 deterministic output/artifact verification으로 판단한다.

### Failure / fallback policy

| Failure | 행동 | 금지 |
|---|---|---|
| no approved match | 기존 current path 계속, `NO_CONTEXT` 기록 | 임의 candidate 선택 |
| ambiguity/tie | deterministic tie-break; 품질 차이가 불명확하면 no context 또는 Human Gate | 여러 context 무차별 로드 |
| source/cache drift | invalidate 후 block/recompile 요청 | stale cache 사용 |
| permission block | 기존 gate로 중단 | 문장 삭제로 permission 세탁 |
| budget overflow | `BUDGET_BLOCKED`; 승인된 larger tier 또는 current path | truncate/raw fallback |
| verifier failure | adapted version reject/quarantine | acceptance 추측 |
| transport unavailable | current path가 안전한 경우 degraded 실행, 아니면 block | user task를 몰래 재작성 |
| LLM/task failure | 실제 failure Evidence 기록 | retry/fallback 보간 |
| cleanup failure | `QUARANTINED`, 경로/hash 보고 | broad destructive delete |

## KPI

KPI는 동일 task/runtime의 paired comparison으로 측정하며 quality와 safety를 context 비용보다 우선한다.

| KPI | 정의 | 방향 | 필수 Evidence |
|---|---|---|---|
| acceptance quality | `all hard gates pass` slot 비율과 candidate별 failed hard checks | 높을수록 좋음; current 대비 비열화 0이 우선 | fixture/rubric version, per-check Evidence |
| prompt tokens | provider/tokenizer가 보고한 prompt token 합계 및 slot별 delta | quality 동등 시 낮을수록 좋음 | tokenizer/runtime ID, null reason |
| loaded context bytes | 실제 주입된 UTF-8 bytes; metadata 제외/포함 범위 고정 | quality 동등 시 낮을수록 좋음 | context hash와 byte count |
| selected capability count | runtime에서 실제 선택·주입된 adapted capability 수 | 필요한 최소 수 | selected/excluded reason |
| LLM calls | task execution, offline extraction, judge 호출을 분리한 실제 호출 수 | runtime 추가 호출 0 목표 | call type, attempt, model/digest |
| execution time | selection+verify+materialize+generation+cleanup end-to-end와 각 구간 | quality 동등 시 낮을수록 좋음 | monotonic timing, timeout |
| failure rate | generation, schema, acceptance, budget, permission, integrity, cleanup 실패를 분리한 비율 | 낮을수록 좋음 | denominator와 terminal state |

초기 release gate 권고는 다음과 같다.

- Safety/permission/integrity hard gate: 100% PASS.
- Candidate별 adapted acceptance: 동일 조건 current-playbook보다 낮아지지 않음.
- Aggregate acceptance는 frozen development와 별도 holdout 양쪽에서 current-playbook 이상.
- Raw external은 evaluation reference일 뿐 runtime fallback이 아니며, quality가 동등 이상일 때 adapted loaded bytes가 raw external의 20% 이하인 것을 목표로 한다.
- Runtime adaptation LLM call 추가: 0.
- 기본 selected capability count: 0 또는 1; 2 이상은 explicit composite fixture와 승인 필요.
- Missing metric, timeout, invalid output은 FAIL 또는 `UNVERIFIED`이며 PASS로 보간하지 않는다.
- 정확한 반복 수, confidence interval, latency margin은 V8.4 benchmark-policy 후속 Task에서 모델/runtime과 함께 freeze한다.

## Acceptance criteria

1. V8.3-1의 2 PASS/18 FAIL과 V8.3-2의 8 PASS/12 FAIL을 분리 기록한다.
2. V8.3-2 adapted 5/5와 external 1/5를 사실로 기록하되 adoption decision으로 재해석하지 않는다.
3. Raw/adapted context 54,704/2,799 bytes와 94.883% 감소를 재현 가능하게 연결한다.
4. Offline compile과 runtime assembly가 분리된다.
5. Raw snapshot은 immutable reference이며 runtime injection 대상이 아니다.
6. Approved candidate만 selector 입력이 된다.
7. 현재 승인 상태에서는 SymPy와 Citation 두 candidate만 초기 eligibility를 가진다.
8. Context schema에 provenance, snapshot hash, transformation, permissions, unit hashes, budget, verification이 포함된다.
9. Quality/safety required unit은 budget을 위해 truncate되지 않는다.
10. Cache key와 모든 invalidation 입력이 명시된다.
11. Permission propagation은 deny/strongest-gate 우선이며 adaptation으로 약화되지 않는다.
12. Router scoring/registry와 Skill Materializer의 책임이 변경되지 않는다.
13. Adapted context는 Skill discovery directory에 full Skill처럼 materialize되지 않는다.
14. Runtime artifact는 session-local이고 integrity verification과 managed cleanup을 가진다.
15. Raw external, stale cache, 다른 candidate로 자동 fallback하지 않는다.
16. Long-run checkpoint, idempotent resume, cleanup/quarantine terminal state가 정의된다.
17. 7개 KPI의 unit, direction, denominator, missing-data behavior가 후속 benchmark policy에서 freeze된다.
18. Development fixture와 holdout fixture가 분리된다.
19. Context transport와 architecture integration은 구현 전 Human Gate를 거친다.
20. ACTIVE registry, Router, global/repository AGENTS와 V8.3 artifacts는 이 설계 Task에서 변경되지 않는다.

## Implementation phases

1. **Decision freeze**: transport, eligibility, tokenizer/budget, cache/privacy, fallback, KPI threshold를 Human Gate에서 승인한다.
2. **Schema and offline harness**: Adapted Capability Catalog, definition/envelope schema, provenance/permission validator를 isolated evaluation path에 만든다.
3. **Approved-candidate compile pilot**: 현 `ADAPT_CANDIDATE`인 SymPy와 Citation만 compile하고 source-alignment review와 holdout을 수행한다.
4. **Selector and budget planner**: ACTIVE Router를 수정하지 않는 별도 selector를 shadow mode로 구현하고 over/under-selection Evidence를 수집한다.
5. **Context materialization and transport**: 별도 Context Materializer와 승인된 transport를 session-local 경로에 구현하고 cleanup/failure injection을 검증한다.
6. **Controlled benchmark**: current-playbook, raw-reference evaluation, adapted-on-demand를 frozen runtime과 blinded holdout에서 비교한다.
7. **Limited opt-in pilot**: approved candidates에만 opt-in하고 KPI, failure slice, cleanup integrity를 관찰한다.
8. **Expansion review**: EDA, sklearn, DOCX를 포함한 추가 candidate는 Wave 2만으로 승격하지 않고 별도 adoption review 후 결정한다.

각 phase는 독립 Task와 Evidence를 가져야 하며 이전 phase PASS와 필요한 Human Gate 없이는 다음 phase를 시작하지 않는다.

## 필요한 후속 Task 목록

1. `V8_4-EXPERT-CONTEXT-002`: Context transport와 Architecture boundary 결정.
2. `V8_4-EXPERT-CONTEXT-003`: Adapted definition/runtime envelope JSON Schema 및 validator 설계·구현.
3. `V8_4-EXPERT-CONTEXT-004`: Pinned snapshot offline compiler와 provenance/safety inspection harness.
4. `V8_4-EXPERT-CONTEXT-005`: Approved-only selector, overlap detector, budget planner shadow mode.
5. `V8_4-EXPERT-CONTEXT-006`: Session-local Context Materializer, integrity, cleanup, quarantine.
6. `V8_4-EXPERT-CONTEXT-007`: Development/holdout fixture와 controlled benchmark policy.
7. `V8_4-EXPERT-CONTEXT-008`: SymPy/Citation limited pilot 및 KPI report.
8. `V8_4-EXPERT-CONTEXT-009`: Wave 2 후보 재평가와 expansion Human Gate.

### 기존 Architecture를 유지하는 부분

ACTIVE registry와 Router scoring, activation permission gate, full Skill용 Materializer, Discovery Bridge lifecycle, V8.3 snapshot/Evidence/adoption decision은 그대로 유지한다.

### 새로 필요한 부분

승인 전용 Adapted Capability Catalog, offline Compiler/Verifier, 별도 Selector, Budget Planner/Assembler, Context Materializer, transport adapter, provenance/cache/evidence contract가 필요하다.

### 위험 요소

5개 fixture·단일 Qwen run 과적합, validator/contract 변화와 context 효과 혼동, 압축 중 지식·안전 제약 손실, permission laundering, external prompt injection, stale cache, selector 오선택, tokenizer drift, task fingerprint privacy, cleanup 실패, 기존 launcher의 exact-task invariant 침해가 주요 위험이다.

### 구현 전에 반드시 결정해야 하는 사항

Transport와 architecture 승인 범위, 초기 eligible candidate, extraction 승인 주체, tokenizer와 hard budget, cache/privacy, failure fallback, holdout·반복 수·KPI threshold를 먼저 freeze해야 한다. 이 결정이 없으면 구현 Task는 `BLOCKED`로 처리한다.
