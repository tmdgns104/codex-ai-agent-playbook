# 개발일지 — Codex AI Agent Playbook

> 이 문서는 기능 목록이 아니라 **문제 → 설계 변화 → 구현 → 검증**의 흐름을 기록합니다.

## 1. 시작점 — 좋은 규칙을 많이 넣으면 더 좋아질까?

초기 문제는 단순했습니다.

```text
Codex를 더 잘 쓰고 싶다
→ 좋은 규칙과 Skill을 많이 넣는다
→ 하지만 모든 규칙/Skill을 매번 읽으면 Context와 토큰이 커진다
→ 규칙이 많아질수록 중복, stale instruction, 잘못된 routing 위험도 커진다
```

그래서 방향이 바뀌었습니다.

```text
많이 넣기
→ 필요한 것만 선택하기
→ 선택과 검증을 가능한 한 결정론적으로 만들기
→ Library는 크게 가져가되 ACTIVE는 통제하기
```

현재 핵심 철학은 **많은 지식을 보유하되 정상 작업 경로는 가볍게 유지하는 것**입니다.

---

## 2. V4 — Playbook + Guide PPT

V4에서 프로젝트 개발 흐름을 다음처럼 구조화했습니다.

```text
Problem
→ Requirements
→ Architecture
→ Task Contract
→ Implementation
→ Verification
→ Review
```

`guide-ppt-creator`를 추가하면서 PPT도 바로 결과물을 만드는 대신 Storyboard/Slide/Diagram/Speaker Notes Contract와 Visual/Content QA를 먼저 정의하는 방식을 채택했습니다.

이 단계에서 **결과물보다 먼저 구조와 검증 계약을 세운다**는 원칙이 자리 잡았습니다.

---

## 3. V5 — 사람이 읽을 수 있는 개발

### `human-readable-code`

작동만 하는 코드가 아니라 사람이 읽고 배우고 유지보수할 수 있는 코드를 목표로 했습니다.

- 의미 있는 이름
- 함수/모듈 책임 분리
- 핵심 흐름 가시성
- 불필요한 추상화 금지
- WHY 중심 주석

### `human-centered-project-builder`

```text
Problem
→ Requirements
→ Architecture
→ Task Contract
→ Human-Readable Implementation
→ Test
→ Acceptance Check
→ README / Explanation
→ Evidence
```

Playbook이 단순 프롬프트 모음이 아니라 재사용 가능한 개발 절차가 되기 시작했습니다.

---

## 4. V6 — 장기 작업과 Task Routing 분리

긴 작업에서 세션을 넘어 상태를 이어가기 어렵고, 작업마다 어느 정도 Reasoning/검증/Skill이 필요한지 판단 비용이 커졌습니다.

그래서 다음을 추가했습니다.

### `codex-long-run`

```text
Orient
→ Outcome Contract
→ Small Implementation Loop
→ Focused Verification
→ Meaningful Checkpoint
→ Resume
→ Final Evidence
```

채팅 기억보다 Repository 기반 durable state를 우선합니다.

### `codex-task-router`

Complexity, Uncertainty, Risk, Architecture Impact, Verification Difficulty를 기준으로 최소 충분 route를 추천하도록 분리했습니다.

### Global AGENTS marker

전역 규칙 전체를 덮어쓰지 않고 다음 marker 내부만 관리하도록 했습니다.

```text
<!-- BEGIN AI_AGENT_PLAYBOOK_KIT -->
...
<!-- END AI_AGENT_PLAYBOOK_KIT -->
```

이 구조가 설치/업데이트/제거 시 사용자 커스텀 영역을 보존하는 기반이 됐습니다.

---

## 5. V7 — Context Efficient Global Playbook

V7의 최우선 목표는 **토큰 절감**이었습니다. 단, 검증 강도를 낮추지 않는 조건이 붙었습니다.

책임을 분리했습니다.

```text
항상 필요한 원칙    → Global AGENTS.md
상황별 상세 절차    → Skills
프로젝트별 사실     → Repository
결정론적 검사       → Harness
```

### stale model 정보 제거

모델 이름/Reasoning 표를 영구 저장하지 않고 필요할 때 현재 runtime/catalog를 확인하도록 변경했습니다.

### Windows 설치 멱등성

동일 버전 재설치에서 변경이 없으면 재복사나 새 backup을 만들지 않도록 했습니다.

### backup discovery hazard 해결

이전:

```text
~/.agents/skills/<skill>.backup-<timestamp>
```

변경:

```text
~/.codex/playbook-backups/<timestamp>/
```

Skill discovery path 안에 backup `SKILL.md`가 남아 중복 Skill로 잡히는 위험을 제거했습니다.

---

## 6. V8 — 설명형 Playbook에서 Deterministic Harness로

V8 계열의 가장 큰 변화는 **LLM에게 잘하라고 말하는 것**에서 **코드가 직접 검사하고 통제하는 것**으로 이동한 것입니다.

주요 구성:

```text
MINIMAL / STANDARD / STRICT profile
Quality Gate
Harness Audit
Capability Registry
Metadata Router
Skill Materializer
Permission / Risk Gate
Launcher
Runtime cleanup
privacy-safe event/evidence
```

핵심 계약:

```text
Repository-defined verification
+
Deterministic supplemental checks
```

Harness가 Repository의 실제 test/build를 대체하지 않습니다.

STRICT에서 실행 Evidence가 필요한데 `--verify`가 없으면 거짓 PASS 대신:

```text
0 = PASS
1 = FAIL
2 = UNVERIFIED
```

를 유지합니다.

---

## 7. V8.2 — Self-Managing Skill Library

Skill 수가 늘어도 사람이 모든 Skill을 수동 관리하지 않도록 Control Plane을 추가했습니다.

정상 작업 경로:

```text
Task
→ Metadata Router
→ Skill 0~3개
→ Risk / Permission Gate
→ temporary activation
→ Codex
→ Verification
→ cleanup
```

유지보수 경로:

```text
Evidence / Gap
→ Creator / Evolver / Curator Proposal
→ Candidate
→ Skill Audit
→ Protected Regression
→ Promotion Gate
→ Human Gate
```

안전 경계:

- 한 번의 Router miss로 Skill 자동 생성 금지
- Candidate가 ACTIVE를 바로 덮어쓰지 않음
- permission/trigger 확대는 Human Gate
- raw task text 저장 금지
- target Repository에 self-management telemetry 생성 금지
- split/merge/archive 자동 적용 금지

V8.2 Windows 검증에서 lifecycle, router, materializer, launcher, audit, STRICT gate, install/reinstall 멱등성까지 PASS했습니다.

이 결과로 다음 결론을 얻었습니다.

> **Skill은 많이 모을 수 있다. 다만 모두 ACTIVE로 만들 필요는 없다.**

---

## 8. V8.3 — Skill Library Expansion

V8.3은 두 트랙으로 분리했습니다.

### Track A — 내부 Candidate 확장

브랜치:

```text
v8.3-skill-library-expansion
```

Batch 2A 후보 8개:

```text
python-project-engineering
powershell-windows
api-client-integration
configuration-management
data-analysis-pandas
data-validation
ci-cd-workflow
refactoring
```

체크포인트:

```text
e5a83cdf78a091f68978f46138f402e866bce278
V8.3: register Batch 2A candidate files in manifest
```

검증:

```text
Candidate          8/8
activation         72/72
Skill Audit         9/9
skills             79/79
Harness Audit      PASS
STRICT Gate        PASS / exit 0
```

아직 ACTIVE promotion은 하지 않았습니다.

### Track B — External Expert Skill Catalog

브랜치:

```text
v8.3-expert-skill-catalog
```

목표는 유명 저장소의 Skill을 무작정 복사하는 것이 아니라:

```text
정적 inspection
→ benchmark eligibility
→ controlled benchmark
→ promotion decision
```

으로 분리하는 것입니다.

후보 상태:

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

---

## 9. BENCH-001 — 외부 Expert Source 선정

Tier A:

```text
agentskills/agentskills
anthropics/skills
NVIDIA/skills
```

Tier B:

```text
K-Dense scientific skills
```

Tier C:

```text
ECC
alirezarezvani/claude-skills
```

Discovery 참고:

```text
VoltAgent
```

그리고 25개 Domain Pack을 정의했습니다.

---

## 10. BENCH-002 — 100개 Candidate Catalog

결과:

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

이 단계는 Discovery였습니다.

중요한 교훈:

> Candidate에 들어갔다는 사실은 upstream path/license/content가 검증됐다는 뜻이 아니다.

---

## 11. BENCH-003 — 실제 Upstream Inspection

pinned revision의 실제 파일을 검사했습니다.

완료 결과:

```text
INSPECTED              32
BENCHMARK_READY         28
duplicate clusters       5
shortlist               15
shortlist domains       15
external script exec     0
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
V8.3: complete expert skill inspection verification
```

---

## 12. BENCH-003A — 50+ usable inspection 확장

Task baseline:

```text
d8e801f2b668027baafb51f3fbf73507e9e659fe
V8.3: define 50+ expert skill inspection expansion
```

목표:

```text
INSPECTED >= 60
BENCHMARK_READY >= 50
inspected domain packs >= 20
external scripts executed = false
ACTIVE import = 0
```

### K-Dense 1차 Wave

7개 추가 inspection 후:

```text
INSPECTED        39
BENCHMARK_READY  34
```

`kd-pdf`는 per-skill Proprietary license로 `REFERENCE_ONLY` 처리했습니다.

### NVIDIA Wave

10개 inspection:

```text
9 BENCHMARK_READY
1 REFERENCE_ONLY
```

`nv-rtvi-cv-scaffold-vss-service`는 `NVIDIA Proprietary`라 `REFERENCE_ONLY` 처리했습니다.

중간 결과:

```text
INSPECTED        49
BENCHMARK_READY  43
```

### ECC Path Drift

기존 Catalog의 다음 4개는 pinned revision에 실제 path가 없었습니다.

```text
ecc-aws
ecc-azure-bicep
ecc-api-security
ecc-arm-cortex-m
```

비슷한 Skill로 조용히 대체하지 않고 모두 `REJECTED`로 기록했습니다.

중간 결과:

```text
INSPECTED        53
BENCHMARK_READY  43
```

### ECC 재탐색

실제 트리에서 다음 실존 Skill을 확인했습니다.

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

하지만 BENCH-003A는 기존 100 Candidate inspection 범위이므로 새 후보를 즉시 넣지 않고 별도 catalog-correction Task로 분리했습니다.

### K-Dense 추가 8개

저장소 rename을 확인했습니다.

```text
K-Dense-AI/scientific-agent-skills
```

pinned revision:

```text
390f5146bf3c1877cf15636a3dd7b775e4f0f185
```

추가 검사:

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

Batch A/B로 나눠 반영하고 각 Batch 뒤 focused test를 수행했습니다.

결과:

```text
INSPECTED        61
BENCHMARK_READY  51
DOMAIN_PACKS     19
```

수치 2개는 목표를 넘었지만 domain pack이 1개 부족해 STOP했습니다.

### `anth-claude-api` 검사

기존 100 Candidate 중 아직 검사하지 않은 `anth-claude-api`를 선택했습니다.

```text
source          anthropic-reference-skills
path            skills/claude-api
license         Apache-2.0
domain          backend-api
decision        BENCHMARK_READY
```

inspection 중 network/API/install/script는 실행하지 않았습니다.

최종 수치:

```text
INSPECTED                  62
BENCHMARK_READY            52
INSPECTION_DOMAINS         20
INSPECTION_SOURCES          5
ACTIVE_IMPORTS              0
EXTERNAL_SCRIPTS_EXECUTED   0
```

---

## 13. BENCH-003A 테스트 fixture 문제

`test_uninspected_cluster_member_rejected`는 `anth-claude-api`를 미검사 후보로 하드코딩하고 있었습니다.

실제로 inspection에 추가하자 테스트가 실패했습니다.

원래 validator는 정상적으로:

```text
cluster member가 inspections에 없으면 ExternalCatalogError
```

를 발생시키고 있었습니다.

따라서 validator를 약화하지 않고 fixture만 일반화했습니다.

```text
실제 duplicate cluster member 선택
→ temp inspections에서 해당 member 제거
→ ExternalCatalogError 확인
```

재검증:

```text
Inspection Wave 8/8 PASS
```

---

## 14. BENCH-003A Windows CRLF 문제

STRICT Gate 첫 실행에서 다음이 발생했습니다.

```text
FAIL unresolved Git conflicts:
warning: ... test_inspection_wave.py, LF will be replaced by CRLF ...
```

실제 Git conflict가 아니라 Git warning이 conflict path 출력처럼 읽힌 상황이었습니다.

테스트나 Gate를 낮추지 않고 파일 줄바꿈만 CRLF로 복구했습니다.

재검증:

```text
Inspection Wave          8/8 PASS
STRICT Quality Gate      PASS
git diff --check         PASS
```

---

## 15. BENCH-003A 최종 검증

외부 Catalog 계열:

```text
External Catalog          12/12 PASS
Effective Coverage         5/5 PASS
Candidate Wave             5/5 PASS
Inspection Wave            8/8 PASS
```

V8.2 normal-path regression:

```text
Capability Manager        12/12 PASS
Skill Materializer        10/10 PASS
Discovery Bridge          10/10 PASS
Playbook Launcher         12/12 PASS
Capability Router         28/28 PASS
TOTAL                      72/72 PASS
```

Harness:

```text
Harness Audit             PASS / warnings 0
STRICT Quality Gate       PASS
git diff --check          PASS
working tree              CLEAN before push
```

완료 commit:

```text
4e1d92531cebb32a995562e922db50b35e0bcb5f
V8.3: expand expert skill inspection to 50+ ready candidates
```

원격 `v8.3-expert-skill-catalog` HEAD도 동일 SHA로 검증했습니다.

따라서:

```text
BENCH-003A COMPLETE - VERIFIED
```

로 기록합니다.

---

## 16. 현재 설계 철학

예전:

```text
좋은 Skill이 많을수록 좋다
→ 많이 설치한다
```

현재:

```text
좋은 Skill을 많이 수집한다
→ metadata/catalog에 보관한다
→ 검증된 Candidate만 benchmark한다
→ 필요한 일부만 ACTIVE로 promotion한다
→ runtime에서는 필요한 0~3개만 materialize한다
```

Library 규모와 매 요청의 Context 비용을 분리하는 것이 핵심입니다.

---

## 17. 다음 개발 방향

```text
BENCH-003A COMPLETE - VERIFIED
→ BENCH-004 controlled benchmark
→ ADOPT / ADAPT / REFERENCE / REJECT 판단
→ 충분한 Evidence가 있는 일부만 promotion 후보
```

별도로 ECC 실존 후보를 등록하는 catalog-correction Task를 분리합니다.

원칙은 계속 동일합니다.

> **정확성/검증 신뢰성을 낮추지 않는 범위에서 Context와 토큰을 줄인다.**