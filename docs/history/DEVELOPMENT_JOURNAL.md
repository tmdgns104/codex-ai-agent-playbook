# 개발일지 — Codex AI Agent Playbook

> 이 문서는 기능 목록이 아니라 **문제 → 설계 변화 → 구현 → 검증**의 흐름을 기록합니다.

## 1. 프로젝트가 해결하려던 문제

초기 문제는 단순했습니다.

```text
Codex를 더 잘 쓰고 싶다
↓
좋은 규칙과 Skill을 많이 넣는다
↓
하지만 모든 규칙/Skill을 매번 읽으면 Context와 토큰이 커진다
↓
규칙이 많아질수록 중복, 오래된 지침, 잘못된 routing 위험도 커진다
```

그래서 방향이 바뀌었습니다.

```text
많이 넣기
→ 필요한 것만 선택하기
→ 선택과 검증을 가능한 한 결정론적으로 만들기
→ Skill Library는 크게 가져가되 ACTIVE는 통제하기
```

현재 Playbook의 핵심은 **많은 지식을 보유하되, 정상 작업 경로는 가볍게 유지하는 것**입니다.

---

## 2. V4 — Playbook + Guide PPT

`V4_CHANGES_KO.md`에서 추적 가능한 시작점입니다.

V4는 기존 AI Agent Development Playbook에 `guide-ppt-creator`를 추가했습니다.

핵심 구조:

```text
Problem
→ Requirements
→ Architecture
→ Task Contract
→ Implementation
→ Verification
→ Review
```

PPT 작업도 바로 `.pptx`부터 만들지 않고 다음 Contract를 거치도록 했습니다.

- Storyboard Contract
- Slide Contract
- Diagram Contract
- Speaker Notes Contract
- Visual QA
- Content QA

이때부터 프로젝트 전반에 **결과물보다 먼저 구조와 검증 계약을 세운다**는 성향이 나타났습니다.

---

## 3. V5 — 사람이 읽을 수 있는 개발

V5에서 두 Skill이 추가됐습니다.

### `human-readable-code`

작동만 하는 코드가 아니라 사람이 읽고 배우고 유지보수할 수 있는 코드를 목표로 했습니다.

- 의미 있는 이름
- 함수/모듈 책임 분리
- 핵심 실행 흐름 가시성
- 불필요한 추상화 금지
- WHY 중심 주석
- 구현 후 설명

### `human-centered-project-builder`

설계와 구현을 한 흐름으로 연결했습니다.

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

이 단계에서 Playbook은 단순 프롬프트 모음이 아니라 **개발 절차를 재사용하는 Skill 세트**가 되기 시작했습니다.

---

## 4. V6 — 장기 작업과 Task Routing 분리

실제 Codex 장기 작업에서 두 문제가 반복됐습니다.

1. 긴 작업을 여러 세션/사이클에 걸쳐 이어가기 어렵다.
2. 작업마다 어느 정도의 Reasoning/검증/Skill이 필요한지 판단 비용이 든다.

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

핵심은 채팅 기억보다 **Repository 기반 durable state**를 우선하는 것입니다.

### `codex-task-router`

Complexity, Uncertainty, Risk, Architecture Impact, Verification Difficulty 등을 기준으로 최소 충분 route를 추천하도록 분리했습니다.

### Global AGENTS marker 구조

전역 규칙을 통째로 덮어쓰지 않고 다음 marker 내부만 관리하도록 했습니다.

```text
<!-- BEGIN AI_AGENT_PLAYBOOK_KIT -->
...
<!-- END AI_AGENT_PLAYBOOK_KIT -->
```

이 결정은 이후 설치/업데이트/제거에서 사용자 커스텀 영역을 보존하는 기반이 됐습니다.

### GitHub 문서 구조

V6에서 현재 문서 구조의 뼈대가 생겼습니다.

```text
README.md
docs/QUICKSTART.md
docs/HOW_IT_WORKS.md
docs/SKILLS.md
docs/DEVELOPMENT.md
```

---

## 5. V7 — Context Efficient Global Playbook

V7의 최우선 목표는 **토큰 절감**이었습니다. 단, 검증 강도를 낮추지 않는 조건이 붙었습니다.

핵심 분리:

```text
항상 필요한 원칙    → Global AGENTS.md
상황별 상세 절차    → Skills
프로젝트별 사실     → Repository
결정론적 검사       → Harness
```

### 전역 Context 축소

항상 필요한 원칙만 남겼습니다.

- Repository Source of Truth
- 한 번에 하나의 coherent outcome
- 요구/Architecture 임의 변경 금지
- Evidence 기반 완료
- Human Gate
- minimum sufficient context
- minimum Skill selection

### stale model 정보 제거

Task Router에 모델 이름/Reasoning 표를 영구 저장하면 제품 변화에 따라 낡을 수 있었습니다.

그래서 영구 모델표를 제거하고 필요할 때 현재 runtime/catalog를 확인하도록 변경했습니다.

### Windows 설치 멱등성

동일 버전 재설치에서 변경이 없으면:

- 재복사하지 않음
- backup을 새로 만들지 않음

### backup discovery hazard 해결

이전에는 Skill 검색 경로 아래 backup에도 `SKILL.md`가 남아 중복 Skill로 발견될 수 있었습니다.

```text
이전
~/.agents/skills/<skill>.backup-<timestamp>

변경
~/.codex/playbook-backups/<timestamp>/
```

### `verify-install.ps1`

GitHub Repository와 실제 PC 전역 적용본의 drift를 비교하는 검증 도구를 추가했습니다.

---

## 6. V8 계열 — 설명형 Playbook에서 Deterministic Harness로

V8 계열의 가장 큰 변화는 **LLM에게 잘하라고 말하는 것**에서 **코드가 직접 검사하고 통제하는 것**으로 이동한 것입니다.

주요 구성:

- MINIMAL / STANDARD / STRICT profile
- deterministic Quality Gate
- Harness Audit
- Capability Registry
- Metadata Router
- Materialization / temporary activation
- Permission/Risk Gate
- Launcher
- Runtime cleanup
- privacy-safe event/evidence

중요한 원칙:

```text
Repository-defined test
+
Deterministic supplemental checks
```

Harness가 Repository 테스트를 대체하지 않습니다.

STRICT에서 실행 Evidence가 필요한데 실제 검증 명령이 없으면 거짓 PASS 대신 `UNVERIFIED`를 유지하는 계약을 채택했습니다.

```text
0 = PASS
1 = FAIL
2 = UNVERIFIED
```

---

## 7. V8.2 — Self-Managing Skill Library

V8.2에서는 Skill 수가 계속 증가해도 사람이 모든 Skill을 수동 관리하지 않도록 Control Plane을 추가했습니다.

### 정상 작업 경로

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

### 유지보수 경로

```text
Evidence / Gap
→ Creator / Evolver / Curator Proposal
→ Candidate
→ Skill Audit
→ Protected Regression
→ Promotion Gate
→ Human Gate
```

### 중요한 안전 경계

- 한 번의 Router miss로 Skill 자동 생성 금지
- Candidate가 ACTIVE를 바로 덮어쓰지 않음
- permission/trigger 확대는 Human Gate
- raw task text 저장 금지
- target Repository에 self-management telemetry를 만들지 않음
- split/merge/archive 자동 적용 금지

### 실제 Windows 검증

V8.2 최종 검증에서 lifecycle, creator/evolver/curator, router, materializer, launcher, audit, STRICT gate, install/reinstall 멱등성까지 PASS했습니다.

Metadata Router benchmark에서도 Skill 수가 1000개 수준일 때 수 ms 수준으로 유지되어, 상시 embedding/semantic router를 추가할 필요가 없다고 판단했습니다.

이 결과가 이후 전략의 근거가 됐습니다.

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

- python-project-engineering
- powershell-windows
- api-client-integration
- configuration-management
- data-analysis-pandas
- data-validation
- ci-cd-workflow
- refactoring

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

목표는 유명 저장소의 Skill을 무작정 복사하는 것이 아니라 **정적 inspection → benchmark eligibility → 별도 promotion** 흐름을 만드는 것입니다.

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

선정 소스:

### Tier A

- `agentskills/agentskills`
- `anthropics/skills`
- `NVIDIA/skills`

### Tier B

- `K-Dense/scientific-agent-skills`

### Tier C

- ECC
- `alirezarezvani/claude-skills`

Discovery 참고:

- VoltAgent

그리고 25개 Domain Pack을 정의했습니다.

예:

- documentation-guide
- data-analysis
- machine-learning
- computer-vision
- edge-ai-nvidia
- rag-llm-agent
- backend-api
- database-sql
- devops-container
- testing-qa
- security-auth
- embedded-iot
- robotics-ros
- industrial-automation
- networking
- scientific-computing

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

이 단계는 **Discovery**였습니다.

중요한 교훈은 뒤에서 나왔습니다.

> Candidate에 들어갔다는 사실은 upstream path/license/content가 검증됐다는 뜻이 아니다.

---

## 11. BENCH-003 — 실제 Upstream Inspection

BENCH-003에서 처음으로 pinned revision의 실제 파일을 직접 검사했습니다.

완료 결과:

```text
inspected             32
BENCHMARK_READY       28
duplicate clusters     5
shortlist             15
shortlist domains     15
external script exec   0
```

대표 shortlist:

- kd-scientific-writing
- kd-dask
- kd-exploratory-data-analysis
- kd-scikit-learn
- kd-pytorch-lightning
- kd-sympy
- kd-citation-management
- kd-scientific-slides
- kd-docx
- kd-pylabrobot
- kd-pydicom
- nv-aiq-deploy
- nv-holoscan-setup
- nv-dynamo-interconnect-check
- nv-dynamo-troubleshoot

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

### K-Dense Wave

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

`nv-rtvi-cv-scaffold-vss-service`는 `NVIDIA Proprietary`라서 REFERENCE_ONLY 처리했습니다.

결과:

```text
INSPECTED        49
BENCHMARK_READY  43
NVIDIA_WAVE      10/10
external scripts false
```

### ECC Path Drift

Catalog에 있던 다음 4개는 pinned revision에 실제 path가 없었습니다.

```text
ecc-aws          -> skills/aws
ecc-azure-bicep  -> skills/azure-bicep
ecc-api-security -> skills/api-security
ecc-arm-cortex-m -> skills/arm-cortex-m
```

비슷한 Skill로 조용히 대체하지 않고 4개 모두 `REJECTED`로 기록했습니다.

로컬 체크포인트:

```text
INSPECTED        53
BENCHMARK_READY  43
focused tests     8/8 PASS
git diff --check PASS
```

---

## 13. ECC 재탐색에서 확인한 실존 Skill

심층 재탐색으로 다음과 같은 실제 Skill이 존재함을 확인했습니다.

- `.agents/skills/api-design`
- `.agents/skills/backend-patterns`
- `.agents/skills/coding-standards`
- `.agents/skills/agent-introspection-debugging`
- `.agents/skills/security-review`
- `skills/deployment-patterns`
- `skills/react-testing`
- `.agents/skills/verification-loop`

하지만 BENCH-003A는 **기존 100 Candidate inspection**이 Task 범위이므로, 새 ECC 후보를 즉시 추가하면 현재 Task 범위를 넓히게 됩니다.

결정:

```text
003A 먼저 완료
→ 새 ECC 실존 후보는 별도 catalog-correction Task에서 등록
```

---

## 14. 현재 설계 철학

프로젝트가 발전하면서 가장 크게 바뀐 생각은 다음과 같습니다.

### 예전

```text
좋은 Skill이 많을수록 좋다
→ 많이 설치한다
```

### 현재

```text
좋은 Skill을 많이 수집한다
→ metadata/catalog에 보관한다
→ 검증된 Candidate만 benchmark한다
→ 필요한 일부만 ACTIVE로 promotion한다
→ runtime에서는 필요한 0~3개만 materialize한다
```

이 구조 덕분에 Library를 100개, 200개 이상으로 키우는 것과 **매 요청의 Context 비용**을 분리할 수 있습니다.

---

## 15. 다음 개발 방향

1. BENCH-003A 목표 `INSPECTED >=60 / READY >=50` 완료
2. 정상 path를 가진 기존 Candidate 추가 검사
3. full regression / Harness Audit / STRICT Gate
4. 003A Evidence commit
5. ECC catalog correction Task 분리
6. BENCH-004에서 실제 benchmark/adopt/adapt 판단
7. 충분한 router Evidence를 확보한 뒤 ACTIVE 규모를 점진 확대

원칙은 계속 동일합니다.

> **정확성/검증 신뢰성을 낮추지 않는 범위에서 Context와 토큰을 줄인다.**
