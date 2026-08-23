# V8.3-SKILL-BENCH-002 - Expert Candidate Wave 1

상태: **APPROVED - READY FOR IMPLEMENTATION**

선행 조건:

- V8_3-SKILL-BENCH-001 Foundation 구현
- External Catalog focused test 10/10 PASS
- Effective Coverage focused test 5/5 PASS
- Effective Coverage report RESULT PASS
- 현재 목표 172 capability 중 29 covered / 143 uncovered

## 목적

분야별 유명/전문 외부 Skill 중 현재 Playbook의 143개 capability gap을 보완할 가능성이 높은 후보 약 100개를 metadata-only Candidate로 수집합니다.

이 Task에서는 Candidate를 ACTIVE Library에 설치하거나 Router에 노출하지 않습니다.

## Candidate Source

우선 사용:

```text
anthropics/skills
NVIDIA/skills
K-Dense-AI/scientific-agent-skills
alirezarezvani/claude-skills
affaan-m/ECC
```

`VoltAgent/awesome-agent-skills`는 discovery index로만 사용하며 직접 채택 근거로 사용하지 않습니다.

## 우선 Domain

1. documentation-guide / office-documents / presentation-visual
2. data-analysis / big-data / machine-learning / deep-learning-gpu
3. computer-vision / edge-ai-nvidia
4. rag-llm-agent / backend-api / database-sql
5. testing-qa / debug-performance / security-auth / reliability-observability
6. devops-container / cloud-infra
7. research-literature / scientific-computing
8. embedded-iot / robotics-ros / networking

industrial-automation은 신뢰도 높은 전문 Source가 부족하면 억지 Candidate를 채우지 않고 다음 targeted source discovery로 넘깁니다.

## Discovery Metadata Contract

`DISCOVERED` Candidate는 아직 Skill body/support files를 검사하기 전 상태입니다.

필수:

```text
candidate_id
source_id
upstream_path
domain_pack
source_revision = null 허용
license_status = unknown 허용
compatibility_status = unknown 허용
dependencies = []
permissions = []
bundled_scripts = null 허용
external_scripts_executed = false
decision = DISCOVERED
```

`bundled_scripts = null`은 "스크립트 없음"이 아니라 "아직 검사하지 않음"을 의미합니다.

`INSPECTED` 이상으로 전환하려면 bundled_scripts를 true/false로 확정해야 합니다.

## Safety

- 외부 Skill script/install command 자동 실행 금지
- Candidate metadata 수집만으로 ACTIVE registry 변경 금지
- Candidate body를 normal Router context에 로드 금지
- unknown license Candidate의 ADOPT/ADAPT/PROMOTED 전환 금지
- Anthropic mixed/source-available 자산은 개별 license 확인 전 reference-only 성격으로 취급
- permission/trigger expansion은 V8.2 Human Gate 유지
- Global AGENTS.md / Router scoring 변경 금지

## Acceptance Criteria

1. Candidate metadata 약 100개, 최소 100개
2. source diversity >= 5
3. protected domain `documentation-guide`, `big-data` 각각 Candidate >= 3
4. 최소 18개 Domain Pack에 Candidate 존재
5. 모든 Candidate `external_scripts_executed=false`
6. DISCOVERED의 unknown bundled_scripts 표현 가능
7. INSPECTED 이상은 bundled_scripts boolean 필수
8. unknown license advance 차단 유지
9. external catalog validation PASS
10. Candidate Wave focused test PASS
11. ACTIVE registry hash unchanged
12. current effective coverage 29/172 자체는 Candidate 때문에 증가하지 않음
13. normal Router/Global AGENTS 변경 없음
14. Windows Evidence 전 COMPLETE 표시 금지

## 다음 단계

`V8_3-SKILL-BENCH-003 - Expert Candidate Inspection and Benchmark Shortlist`

- Candidate별 upstream revision / license / dependencies / scripts 검사
- 중복 cluster
- domain별 benchmark shortlist 선정
- ADOPT / ADAPT / REFERENCE_ONLY / REJECT 결정 근거 수집
- 여전히 자동 ACTIVE import 금지
