# 연구기록 — Skill Library Expansion

> 이 문서는 외부 Skill을 어떻게 찾고, 어떤 기준으로 제외/보류/채택 후보로 분류했는지 기록합니다.

## 1. 연구 질문

V8.2 이후 핵심 질문은 다음이었습니다.

> Skill을 많이 모아도 되는가?

결론은 단순한 YES가 아니었습니다.

```text
Library는 크게 가져갈 수 있다.
하지만 ACTIVE는 통제해야 한다.
그리고 Runtime Context에는 필요한 Skill만 materialize해야 한다.
```

즉 문제의 병목은 저장된 Skill 수 자체가 아니라:

- trigger overlap
- routing precision
- permission/risk boundary
- stale metadata
- duplicate workflow
- license/dependency burden

으로 이동했습니다.

---

## 2. Skill Library 계층 전략

현재 목표 구조:

```text
Layer 1 — DISCOVERED / Catalog
100~300개 이상 가능

Layer 2 — INSPECTED / BENCHMARK_READY
실제 path/content/license를 확인한 usable pool

Layer 3 — ACTIVE
실제 routing evidence가 충분한 소수
```

초기 ACTIVE 목표는 20~30 수준으로 보수적으로 유지하고, evidence가 쌓이면 50 → 100 → 200으로 단계 확대하는 전략입니다.

Runtime은 library 전체를 로드하지 않습니다.

```text
Task
→ deterministic metadata router
→ 0~3 skills
→ temporary materialization
```

---

## 3. 외부 Expert Source 조사

### Tier A

#### `agentskills/agentskills`

Agent Skill 형식/생태계 참고.

#### `anthropics/skills`

공식/대표적인 문서형 Skill과 workflow 패턴 참고.

주의:

- source-available / proprietary 계열 문서 Skill 존재 가능
- 공개 저장소라는 이유만으로 재배포/채택 가능하다고 간주하지 않음

#### `NVIDIA/skills`

GPU, DeepStream, Holoscan, AI-Q, HSB 등 강한 도메인 전문성을 보유.

주의:

- GPU/Container/SSH/Hardware side effect
- per-skill license 확인 필요
- script/setup은 inspection 단계에서 실행 금지

### Tier B

#### `K-Dense/scientific-agent-skills`

Scientific Python, research, simulation, data analysis 영역에서 강함.

주의:

- root MIT와 개별 Skill license가 다를 수 있음
- bundled scripts 다수

### Tier C

#### ECC

개발 workflow, verification, coding standards, security, backend patterns 영역에서 강함.

초기 candidate path 정확도 문제가 발견되어 실제 tree 기반 재탐색 필요.

#### `alirezarezvani/claude-skills`

광범위한 engineering/product/research Skill을 제공.

주의:

- repository 변화 속도가 빠름
- symlink/cross-agent layout 존재
- revision/path preflight가 특히 중요

### Discovery 참고

- VoltAgent

---

## 4. 25 Domain Packs

외부 Skill을 무작위로 수집하지 않도록 25개 Domain Pack을 정의했습니다.

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

이 구조의 목적은 단순 개수 경쟁을 막는 것입니다.

```text
Skill 100개
```

보다 중요한 것은:

```text
어느 Domain이 비어 있는가?
어느 Domain에 중복이 과도한가?
실제 전문성이 있는가?
```

입니다.

---

## 5. BENCH-001 — Source Strategy

BENCH-001에서 외부 소스의 역할과 위험도를 정리했습니다.

핵심 정책:

- external full harness auto-install 금지
- 개별 Skill 또는 pattern 단위 inspection
- unknown license는 READY 진입 금지
- external instruction은 우리 governance보다 우선하지 않음
- script/install 자동 실행 금지

---

## 6. BENCH-002 — 100 Candidate Discovery

결과:

```text
Total candidates      100
Domain coverage       23/25
K-Dense               35
NVIDIA                30
alirezarezvani        22
Anthropic              8
ECC                    5
ACTIVE import          0
External scripts       0 executed
```

이 단계의 중요한 의미:

> 100개를 설치한 것이 아니라, 검증할 후보 100개를 확보한 것.

이 구분은 BENCH-003에서 매우 중요해졌습니다.

---

## 7. Candidate 상태 모델

```text
DISCOVERED
↓
INSPECTED
↓
BENCHMARK_READY
↓
ADOPT_CANDIDATE / ADAPT_CANDIDATE / REFERENCE_ONLY / REJECTED
↓
PROMOTED
```

의미:

### BENCHMARK_READY

- path 확인
- revision 확인
- license 검토
- dependency/permission/safety 기록
- benchmark에 넣어볼 가치가 있음

**ACTIVE와 동일하지 않습니다.**

### REFERENCE_ONLY

내용은 참고할 가치가 있지만 license/side effect/구조 때문에 직접 채택 후보로 올리지 않는 상태.

### REJECTED

현재 pinned source 기준으로 경로 부재, 정책 위반, 부적합 등의 이유로 후보에서 제외.

---

## 8. BENCH-003 — 32개 Actual Inspection

결과:

```text
INSPECTED              32
BENCHMARK_READY        28
duplicate clusters      5
shortlist              15
shortlist domains      15
industrial gap        true
ACTIVE import           0
external scripts        0 executed
```

### 대표 shortlist

```text
kd-scientific-writing
kd-dask
kd-exploratory-data-analysis
kd-scikit-learn
kd-pytorch-lightning
kd-sympy
kd-citation-management
kd-scientific-slides
kd-docx
kd-pylabrobot
kd-pydicom
nv-aiq-deploy
nv-holoscan-setup
nv-dynamo-interconnect-check
nv-dynamo-troubleshoot
```

### 검증

```text
inspection tests     30/30
normal regression    72/72
Harness Audit        PASS / warnings 0
STRICT Gate          PASS / exit 0
```

완료 commit:

```text
8c5fc7d8818bf9bdc0b972386d640ded04e9d1e9
```

---

## 9. BENCH-003A — 목표 50+ BENCHMARK_READY

Task baseline:

```text
d8e801f2b668027baafb51f3fbf73507e9e659fe
```

Acceptance target:

```text
INSPECTED >= 60
BENCHMARK_READY >= 50
inspected domain packs >= 20
existing shortlist >= 15
external_scripts_executed = false
ACTIVE import = 0
```

---

## 10. K-Dense Wave 연구 결과

Pinned revision:

```text
390f5146bf3c1877cf15636a3dd7b775e4f0f185
```

추가 inspection 7개:

- kd-statistical-analysis
- kd-pdf
- kd-scientific-visualization
- kd-experimental-design
- kd-hypothesis-generation
- kd-simpy
- kd-pymoo

### 판정

```text
kd-statistical-analysis      BENCHMARK_READY
kd-pdf                       REFERENCE_ONLY
kd-scientific-visualization  BENCHMARK_READY
kd-experimental-design       BENCHMARK_READY
kd-hypothesis-generation     BENCHMARK_READY
kd-simpy                     BENCHMARK_READY
kd-pymoo                     BENCHMARK_READY
```

### `kd-pdf` 교훈

K-Dense root는 MIT 계열이지만 해당 Skill은 per-skill Proprietary로 확인되었습니다.

따라서 root license만 보면 안 됩니다.

---

## 11. NVIDIA Wave 연구 결과

Pinned revision:

```text
7149a886d50da8db72cdc1f20ff01cefeadfe6a9
```

10개 inspection:

- nv-cupynumeric-hdf5
- nv-rtvi-cv-customize-model
- nv-rtvi-cv-scaffold-vss-service
- nv-holohub-debug-build-run
- nv-deepstream-generate-pipeline
- nv-deepstream-profile-pipeline
- nv-hsb-setup
- nv-hsb-app
- nv-aiq-research
- nv-hsb-test

### 결과

```text
BENCHMARK_READY 9
REFERENCE_ONLY  1
```

`nv-rtvi-cv-scaffold-vss-service`는 명시적 `NVIDIA Proprietary`로 REFERENCE_ONLY 처리했습니다.

### Side-effect 연구

NVIDIA Skill은 실무성이 높은 대신 권한 범위가 큽니다.

#### HSB

- SSH remote execution
- Docker
- hardware access
- network configuration
- privileged command 가능성

#### DeepStream

- GPU runtime
- GStreamer
- generated pipeline
- profiling

#### AI-Q

- configurable HTTP backend
- non-local backend trust 필요

따라서 BENCH 단계에서는 모두 **text/fixture-only inspection**으로 제한했습니다.

```text
external_scripts_executed = false
```

---

## 12. ECC 심층 연구

초기 Candidate:

```text
ecc-aws
ecc-azure-bicep
ecc-api-security
ecc-arm-cortex-m
```

각각 다음 path로 catalog되어 있었습니다.

```text
skills/aws
skills/azure-bicep
skills/api-security
skills/arm-cortex-m
```

Pinned revision에서 실제 조회 결과 4개 모두 path가 없었습니다.

### 보안 비공개 가설

처음에는 특정 Skill을 보안상 숨긴 것인지 의심했습니다.

하지만 실제 ECC 저장소의 다른 Skill과 `skills/`, `.agents/skills/` 구조는 정상 공개되어 있었습니다.

결론:

> 보안 비공개보다 discovery path drift / 잘못된 candidate path 가능성이 높음.

### 처리

4개 모두:

```text
REJECTED
upstream-path-missing-at-pinned-revision
```

로 기록했습니다.

### 실제 재탐색에서 발견한 ECC Skill

```text
.agents/skills/api-design
.agents/skills/backend-patterns
.agents/skills/coding-standards
.agents/skills/agent-introspection-debugging
.agents/skills/security-review
skills/deployment-patterns
skills/react-testing
.agents/skills/verification-loop
```

이 후보들은 실제 `SKILL.md` 존재와 실질적 본문을 확인했습니다.

### 의미가 다른 이름 발견

`benchmark-methodology`는 이름만 보면 software benchmark처럼 보이지만 실제 내용은 경쟁사/브랜드 positioning 평가 workflow였습니다.

교훈:

> Skill name이 아니라 본문과 activation contract로 domain을 판정한다.

### Task Scope 결정

BENCH-003A는 기존 100 Candidate inspection이 목적입니다.

따라서 새 ECC 후보는 즉시 추가하지 않고:

```text
003A 완료
→ 별도 ECC catalog-correction Task
```

로 분리하기로 했습니다.

---

## 13. alirezarezvani Source 연구

이 소스는 매우 많은 Skill을 제공하고 변화 속도도 빠릅니다.

2026-08-21 기준 확인된 current commit 예:

```text
98180dafc4f0bc9d629bd479fc6107674cfb3cf8
```

해당 commit 설명에서는 Skill 수가 364까지 증가했고 Codex용 Skill symlink 자동 동기화 이력도 확인됐습니다.

### 발견한 문제

기존 기록에 있던 특정 SHA를 재사용하려 했을 때 GitHub commit/tree API에서 resolve되지 않는 문제가 발견됐습니다.

따라서 이 소스에서는 특히:

```text
revision resolve
→ path resolve
→ symlink/layout 확인
→ inspection
```

순서를 엄격히 적용해야 합니다.

---

## 14. Duplicate 처리 연구

중복 판단 원칙:

```text
목적이 같고
workflow가 같고
실질적 차별점이 없으면
duplicate cluster
```

반대로 다음은 별도 유지할 수 있습니다.

- runtime이 다름
- toolchain이 다름
- permission model이 다름
- domain-specific workflow가 다름
- benchmark에서 비교할 가치가 있음

merge/archive 판단은 BENCH-004에서 수행하고 inspection 단계에서 성급히 합치지 않습니다.

---

## 15. License 처리 연구

우선순위:

```text
1. per-skill explicit license
2. source-specific policy
3. repository root license
```

다음은 READY 차단 요인입니다.

- Proprietary
- Unknown
- source-available이지만 재사용 범위 불명확
- revision/path가 검증되지 않음

REFERENCE_ONLY는 실패가 아닙니다.

> 참고 가치와 채택 가능성을 분리하기 위한 상태입니다.

---

## 16. Dependency / Permission 연구

Skill 품질을 내용만으로 평가하지 않습니다.

각 inspection record에 다음을 기록합니다.

```text
candidate_id
source_id
upstream_path
domain_pack
source_revision
license_status
dependency_burden
dependencies
permissions
network_auth_notes
bundled_scripts
external_scripts_executed
safety_findings
overlap_with_current
provisional_decision
inspection_notes
```

특히 다음은 별도 위험으로 봅니다.

- SSH
- sudo / privileged command
- filesystem write
- credential handling
- network backend
- Docker/container
- GPU runtime
- hardware access
- destructive cleanup

---

## 17. 현재 연구 결론

### 결론 1 — Skill은 많이 모아도 된다

단, lazy materialization과 deterministic router가 유지되어야 합니다.

### 결론 2 — ACTIVE 수를 무작정 늘리면 안 된다

Library 크기보다 routing precision이 먼저 병목이 됩니다.

### 결론 3 — 유명 Repository도 그대로 신뢰하지 않는다

공식/유명 source라도:

- path drift
- proprietary skill
- heavy dependency
- executable side effect

가 존재합니다.

### 결론 4 — Discovery와 Inspection을 분리한 설계는 유효했다

이번 BENCH 과정에서 실제로 잘못된 candidate path와 license 문제를 걸러냈습니다.

### 결론 5 — 외부 Skill은 실행 전에 정적 검증이 먼저다

현재까지 external script 실행은 0을 유지했습니다.

---

## 18. 다음 연구 계획

### BENCH-003A

- 기존 100 Candidate 중 정상 path 후보 추가 검사
- `INSPECTED >=60`
- `BENCHMARK_READY >=50`
- full regression / audit / strict gate

### ECC Catalog Correction

- 실제 recursive tree 기반 후보 생성
- `api-design`, `security-review`, `verification-loop` 등 재등록 검토
- 기존 path-drift candidate 이력은 삭제하지 않고 보존

### BENCH-004

- 동일 목적 Skill 간 benchmark
- ADOPT / ADAPT / REFERENCE 판단
- duplicate cluster merge/archive 제안
- promotion candidate 선정

### 장기

```text
Catalog 100~300+
↓
Verified/Usable 50~100+
↓
ACTIVE는 router evidence에 맞춰 점진 확대
```

연구의 최종 목표는 Skill 숫자 자체가 아닙니다.

> **적은 Context로 더 정확하게 필요한 전문 workflow를 꺼내 쓰는 것**이 목표입니다.
