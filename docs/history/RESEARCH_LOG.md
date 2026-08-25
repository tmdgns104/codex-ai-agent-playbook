# 연구기록 — Skill Library Expansion

> 이 문서는 외부 Skill을 어떻게 찾고, 어떤 기준으로 제외/보류/채택 후보로 분류했는지 기록합니다.

## 1. 연구 질문

V8.2 이후 핵심 질문은 다음이었습니다.

> Skill을 많이 모아도 되는가?

결론:

```text
Library는 크게 가져갈 수 있다.
하지만 ACTIVE는 통제해야 한다.
Runtime Context에는 필요한 Skill만 materialize해야 한다.
```

즉 병목은 저장된 Skill 수 자체보다 다음으로 이동합니다.

```text
trigger overlap
routing precision
permission/risk boundary
stale metadata
duplicate workflow
license/dependency burden
```

---

## 2. Skill Library 계층 전략

```text
Layer 1 — DISCOVERED / Catalog
100~300개 이상 가능

Layer 2 — INSPECTED / BENCHMARK_READY
path/content/license/dependency/permission을 실제 확인한 usable pool

Layer 3 — ACTIVE
실제 routing evidence와 promotion gate를 통과한 Skill
```

현재 원칙은 **많이 발견하되 천천히 ACTIVE로 승격**하는 것입니다.

---

## 3. 25개 Domain Pack

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

Domain 수를 채우는 것 자체가 목적이 아니라, 실제 활용 가능한 Skill의 coverage를 관리하기 위한 분류입니다.

---

## 4. 외부 Source 계층

### Tier A

```text
agentskills/agentskills
anthropics/skills
NVIDIA/skills
```

### Tier B

```text
K-Dense scientific skills
```

### Tier C

```text
ECC
alirezarezvani/claude-skills
```

### Discovery 참고

```text
VoltAgent
```

Source tier가 높다고 개별 Skill을 자동 신뢰하지 않습니다. 실제 pinned revision의 파일과 license를 다시 확인합니다.

---

## 5. BENCH-002 — 100 Candidate Catalog

초기 catalog 결과:

```text
Candidate            100
covered domains       23/25
K-Dense               35
NVIDIA                30
alirezarezvani        22
Anthropic              8
ECC                    5
ACTIVE import          0
external script exec   0
```

이 단계의 중요한 성격:

```text
DISCOVERY
!=
VERIFICATION
```

이후 실제 inspection에서 path drift와 license 차이가 발견되며 이 구분이 중요하다는 것이 확인됐습니다.

---

## 6. BENCH-003 — 실제 upstream inspection

완료 결과:

```text
INSPECTED              32
BENCHMARK_READY         28
DUPLICATE_CLUSTERS       5
SHORTLIST               15
SHORTLIST_DOMAINS       15
SHORTLIST_SOURCES        2
ACTIVE_IMPORT             0
external scripts          0
```

대표 shortlist:

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

검증:

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

## 7. BENCH-003A 연구 목표

Task baseline:

```text
d8e801f2b668027baafb51f3fbf73507e9e659fe
```

목표:

```text
INSPECTED >= 60
BENCHMARK_READY >= 50
inspected domain packs >= 20
external scripts executed = false
ACTIVE import = 0
```

핵심은 단순히 숫자를 늘리는 것이 아니라 **기존 100 Candidate 안에서 실제 usable pool을 50+로 만드는 것**이었습니다.

---

## 8. K-Dense 연구

### 저장소 rename

기존 이름에서 현재 정식 이름으로 이동했음을 확인했습니다.

```text
K-Dense-AI/scientific-agent-skills
```

pinned revision:

```text
390f5146bf3c1877cf15636a3dd7b775e4f0f185
```

은 새 정식 저장소에서도 유효했습니다.

### 추가 inspection

1차 Wave에서 다음과 같은 후보를 검사했습니다.

```text
kd-statistical-analysis
kd-pdf
kd-scientific-visualization
kd-experimental-design
kd-hypothesis-generation
kd-simpy
kd-pymoo
```

`kd-pdf`는 per-skill Proprietary라 `REFERENCE_ONLY`로 처리했습니다.

추가 Wave:

```text
kd-statsmodels
kd-matplotlib
kd-seaborn
kd-vaex
kd-zarr-python
kd-peer-review
kd-scientific-schematics
kd-infographics
```

### 안전 관찰

- `kd-matplotlib`: bundled scripts 존재 가능, 실행하지 않음
- `kd-seaborn`: `sns.load_dataset()`은 optional network 가능
- `kd-vaex`: optional cloud I/O/credential 가능
- `kd-zarr-python`: remote store 사용 시 network/credential 가능
- `kd-peer-review`: confidential manuscript 취급 주의
- `kd-scientific-schematics`: OpenRouter/Gemini 계열 외부 전송 가능
- `kd-infographics`: OpenRouter/Perplexity 계열 외부 전송 가능

모든 항목은 inspection 중 external script/API/install을 실행하지 않았습니다.

---

## 9. NVIDIA 연구

10개 추가 inspection에서:

```text
9 BENCHMARK_READY
1 REFERENCE_ONLY
```

`nv-rtvi-cv-scaffold-vss-service`는 `NVIDIA Proprietary`라 `REFERENCE_ONLY` 처리했습니다.

관찰된 dependency/permission 특성:

- GPU/runtime 의존 가능
- Docker/SSH/network setup 가능
- DeepStream/Holoscan 등 특정 runtime 필요 가능
- AI-Q backend/API 사용 가능

inspection 단계에서는 실행하지 않고 정적 기록만 남겼습니다.

---

## 10. ECC 연구 — path drift와 실존 후보 분리

초기 Catalog의 다음 후보는 pinned revision에서 경로가 없었습니다.

```text
ecc-aws
ecc-azure-bicep
ecc-api-security
ecc-arm-cortex-m
```

결정:

```text
REJECTED
safety_findings = upstream-path-missing-at-pinned-revision
```

중요한 원칙:

> “비슷한 Skill이 있으니 같은 후보로 치자”라고 처리하지 않는다.

재탐색에서 실제 존재가 확인된 후보:

```text
ecc-api-design
ecc-backend-patterns
ecc-coding-standards
ecc-agent-introspection-debugging
ecc-security-review
ecc-deployment-patterns
ecc-react-testing
ecc-verification-loop
```

이 후보들은 BENCH-003A의 기존 100 Candidate 범위를 깨지 않기 위해 별도 catalog-correction Task로 분리합니다.

---

## 11. Anthropic `anth-claude-api` 연구

BENCH-003A에서 domain pack이 19에 머물러 목표 20을 만족하지 못했습니다.

기존 100 Candidate 중 아직 검사하지 않은 후보를 다시 확인해 `anth-claude-api`를 선택했습니다.

검사 정보:

```text
candidate_id     anth-claude-api
source           anthropic-reference-skills
upstream_path    skills/claude-api
license          Apache-2.0
domain           backend-api
decision         BENCHMARK_READY
```

실제 사용 시에는 Anthropic SDK/raw HTTP, network, `ANTHROPIC_API_KEY`가 필요할 수 있습니다.

하지만 inspection 중에는:

```text
network 실행 없음
API 호출 없음
credential 사용 없음
install 실행 없음
external script 실행 없음
```

을 유지했습니다.

이 후보 추가 후 최종 domain pack coverage는 20이 됐습니다.

---

## 12. Duplicate/overlap 연구

같은 목적과 workflow를 가진 후보가 여러 source에 존재할 수 있습니다.

현재 원칙:

```text
same purpose
+ same workflow
+ meaningful differentiation 없음
→ duplicate cluster 후보
```

반대로 runtime/tool/workflow가 실제로 다르면 별도 후보로 유지할 수 있습니다.

현재 duplicate cluster는 5개이며 실제 merge/archive 판단은 BENCH-004에서 다룹니다.

---

## 13. Test fixture 연구에서 얻은 교훈

`anth-claude-api`를 실제 inspection에 추가하자 `test_uninspected_cluster_member_rejected`가 실패했습니다.

원인은 validator가 아니라 테스트 fixture가 특정 candidate ID를 영구적인 미검사 후보로 가정한 것이었습니다.

개선:

```text
특정 ID 하드코딩 제거
→ 실제 cluster member를 temp inspections에서 제거
→ rejection invariant 검증
```

결과:

```text
Inspection Wave 8/8 PASS
```

교훈:

> Catalog가 성장하는 시스템의 테스트는 “현재 우연히 미검사인 특정 ID”가 아니라 invariant를 검증해야 한다.

---

## 14. Windows 줄바꿈과 Gate 연구

STRICT Gate 첫 실행에서 Git의 LF→CRLF 경고가 conflict 파일처럼 해석돼 FAIL했습니다.

실제 conflict는 없었습니다.

검증을 완화하지 않고 CRLF를 복구한 뒤:

```text
Inspection Wave 8/8 PASS
STRICT Quality Gate PASS
```

를 재확인했습니다.

이 사례는 **환경 경고와 실제 repository state를 구분해서 판정해야 한다**는 점을 보여줍니다.

---

## 15. BENCH-003A 최종 결과

완료 commit:

```text
4e1d92531cebb32a995562e922db50b35e0bcb5f
V8.3: expand expert skill inspection to 50+ ready candidates
```

최종 Evidence:

```text
INSPECTED                  62
BENCHMARK_READY            52
INSPECTION_DOMAINS         20
INSPECTION_SOURCES          5
SHORTLIST                  15
ACTIVE_IMPORTS              0
ACTIVE_REGISTRY_UNCHANGED  True
EXTERNAL_SCRIPTS_EXECUTED   0
```

검증:

```text
External Catalog          12/12 PASS
Effective Coverage         5/5 PASS
Candidate Wave             5/5 PASS
Inspection Wave            8/8 PASS
V8.2 normal regression    72/72 PASS
Harness Audit             PASS / warnings 0
STRICT Quality Gate       PASS
git diff --check          PASS
```

GitHub 원격 `v8.3-expert-skill-catalog` HEAD도 완료 SHA와 동일함을 확인했습니다.

결론:

```text
BENCH-003A COMPLETE - VERIFIED
```

---

## 16. 현재 연구 결론

1. **Skill을 많이 모으는 것 자체는 문제의 핵심이 아니다.**
2. Runtime Context에는 필요한 Skill만 materialize하면 된다.
3. 진짜 병목은 routing precision, overlap, permission, license, stale metadata다.
4. Discovery와 Verification을 분리해야 한다.
5. 공개 저장소라고 개별 Skill license가 자유 사용 가능한 것은 아니다.
6. 외부 Skill은 static inspection을 먼저 하고 실행은 별도 sandbox/Task로 분리해야 한다.
7. 특정 candidate ID보다 invariant 중심 테스트가 Catalog 성장에 더 강하다.
8. 좋은 새 후보를 발견해도 현재 Task 범위를 깨면서 즉시 흡수하지 않는다.

---

## 17. 다음 연구 단계

다음 단계는 **BENCH-004 controlled benchmark / adoption decision**입니다.

```text
BENCH-003A COMPLETE - VERIFIED
→ BENCH-004
→ 실제 benchmark
→ duplicate/overlap 비교
→ dependency/permission burden 비교
→ ADOPT / ADAPT / REFERENCE / REJECT
→ promotion 후보 선정
```

새 ECC 실존 후보 등록은 별도 catalog-correction Task로 분리합니다.

연구 원칙은 유지합니다.

> **많이 발견하고, 엄격히 검사하고, 적게 활성화한다.**