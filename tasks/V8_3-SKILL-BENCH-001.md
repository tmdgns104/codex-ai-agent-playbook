# V8.3-SKILL-BENCH-001 - External Expert Skill Benchmark Foundation

상태: **APPROVED - READY FOR IMPLEMENTATION**

선행 조건:

- V8.2 COMPLETE - VERIFIED
- `main` baseline after V8.2 documentation refresh

## 목적

분야별 유명/전문 Skill을 대규모로 활용하기 전에 외부 Source, Domain Pack, Candidate, Benchmark, Promotion 경계를 먼저 고정합니다.

이 Task에서는 외부 Skill을 ACTIVE Library에 대량 설치하지 않습니다.

## Source Baseline

초기 Source:

```text
Tier A
- agentskills/agentskills
- anthropics/skills
- NVIDIA/skills

Tier B
- K-Dense-AI/scientific-agent-skills

Tier C
- affaan-m/ECC
- alirezarezvani/claude-skills

Discovery only
- VoltAgent/awesome-agent-skills
```

Source claim은 2026-08-23 upstream README 기준으로 기록하며, 실제 채택 시에는 개별 Skill path/license/revision을 다시 확인합니다.

## Domain Coverage Baseline

25개 Domain Pack을 정의합니다.

```text
documentation-guide
presentation-visual
data-analysis
big-data
machine-learning
deep-learning-gpu
computer-vision
edge-ai-nvidia
rag-llm-agent
backend-api
database-sql
devops-container
cloud-infra
testing-qa
debug-performance
security-auth
reliability-observability
git-delivery
embedded-iot
robotics-ros
industrial-automation
networking
research-literature
scientific-computing
office-documents
```

## 구현 산출물

이미 baseline으로 생성:

```text
V8_3_EXPERT_SKILL_CATALOG_REQUIREMENTS.md
V8_3_EXPERT_SKILL_CATALOG_ARCHITECTURE.md
evaluation/external-skills/sources.json
evaluation/external-skills/domain-packs.json
tasks/V8_3-SKILL-BENCH-001.md
```

이 Task에서 추가 구현할 최소 코드/데이터:

```text
harness/skills/external_catalog.py
harness/skills/test_external_catalog.py
evaluation/external-skills/candidates.json
evaluation/external-skills/benchmark-schema.json
evaluation/external-skills/reports/coverage-baseline.json
```

파일명은 구현 과정에서 더 명확한 이름이 필요하면 Task 목적을 바꾸지 않는 범위에서 조정할 수 있습니다.

## Functional Requirements

### 1. Source Registry Validation

- source id unique
- repository non-empty
- tier valid
- license field required
- import policy required
- external script auto-execute must be false

### 2. Domain Taxonomy Validation

- domain id unique
- desired capabilities non-empty
- documentation-guide와 big-data pack은 필수 protected pack
- 최소 25 pack 유지

### 3. Candidate Metadata

Candidate는 body를 정상 Router에 노출하지 않고 metadata만 기록합니다.

필수:

- candidate id
- source id
- upstream path/name
- domain pack
- source revision when inspected
- license status
- compatibility status
- dependencies
- permission/risk hints
- bundled scripts 여부
- decision state

### 4. Decision State

허용:

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

### 5. Benchmark Schema

최소 variant:

```text
baseline-no-optional
current-playbook
external-expert
adapted-playbook
```

최소 evidence:

- acceptance/test result
- selected capabilities
- selected count
- loaded skill bytes/context proxy
- permission/gate result
- dependency burden
- execution time if deterministic
- notes/reason

### 6. Coverage Report

Domain별:

- desired capability count
- discovered candidate count
- inspected count
- benchmark-ready count
- active coverage count
- uncovered capability names

를 deterministic JSON으로 출력할 수 있어야 합니다.

## Safety Requirements

- 외부 repository script 자동 실행 금지
- 외부 install command 자동 실행 금지
- external Skill text가 Governance/Audit/AGENTS를 변경하도록 허용 금지
- unknown license import 금지
- mixed license는 개별 Skill 확인 전 REFERENCE_ONLY 기본값
- executable support file이 있으면 별도 review marker 필요
- credential/network/external-write 요구를 숨기지 않음
- Candidate catalog가 ACTIVE registry를 직접 수정하지 않음

## Token / Performance Requirements

- normal task Router가 `evaluation/external-skills` 전체 body를 읽지 않음
- Candidate count 증가가 Global AGENTS.md 증가로 이어지지 않음
- 기존 ACTIVE Router scoring 변경 금지
- benchmark foundation을 이유로 semantic router 추가 금지
- V8.2 0~3 selected capability 원칙 유지

## First Candidate Wave 계획

Foundation PASS 후 다음 Task에서 약 100개 전후 Candidate metadata를 분야별로 수집합니다.

우선순위:

```text
1. Documentation / Guide / PDF / PPTX / XLSX
2. Data Analysis / Big Data / ML
3. RAG / Agent / Backend / DB
4. Testing / Debug / Security / DevOps
5. Computer Vision / Edge AI / NVIDIA
6. Research / Scientific Computing
7. Embedded / Robotics / Industrial / Networking
```

후보 수는 목표치이지 채택 수가 아닙니다.

## Acceptance Criteria

1. requirements/architecture 문서 존재
2. source registry >= 6 trusted sources + discovery index
3. 25 domain packs valid
4. external catalog validator tests PASS
5. candidates schema valid
6. benchmark schema valid
7. coverage report deterministic
8. documentation-guide protected coverage 존재
9. big-data protected coverage 존재
10. external scripts not executed
11. ACTIVE registry unchanged
12. Router scoring unchanged
13. Global AGENTS.md unchanged
14. V8.2 router/activation regression PASS
15. Harness Audit PASS
16. STRICT Quality Gate PASS
17. final working tree clean
18. Windows Evidence 확인 전 COMPLETE 표시 금지

## 완료 후 다음 Task

`V8_3-SKILL-BENCH-002 - Expert Candidate Wave 1`

목표:

- 분야별 대표 Candidate 약 100개 metadata 수집
- source/license/dependency 분류
- 중복 clustering
- 첫 benchmark 대상 선정
- ACTIVE import 없음
