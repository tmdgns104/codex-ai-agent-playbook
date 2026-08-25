# Codex AI Agent Playbook

> **안정 버전: V8.2 (`main`) — COMPLETE / VERIFIED**  
> **현재 개발 버전: V8.3 — Skill Library Expansion 진행 중**

Codex를 여러 프로젝트에서 사용할 때 **거대한 고정 지침과 모든 Skill을 매번 읽지 않고**, 현재 작업에 필요한 기능만 선택해 쓰도록 만든 경량 Playbook + Skills + Harness입니다.

핵심 방향은 아래와 같습니다.

```text
많은 Skill을 보유한다
→ 모든 Skill을 상시 ACTIVE로 두지 않는다
→ Metadata Router가 필요한 Skill만 선택한다
→ 위험도에 따라 검증 강도를 결정한다
→ Git / Test / Artifact Evidence로 완료를 판단한다
```

V8.2는 Windows 실환경 검증을 끝낸 안정판입니다. V8.3은 이 구조를 유지한 채 **Skill Library를 대규모로 확장하되 검증되지 않은 외부 Skill이 곧바로 ACTIVE로 들어오지 못하도록 Catalog → Inspection → Benchmark → Promotion 단계를 강화하는 개발 버전**입니다.

[상세 한글 가이드](README_KO.md) · [빠른 시작](docs/QUICKSTART.md) · [동작 원리](docs/HOW_IT_WORKS.md) · [Skills 가이드](docs/SKILLS.md) · [최신 개발 상태](docs/history/LATEST_STATUS.md) · [개발일지](docs/history/DEVELOPMENT_JOURNAL.md) · [트러블슈팅](docs/history/TROUBLESHOOTING_LOG.md) · [연구기록](docs/history/RESEARCH_LOG.md)

---

## 현재 프로젝트 상태

### 안정판 — V8.2

```text
Stable branch        main
Stable version       V8.2
Status               COMPLETE - VERIFIED
Core Skills          7
Optional Skills      10
Capability wrappers  2
Registry total       12 capabilities
Global AGENTS.md     4579 bytes
Windows verification PASS
```

V8.2의 핵심은 **Self-Managing Skill Library + Deterministic Harness**입니다.

```text
정상 작업
→ Metadata Router
→ 필요한 Skill 0~3개 선택
→ Risk / Permission Gate
→ Codex 실행
→ Repository Verification
→ privacy-safe Event
→ Cleanup
```

```text
유지보수 작업
→ Gap / Evidence 집계
→ Creator / Evolver / Curator Proposal
→ Candidate Audit
→ Protected Regression
→ Promotion Gate
→ Human Gate
```

Creator/Evolver/Curator는 매 작업마다 실행되지 않습니다. 정상 작업 경로는 계속 가볍게 유지합니다.

### 개발판 — V8.3

V8.3은 두 트랙으로 분리해서 진행합니다.

| 트랙 | 브랜치 | 목적 | 현재 상태 |
|---|---|---|---|
| Track A | `v8.3-skill-library-expansion` | 내부 Candidate 확장 | Batch 2A 8개 검증 완료, ACTIVE promotion 전 |
| Track B | `v8.3-expert-skill-catalog` | 외부 Expert Skill 수집·정적검사·Benchmark 준비 | **BENCH-003A COMPLETE - VERIFIED** |

#### Track A 체크포인트

```text
Candidate                8/8
activation regression   72/72
Skill Audit               9/9
skills                   79/79
Harness Audit            PASS
STRICT Gate              PASS / exit 0
```

아직 ACTIVE promotion은 하지 않았습니다.

#### Track B — BENCH-003A 최종 체크포인트

완료 commit:

```text
4e1d92531cebb32a995562e922db50b35e0bcb5f
V8.3: expand expert skill inspection to 50+ ready candidates
```

GitHub 원격 `v8.3-expert-skill-catalog` HEAD도 위 SHA와 동일함을 확인했습니다.

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
working tree              CLEAN before push
```

따라서 BENCH-003A의 수치 목표인 `INSPECTED >= 60`, `BENCHMARK_READY >= 50`, `domain packs >= 20`, `ACTIVE import = 0`, `external scripts executed = false`를 모두 만족했습니다.

---

## 최근 연구·트러블슈팅에서 확인한 내용

### 1. ECC Candidate path drift

기존 Catalog의 다음 4개 경로는 pinned ECC revision에서 실제로 존재하지 않았습니다.

```text
ecc-aws
ecc-azure-bicep
ecc-api-security
ecc-arm-cortex-m
```

비슷한 다른 Skill로 조용히 바꾸지 않고 모두 `REJECTED` Evidence를 남겼습니다.

반면 ECC에는 실제 존재하는 다음 후보가 확인됐습니다.

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

이 후보들은 현재 BENCH-003A 범위에 억지로 넣지 않고 별도 catalog-correction Task로 분리합니다.

### 2. K-Dense 저장소 rename

현재 정식 저장소 이름은 다음으로 확인했습니다.

```text
K-Dense-AI/scientific-agent-skills
```

pinned revision:

```text
390f5146bf3c1877cf15636a3dd7b775e4f0f185
```

도 유효함을 확인했습니다.

추가 8개 후보를 정적검사해 BENCH-003A에 반영했습니다.

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

### 3. `anth-claude-api` 추가 검사

기존 100 Candidate 중 `anth-claude-api`를 Anthropic pinned source에서 정적으로 검사해 `backend-api` domain coverage를 채웠습니다.

- Apache-2.0
- live 사용 시 Anthropic API/network/API key가 필요할 수 있음
- inspection 중 API/network/install/script 실행 없음
- `BENCHMARK_READY`

### 4. 테스트 fixture 하드코딩 문제

`test_uninspected_cluster_member_rejected`가 `anth-claude-api`를 영구적인 “미검사 후보”처럼 하드코딩하고 있어, 실제 inspection에 추가한 뒤 테스트가 실패했습니다.

Validator를 약화하지 않고 fixture를 다음처럼 수정했습니다.

```text
실제 duplicate cluster 멤버 하나 선택
→ temp inspections에서 제거
→ validator가 uninspected member를 거부하는지 확인
```

focused test는 다시 `8/8 PASS`했습니다.

### 5. LF → CRLF 경고와 STRICT Gate

Windows에서 `test_inspection_wave.py`가 LF로 저장되며 Git이 `LF will be replaced by CRLF` 경고를 냈고, Quality Gate의 conflict 검사에서 그 경고가 파일명처럼 읽혀 한 차례 FAIL했습니다.

실제 Git conflict는 없었습니다.

조치:

```text
CRLF 복구
→ Inspection Wave 8/8 재검증
→ STRICT Quality Gate 재실행
→ RESULT PASS
```

검증 로직이나 테스트 강도를 낮추지 않고 파일 줄바꿈만 복구했습니다.

---

## 설치 — Windows CMD

> 설치와 일반 사용은 검증 완료된 안정판 `main` 기준입니다.

필요 프로그램 확인:

```cmd
git --version
python --version
codex --version
```

처음 설치:

```cmd
git clone https://github.com/tmdgns104/codex-ai-agent-playbook.git
cd codex-ai-agent-playbook
git switch main
powershell -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

설치 후 주요 위치:

```text
%USERPROFILE%\.codex\AGENTS.md
%USERPROFILE%\.agents\skills\                 # 7 Core Skills
%USERPROFILE%\.codex\capability-library\      # Optional Skills + wrappers + governance
%USERPROFILE%\.codex\playbook-harness\        # Router / Activation / Quality / Lifecycle
%USERPROFILE%\.codex\.playbook-state\          # local runtime evidence / proposals
```

설치가 끝나면 verification도 자동 실행됩니다.

정상 예:

```text
PASS     global AGENTS.md playbook block
PASS     capability library
PASS     playbook harness
PASS     harness audit
RESULT   PASS
```

---

## 가장 쉬운 사용법

Playbook 설치 후 **실제로 작업할 Git Repository**로 이동합니다.

```cmd
cd /d D:\my-project
```

작업 문장을 Launcher에 전달합니다.

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행"
```

Launcher가 자동으로 다음을 수행합니다.

```text
Task 분류
→ Optional Skill 선택
→ MINIMAL / STANDARD / STRICT 결정
→ Permission Gate
→ 선택 Skill만 임시 노출
→ Codex 실행
→ Event 기록
→ Cleanup
```

실제 Codex 실행 없이 선택 결과만 확인하려면:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행" --dry-run
```

작은 작업은 **Skill 0개**도 정상입니다.

---

## Skill 구성

### Core Skills — 7개

| Skill | 용도 |
|---|---|
| `codex-skill-router` | 애매한 비단순 작업에서 최소 Skill/Profile 추천 |
| `ai-agent-development-playbook` | 복잡한 개발, Architecture, Agent/RAG/Tooling |
| `codex-long-run` | 긴 구현·디버깅·검증 작업과 checkpoint/resume |
| `codex-task-router` | Complexity/Risk/Reasoning/병렬성 판단 |
| `human-readable-code` | 읽기 쉽고 유지보수하기 쉬운 코드 작성 |
| `human-centered-project-builder` | 요구→설계→구현→검증 프로젝트 흐름 |
| `guide-ppt-creator` | 기술/프로젝트 가이드 PPT 제작 |

### Optional Skills — 안정판 ACTIVE 10개

| Skill | 대표 용도 |
|---|---|
| `security-review` | 인증, 권한, secret, 외부 입력, 보안 검토 |
| `testing` | 재현, focused test, regression, acceptance verification |
| `root-cause-debugging` | 증상 수정 전 root cause 추적 |
| `code-review` | 정확성, 회귀, 계약 위반, 검증 누락 검토 |
| `api-design` | REST/GraphQL/OpenAPI/public API contract 설계 |
| `sql-optimization` | 실행계획 기반 SQL/index/N+1 병목 진단 |
| `docker-container` | Dockerfile, image, cache, non-root, secret 검토 |
| `dependency-upgrade` | package/framework upgrade, migration, rollback |
| `performance-profiling` | latency/throughput/CPU/memory profiling과 benchmark |
| `resilient-error-handling` | retry/backoff/timeout/idempotency/circuit breaker |

### Wrapper Capabilities — 2개

| Capability | 용도 |
|---|---|
| `documentation-lookup` | 최신 공식 문서/API 확인이 필요한 작업 |
| `github-ops` | branch/commit/push/PR 등 GitHub 작업 규율 |

전체 설명은 [docs/SKILLS.md](docs/SKILLS.md)를 참고하세요.

---

## V8.3 Skill Library 확장 전략

V8.3의 원칙은 **많이 모으되 천천히 ACTIVE로 승격**하는 것입니다.

```text
Layer 1 — DISCOVERED / Catalog
100~300개 이상 가능

Layer 2 — INSPECTED / BENCHMARK_READY
실제 path / content / license / dependency / permission 확인

Layer 3 — ACTIVE
실제 routing evidence와 promotion gate를 통과한 Skill
```

Library 전체를 Runtime Context에 넣지 않습니다.

```text
Task
→ deterministic metadata router
→ 0~3 skills
→ temporary materialization
```

현재 외부 Expert Catalog는 25개 Domain Pack을 기준으로 관리합니다.

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

---

## 외부 Skill 안전 원칙

- 외부 script/install 자동 실행 금지
- API/credential 사용 없이 정적 inspection 우선
- per-skill license 우선 확인
- Proprietary 또는 불명확 license는 자동 READY 금지
- pinned revision이 resolve되지 않으면 READY 금지
- path가 없으면 비슷한 Skill로 자동 대체 금지
- Skill 이름만 보고 domain 추측 금지
- ACTIVE registry/router/global AGENTS는 inspection 단계에서 변경 금지

---

## 다음 개발 단계

BENCH-003A는 완료됐습니다. 다음 Track B 단계는 **BENCH-004 controlled benchmark / adoption decision**입니다.

```text
BENCH-003A COMPLETE - VERIFIED
→ BENCH-004 controlled benchmark
→ ADOPT / ADAPT / REFERENCE / REJECT 판단
→ 충분한 Evidence가 있는 일부만 promotion 후보
```

새로 발견한 ECC 실존 Skill의 catalog 등록은 BENCH-004에 몰아넣지 않고 별도 catalog-correction Task로 분리하는 원칙을 유지합니다.

---

## 문서

- [README_KO.md](README_KO.md) — 상세 한글 가이드
- [docs/QUICKSTART.md](docs/QUICKSTART.md) — 빠른 시작
- [docs/HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md) — 내부 동작 원리
- [docs/SKILLS.md](docs/SKILLS.md) — Skill 설명
- [docs/history/LATEST_STATUS.md](docs/history/LATEST_STATUS.md) — 최신 상태
- [docs/history/DEVELOPMENT_JOURNAL.md](docs/history/DEVELOPMENT_JOURNAL.md) — 개발일지
- [docs/history/TROUBLESHOOTING_LOG.md](docs/history/TROUBLESHOOTING_LOG.md) — 트러블슈팅
- [docs/history/RESEARCH_LOG.md](docs/history/RESEARCH_LOG.md) — 연구기록

## License

각 외부 Skill은 원본의 license와 사용 조건을 따릅니다. Catalog에 등록됐다는 이유만으로 해당 Skill을 복사·배포·ACTIVE 사용해도 된다는 뜻은 아닙니다.