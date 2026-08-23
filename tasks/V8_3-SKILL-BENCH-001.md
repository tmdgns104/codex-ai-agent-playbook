# V8.3-SKILL-BENCH-001 - External Expert Skill Benchmark Foundation

상태: **COMPLETE - VERIFIED**

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

Foundation 시점의 pre-candidate baseline은 Candidate 0개이며 `evaluation/external-skills/reports/coverage-baseline.json`에 고정되어 있습니다. 이후 `V8_3-SKILL-BENCH-002`에서 Candidate 100개가 추가되었으므로 현재 catalog 실행 결과의 candidate_count는 100입니다.

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

## Windows Verification - COMPLETE

Foundation pre-Wave focused Evidence:

```text
python evaluation\external-skills\tools\test_external_catalog.py
Ran 10 tests - OK

python evaluation\external-skills\tools\external_catalog.py --root .
Foundation pre-candidate catalog validation - RESULT PASS

coverage-baseline.json
candidate_count 0 / domain_pack_count 25 / active_registry_capability_count 12
```

Wave 1 확장 후 current focused Evidence:

```text
python evaluation\external-skills\tools\test_external_catalog.py
Ran 12 tests - OK

python evaluation\external-skills\tools\test_effective_coverage.py
Ran 5 tests - OK

python evaluation\external-skills\tools\external_catalog.py --root .
Candidate count 100 / Domain Pack count 25 / ACTIVE capability count 12
RESULT PASS

python evaluation\external-skills\tools\effective_coverage.py --root .
Candidate count 100 / desired 172 / current covered 29 / uncovered 143
RESULT PASS
```

V8.2 normal-path regression Evidence:

```text
python harness\router\test_capability_router.py
Ran 28 tests - OK

python harness\activation\test_capability_manager.py
Ran 12 tests - OK

python harness\activation\test_skill_materializer.py
Ran 10 tests - OK

python harness\activation\test_discovery_bridge.py
Ran 10 tests - OK

python harness\activation\test_playbook_launch.py
Ran 12 tests - OK
```

Final Harness/Gate Evidence:

```text
python harness\security\harness_audit.py --root .
AGENTS.md 4579 bytes / Core 7 / Optional 10 / warnings 0
RESULT PASS

python harness\quality\quality_gate.py --repo . --profile strict --verify "python evaluation\external-skills\tools\test_external_catalog.py"
RESULT PASS
ERRORLEVEL 0

git status --short
(clean)
```

## Acceptance Criteria Result

1. requirements/architecture 문서 존재 - PASS
2. source registry >= 6 trusted sources + discovery index - PASS
3. 25 domain packs valid - PASS
4. external catalog validator PASS - PASS (Foundation 10/10, current 12/12)
5. candidates schema valid - PASS
6. benchmark schema valid - PASS
7. coverage report deterministic - PASS
8. documentation-guide protected pack 존재 - PASS
9. big-data protected pack 존재 - PASS
10. external scripts not executed - PASS
11. ACTIVE registry unchanged - PASS
12. Router scoring unchanged - PASS
13. Global AGENTS.md unchanged - PASS
14. V8.2 router/activation regression PASS - PASS
15. Harness Audit PASS - PASS
16. STRICT Quality Gate PASS - PASS
17. final working tree clean - PASS
18. Windows Evidence 확인 전 COMPLETE 표시 금지 - PASS

따라서 `V8_3-SKILL-BENCH-001`은 **COMPLETE - VERIFIED**입니다.

## 완료 후 다음 Task

`V8_3-SKILL-BENCH-002 - Expert Candidate Wave 1`

`V8_3-SKILL-BENCH-002`도 Windows Evidence를 통해 COMPLETE - VERIFIED 되었으며, 다음 단계는 `V8_3-SKILL-BENCH-003 - Expert Candidate Inspection and Benchmark Shortlist`입니다.
