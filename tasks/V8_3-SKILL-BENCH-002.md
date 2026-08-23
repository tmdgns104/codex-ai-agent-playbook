# V8.3-SKILL-BENCH-002 - Expert Candidate Wave 1

상태: **IMPLEMENTED - WINDOWS VERIFICATION PENDING**

선행 조건:

- V8_3-SKILL-BENCH-001 Foundation 구현
- External Catalog focused test 10/10 PASS
- Effective Coverage focused test 5/5 PASS
- Effective Coverage report RESULT PASS
- 현재 목표 172 capability 중 29 covered / 143 uncovered

## 목적

분야별 유명/전문 외부 Skill 중 현재 Playbook의 143개 capability gap을 보완할 가능성이 높은 후보 약 100개를 metadata-only Candidate로 수집합니다.

이 Task에서는 Candidate를 ACTIVE Library에 설치하거나 Router에 노출하지 않습니다.

## 구현 결과

```text
Candidate count     100
Source count          5
Domain Pack coverage 23 / 25
ACTIVE import         0
External script run   0
```

Source 분포:

```text
K-Dense      35
NVIDIA       30
alirezarezvani 22
Anthropic     8
ECC           5
```

Candidate는 `discovery_defaults`를 사용해 반복 metadata를 줄이고, 각 항목에는 `candidate_id / source_id / upstream_path / domain_pack`만 직접 기록합니다.

## Candidate Source

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

industrial-automation은 신뢰도 높은 전문 Source가 부족하여 Wave 1에서 억지 Candidate를 만들지 않았습니다. git-delivery도 현재 기존 coverage가 있고 Wave 1 우선순위에서 제외했습니다. 두 분야는 targeted source discovery 대상으로 남깁니다.

## Discovery Metadata Contract

`DISCOVERED` Candidate는 아직 Skill body/support files를 검사하기 전 상태입니다.

기본값:

```text
source_revision = null
license_status = unknown
compatibility_status = unknown
dependencies = []
permissions = []
bundled_scripts = null
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
- discovery default는 identity/source/path/domain 필드를 상속할 수 없도록 제한

## Acceptance Criteria

1. Candidate metadata >= 100
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

## Windows Verification Pending

다음 Evidence가 필요합니다.

```text
python evaluation\external-skills\tools\test_external_catalog.py
python evaluation\external-skills\tools\test_candidate_wave.py
python evaluation\external-skills\tools\test_effective_coverage.py
python evaluation\external-skills\tools\external_catalog.py --root .
python evaluation\external-skills\tools\effective_coverage.py --root .
```

Foundation/Router/Harness regression은 Candidate 관련 변경이 정상 task path를 침범하지 않았는지 별도로 확인합니다.

## 다음 단계

`V8_3-SKILL-BENCH-003 - Expert Candidate Inspection and Benchmark Shortlist`

- Candidate별 upstream revision / license / dependencies / scripts 검사
- 중복 cluster
- domain별 benchmark shortlist 선정
- ADOPT / ADAPT / REFERENCE_ONLY / REJECT 결정 근거 수집
- industrial-automation / networking / robotics targeted source 보강
- 여전히 자동 ACTIVE import 금지
