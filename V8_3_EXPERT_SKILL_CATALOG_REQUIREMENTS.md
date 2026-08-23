# V8.3 Expert Skill Catalog - Requirements

상태: **APPROVED - IMPLEMENTATION BASELINE**

## 1. 목적

V8.3의 목적은 분야별로 신뢰도 높은 Expert Skill을 폭넓게 보유하면서도, 정상 작업에서는 기존 V8.2의 작은 Context와 0~3개 선택 원칙을 유지하는 것입니다.

핵심 목표:

```text
Library coverage는 넓게
Task context는 작게
외부 전문성은 활용
검증/권한 경계는 더 엄격하게
```

## 2. 목표 범위

V8.3은 최소 다음 Domain Pack을 조사하고 대표 Skill Candidate를 확보합니다.

1. Documentation / Guide Writing
2. Presentation / Visual Communication
3. Data Analysis / EDA / Statistics
4. Big Data / ETL / Distributed Data
5. Machine Learning
6. Deep Learning / GPU
7. Computer Vision
8. Edge AI / NVIDIA
9. RAG / LLM / Agent Engineering
10. Backend / API
11. Database / SQL
12. DevOps / Containers / Kubernetes
13. Cloud / Infrastructure
14. Testing / QA
15. Debugging / Performance
16. Security / Auth
17. Reliability / Observability
18. Git / Delivery / Release
19. Embedded / IoT / CAN / Serial
20. Robotics / ROS2
21. Industrial Automation / PLC / OPC UA / Modbus / MES
22. Networking / Troubleshooting
23. Scientific Research / Literature / Citation
24. Scientific Computing / Optimization / Simulation
25. Office / PDF / DOCX / XLSX

분야는 향후 Evidence에 따라 추가할 수 있지만, Global AGENTS.md나 정상 Router의 항상-loaded Context를 늘리는 방식으로 확장하지 않습니다.

## 3. 외부 Source 우선순위

### Tier A - 표준 / 공식 / Vendor-verified

- Agent Skills open standard
- Anthropic official/reference skills
- NVIDIA verified skills
- 기타 제품 Vendor가 직접 관리하는 공식 Skill

### Tier B - 전문 분야 Maintainer Library

- K-Dense Scientific Agent Skills 등 특정 전문 분야에서 대규모로 유지되는 Library

### Tier C - 검증된 Community / Harness Library

- ECC
- 범용 multi-domain Skill Library
- 분야별 community reference

Tier는 품질 PASS를 의미하지 않습니다. 모든 Candidate는 동일한 Intake/Audit/Benchmark를 통과해야 합니다.

## 4. Intake 원칙

외부 Skill은 발견 즉시 ACTIVE Library에 넣지 않습니다.

```text
External Source
-> provenance/license inspection
-> metadata-only catalog
-> safety/dependency inspection
-> benchmark candidate
-> ADOPT / ADAPT / REFERENCE_ONLY / REJECT
-> Candidate Audit
-> Router regression
-> Human Gate if required
-> ACTIVE
```

### 필수 metadata

- source repository
- source revision/tag/commit when adopted
- upstream skill path/name
- license and redistribution status
- maintainer/source tier
- claimed host compatibility
- domain pack
- required tools/dependencies
- network/external-write/credential needs
- bundled scripts/resources 여부
- intake decision

## 5. License / Supply Chain

- Repository 전체 license와 개별 Skill license가 다르면 개별 Skill 조건을 우선합니다.
- source-available/reference-only 항목은 재배포하지 않고 링크/metadata/benchmark reference로만 유지합니다.
- license가 불명확하면 ACTIVE import 금지입니다.
- 외부 executable script를 Intake 단계에서 자동 실행하지 않습니다.
- remote install script / curl pipe / unknown binary를 자동 실행하지 않습니다.
- adopted Skill은 source revision을 pin할 수 있어야 합니다.

## 6. Benchmark 계약

대표 작업에 대해 가능한 경우 다음 4개를 비교합니다.

```text
A. No optional Skill
B. Current Playbook Skill
C. External expert Skill
D. Adapted Playbook version
```

평가 항목:

- task completion / acceptance result
- factual/procedural correctness
- repository test/evidence result
- unnecessary actions
- permission/risk violations
- router precision/false positive/false negative
- selected Skill count
- loaded Skill bytes / context proxy
- execution time where deterministic measurement is possible
- dependency burden
- portability to Codex

LLM 자기보고 점수만으로 승자를 정하지 않습니다.

## 7. ADOPT / ADAPT / REFERENCE_ONLY / REJECT

### ADOPT

- license/redistribution clear
- Codex-compatible structure
- bounded scope
- dependency/risk acceptable
- benchmark superiority or unique value demonstrated

### ADAPT

- 전문 내용은 우수하지만 Claude/vendor-specific assumptions, 과도한 Context, broad trigger, permission scope 등을 수정해야 함
- 원문 전체 복사가 아니라 허용된 license 범위 안에서 구조/원칙을 재작성할 수 있음

### REFERENCE_ONLY

- production reference로 가치가 있지만 재배포 조건, 무거운 dependency, 특정 product/runtime 종속성 때문에 ACTIVE import에 부적합

### REJECT

- license 불명확
- prompt injection / audit bypass / unsafe execution 요구
- 불필요한 credential/network/external-write 요구
- 기존 Skill 대비 가치 없음
- 지나치게 broad하여 Router 품질 악화

## 8. Context / Routing 예산

V8.2 계약을 유지합니다.

- metadata-first deterministic routing
- Skill 0개 허용
- 기본 selected capability 상한 유지
- Skill body는 선택된 경우에만 로드
- 전체 Library body를 정상 task에서 scan/load하지 않음
- Library size 증가만으로 semantic/embedding Router를 추가하지 않음
- Global AGENTS.md는 Expert Catalog 때문에 의미 있게 증가시키지 않음

## 9. 중복 / Domain Pack 관리

같은 목적의 Skill이 여러 Source에 존재할 수 있습니다.

```text
5개 외부 testing Skill 발견
-> 5개 모두 ACTIVE로 설치하지 않음
-> benchmark/reference candidate로 유지
-> 대표 1개 또는 Playbook-adapted 1개 선택
```

Domain Pack은 discovery/benchmark 단위이지 항상 함께 활성화되는 bundle이 아닙니다.

## 10. Self-Managing V8.2와의 관계

V8.3 Catalog는 V8.2 Creator/Evolver/Curator Governance를 우회하지 않습니다.

- External intake 결과는 Proposal/Candidate
- ACTIVE registry silent mutation 금지
- permission/trigger expansion은 기존 Human Gate 적용
- external source update가 자동 ACTIVE update를 의미하지 않음
- upstream 삭제/변경만으로 로컬 Skill 자동 삭제 금지

## 11. 초기 성공 기준

V8.3 Foundation은 다음을 만족하면 완료입니다.

1. 25 Domain Pack taxonomy 정의
2. 최소 6개 고신뢰 Source Registry 작성
3. license/source tier/import policy 기록
4. 외부 Skill body를 ACTIVE에 넣지 않은 상태에서 metadata catalog 가능
5. Benchmark schema/score contract 정의
6. no-skill/current/external/adapted 비교 가능
7. Router/Global Context V8.2 계약 유지
8. external executable 자동 실행 없음
9. 분야별 candidate coverage report 생성 가능
10. Windows verification 전 COMPLETE 표시 금지
