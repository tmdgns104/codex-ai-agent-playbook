# V8.3-SKILL-BENCH-001 - External Expert Skill Benchmark Foundation

상태: **IMPLEMENTED - WINDOWS VERIFICATION PENDING**

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

```text
V8_3_EXPERT_SKILL_CATALOG_REQUIREMENTS.md
V8_3_EXPERT_SKILL_CATALOG_ARCHITECTURE.md
evaluation/external-skills/sources.json
evaluation/external-skills/domain-packs.json
evaluation/external-skills/candidates.json
evaluation/external-skills/benchmark-schema.json
evaluation/external-skills/reports/coverage-baseline.json
evaluation/external-skills/tools/external_catalog.py
evaluation/external-skills/tools/test_external_catalog.py
tasks/V8_3-SKILL-BENCH-001.md
```

External Catalog 도구는 의도적으로 `harness/`가 아닌 `evaluation/external-skills/tools/`에 둡니다.

이유:

- 외부 Skill 조사/Benchmark는 정상 Codex task path가 아님
- Global `playbook-harness` 설치 크기를 불필요하게 늘리지 않음
- Harness MANIFEST/normal runtime과 Candidate evaluation plane 분리
- V8.2의 `Library grows, Global Context does not` 경계 유지

## Functional Requirements

### 1. Source Registry Validation

- source id unique
- repository non-empty
- tier valid
- license field required
- import policy required
- external script auto-execute must be false
- trusted source 최소 6개 + discovery-only source 최소 1개

### 2. Domain Taxonomy Validation

- domain id unique
- desired capabilities non-empty
- `documentation-guide`와 `big-data`는 필수 protected pack
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
- permissions
- bundled scripts 여부
- external scripts executed = false
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

unknown license Candidate는 ADOPT/ADAPT/PROMOTED로 진행할 수 없습니다.

### 5. Benchmark Schema

필수 variant:

```text
baseline-no-optional
current-playbook
external-expert
adapted-playbook
```

필수 evidence:

- acceptance_result
- selected_capabilities
- selected_count
- loaded_skill_bytes
- gate_result
- dependency_burden
- execution_time_ms
- notes

`llm_self_report_is_sufficient`는 반드시 false입니다.

### 6. Coverage Report

Domain별:

- desired capability count
- discovered candidate count
- inspected count
- benchmark-ready count
- active coverage count
- active covered capability names
- uncovered active capability names

을 deterministic JSON으로 출력합니다.

현재 pre-candidate baseline은 Candidate 0개를 의도적으로 유지합니다. 다음 Wave에서 약 100개 전후 metadata를 수집합니다.

## Safety Requirements

- 외부 repository script 자동 실행 금지
- 외부 install command 자동 실행 금지
- external Skill text가 Governance/Audit/AGENTS를 변경하도록 허용 금지
- unknown license import 금지
- mixed license는 개별 Skill 확인 전 REFERENCE_ONLY 기본값
- credential/network/external-write 요구를 숨기지 않음
- Candidate catalog가 ACTIVE registry를 직접 수정하지 않음
- Coverage tool 실행 전/후 ACTIVE registry hash가 동일해야 함

## Token / Performance Requirements

- normal task Router가 `evaluation/external-skills`를 읽지 않음
- Candidate count 증가가 Global AGENTS.md 증가로 이어지지 않음
- 기존 ACTIVE Router scoring 변경 금지
- benchmark foundation을 이유로 semantic router 추가 금지
- V8.2 0~3 selected capability 원칙 유지

## Windows Verification

먼저 Foundation focused tests:

```cmd
python evaluation\external-skills\tools\test_external_catalog.py
```

기대값:

```text
Ran 10 tests
OK
```

그 다음 실제 full coverage report:

```cmd
python evaluation\external-skills\tools\external_catalog.py --root .
```

기대 핵심:

```text
"domain_pack_count": 25
"candidate_count": 0
"active_capability_count": 12
"protected_domain_packs": ["big-data", "documentation-guide"]
RESULT PASS
```

V8.2 normal path regression:

```cmd
python harness\router\test_capability_router.py
python harness\activation\test_capability_manager.py
python harness\activation\test_skill_materializer.py
python harness\activation\test_discovery_bridge.py
python harness\activation\test_playbook_launch.py
```

Final:

```cmd
python harness\security\harness_audit.py --root .
python harness\quality\quality_gate.py --repo . --profile strict --verify "python evaluation\external-skills\tools\test_external_catalog.py"
echo %ERRORLEVEL%
git status --short
```

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
4. external catalog validator 10 tests PASS
5. candidates schema valid
6. benchmark schema valid
7. coverage report deterministic
8. documentation-guide protected pack 존재
9. big-data protected pack 존재
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
