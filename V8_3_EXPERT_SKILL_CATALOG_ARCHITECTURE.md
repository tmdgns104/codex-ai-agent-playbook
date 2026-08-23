# V8.3 Expert Skill Catalog - Architecture

상태: **APPROVED - IMPLEMENTATION BASELINE**

## 1. 아키텍처 목표

V8.3은 V8.2 Dynamic Capability Library와 Self-Managing Control Plane 위에 **External Expert Catalog Layer**를 추가합니다.

기존 정상 task path는 바꾸지 않습니다.

```text
Normal Task
  -> V8.2 Metadata Router
  -> 0~3 selected capabilities
  -> Gate / Activation / Codex / Verification

External Expert Catalog
  -> Source Registry
  -> Domain Taxonomy
  -> Candidate Metadata
  -> Intake Audit
  -> Benchmark
  -> ADOPT / ADAPT / REFERENCE_ONLY / REJECT
  -> V8.2 Proposal/Candidate Governance
  -> ACTIVE Library
```

## 2. Plane 분리

### ACTIVE Plane

실제 Router가 사용할 수 있는 검증 완료 Capability만 포함합니다.

```text
capability-library/
  registry.json
  skills/optional/
  wrappers/
```

### CANDIDATE / EVALUATION Plane

외부 Source와 Candidate metadata, benchmark 결과를 보관합니다.

```text
evaluation/external-skills/
  sources.json
  domain-packs.json
  candidates.json
  benchmarks/
  reports/
```

외부 Skill 발견만으로 ACTIVE registry가 바뀌지 않습니다.

## 3. Source Registry

각 Source는 다음 필드를 가집니다.

```json
{
  "id": "nvidia-skills",
  "repository": "NVIDIA/skills",
  "tier": "A",
  "license": "Apache-2.0 AND CC-BY-4.0",
  "compatibility": ["codex"],
  "purpose": ["gpu", "data", "vision", "robotics"],
  "import_policy": "per-skill-review"
}
```

Source Registry는 upstream Skill body를 복사하는 저장소가 아니라 provenance와 Intake 정책의 Source of Truth입니다.

## 4. Domain Pack

Domain Pack은 Skill을 항상 함께 활성화하는 package가 아닙니다.

역할:

- coverage gap 확인
- candidate discovery 범위 제한
- benchmark fixture grouping
- 중복 Skill 비교

예:

```text
big-data
  desired capabilities:
  - distributed-dataframe
  - spark/pyspark
  - dask
  - cudf
  - parquet/io
  - etl/data-pipeline
  - data-quality
```

실제 task에서는 Router가 이 중 필요한 일부만 선택합니다.

## 5. Candidate Metadata

Candidate는 최소 다음 상태를 가집니다.

```text
DISCOVERED
INSPECTED
BENCHMARK_READY
ADOPT_CANDIDATE
ADAPT_CANDIDATE
REFERENCE_ONLY
REJECTED
PROMOTED
```

Candidate metadata 예:

```json
{
  "candidate_id": "...",
  "source_id": "...",
  "upstream_path": "...",
  "domain_pack": "big-data",
  "license_status": "verified",
  "script_status": "not-executed",
  "permissions": ["local_read"],
  "dependencies": [],
  "decision": "BENCHMARK_READY"
}
```

## 6. Progressive Disclosure

Agent Skills open format의 progressive disclosure 원칙을 유지합니다.

```text
Discovery
-> metadata only
Activation
-> selected SKILL.md only
Execution
-> references/scripts only when needed
```

우리 V8.2 Router는 이 원칙을 더 엄격하게 적용하여 전체 Library body를 정상 작업에 넣지 않습니다.

## 7. 외부 Source Trust Model

### Tier A

표준/공식/Vendor verified source.

높은 신뢰도는 provenance에 대한 것이며 Skill correctness 자동 PASS를 뜻하지 않습니다.

### Tier B

전문 분야에서 유지되고 테스트/CI/문서화가 확인되는 Maintainer Library.

### Tier C

유명 community/harness source.

### Discovery-only

Awesome list/index는 후보 탐색에만 사용하고 Skill source 자체로 신뢰하지 않습니다.

## 8. License Gate

```text
source license 확인
  |
  +-- clear redistribution -> candidate inspection
  +-- mixed/per-skill      -> skill-level license inspection
  +-- source-available     -> reference-only 기본값
  +-- unknown              -> reject import
```

Anthropic document skills처럼 production reference 가치가 높아도 개별 조건이 open-source가 아니면 원문 재배포 대신 REFERENCE_ONLY 또는 허용 범위 내 ADAPT를 사용합니다.

## 9. Safety Gate

Intake 시 정적으로 확인:

- credential/API key 요구
- network/external write
- destructive/prod command
- prompt injection / policy override
- audit bypass / self-approval
- hidden install/bootstrap
- curl pipe / remote binary
- personal absolute path
- executable support files
- dependency install side effect

외부 script는 Intake/inspection 단계에서 실행하지 않습니다.

## 10. Benchmark Architecture

```text
Benchmark Case
  ├─ baseline: no optional skill
  ├─ current: current Playbook skill
  ├─ external: upstream expert skill
  └─ adapted: Playbook-adapted skill
        |
        v
Deterministic Evidence Collector
        |
        +-- tests/acceptance
        +-- router result
        +-- selected count
        +-- loaded bytes
        +-- permission/gate result
        +-- elapsed deterministic steps
        +-- repository diff/evidence
```

LLM output quality가 필요한 평가는 blind rubric 또는 repository artifact 결과와 함께 사용하며 자기보고 PASS 단독 사용을 금지합니다.

## 11. Promotion

외부 Candidate를 ACTIVE로 승격할 때 기존 V8.2 Governance를 재사용합니다.

```text
Candidate
-> skill_audit
-> routing positive/negative fixtures
-> protected regression
-> permission/trigger delta check
-> Human Gate when required
-> atomic promotion
-> source revision/provenance 기록
```

## 12. Update Strategy

Upstream update는 자동 적용하지 않습니다.

```text
upstream changed
-> revision difference detected
-> candidate update proposal
-> diff inspection
-> benchmark regression
-> promotion
```

upstream 변경 때문에 정상 task path가 네트워크를 호출하지 않습니다.

## 13. 초기 Source Set

Foundation의 최소 Source Set:

1. `agentskills/agentskills` - open standard / progressive disclosure 기준
2. `anthropics/skills` - official/reference implementation, document skills 포함
3. `NVIDIA/skills` - NVIDIA-verified Codex-compatible specialist skills
4. `K-Dense-AI/scientific-agent-skills` - science/data/ML/research specialist library
5. `affaan-m/ECC` - broad engineering/harness/community library
6. `alirezarezvani/claude-skills` - broad multi-domain Codex-compatible community library
7. `VoltAgent/awesome-agent-skills` - discovery-only index

## 14. 성능 경계

- Candidate 수 증가가 normal task body scan으로 이어지지 않음
- Candidate catalog는 normal Router의 ACTIVE registry와 분리
- ACTIVE Library가 커져도 metadata-first routing 유지
- Router 성능 회귀는 10/50/100/500/1000+ metadata benchmark로 감시
- semantic retrieval은 실제 threshold 문제 Evidence가 생기기 전까지 기본 경로에 추가하지 않음

## 15. Human Gate

다음은 기존 V8.2와 동일하게 Human Gate 또는 Manual Only입니다.

- permission expansion
- broad trigger expansion
- new external executable auto-use
- destructive/prod capability
- Core promotion/demotion
- split/merge/archive
- external network writer
- registry structural change that changes safety boundary
