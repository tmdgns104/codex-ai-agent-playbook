# Codex AI Agent Playbook

> **안정 버전: V8.2 (`main`) — COMPLETE / VERIFIED**  
> **현재 개발 버전: V8.3 — Skill Library Expansion 진행 중**

Codex를 여러 프로젝트에서 사용할 때 **매 작업마다 거대한 지침과 모든 Skill을 읽게 하지 않고**, 현재 작업에 필요한 기능만 선택해 사용하는 경량 Playbook + Skills + Harness입니다.

핵심 방향은 단순합니다.

```text
많은 Skill을 보유한다
→ 모든 Skill을 상시 로드하지 않는다
→ Metadata Router가 필요한 Skill만 선택한다
→ 위험도에 맞는 검증을 수행한다
→ 실제 Git / Test / Artifact Evidence로 완료를 판단한다
```

V8.2는 Windows 실제 환경에서 설치, 자동 Skill 선택, 별도 Git Repository 실행, cleanup, 재설치 멱등성, Self-Managing Skill Lifecycle, STRICT Quality Gate까지 검증된 안정판입니다.

V8.3은 이 구조 위에서 **Skill Library를 대규모로 확장하되, 검증되지 않은 Skill이 ACTIVE로 바로 들어오지 못하도록 Catalog → Inspection → Benchmark → Promotion 단계를 강화하는 개발 버전**입니다.

[상세 한글 가이드](README_KO.md) · [빠른 시작](docs/QUICKSTART.md) · [동작 원리](docs/HOW_IT_WORKS.md) · [Skills 가이드](docs/SKILLS.md) · [최신 개발 상태](docs/history/LATEST_STATUS.md) · [개발 기록](docs/history/README.md) · [문서 작성 정책](docs/DOCUMENTATION_POLICY.md)

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

V8.3은 두 트랙으로 나누어 진행합니다.

| 트랙 | 브랜치 | 목적 | 현재 상태 |
|---|---|---|---|
| Track A | `v8.3-skill-library-expansion` | 내부 Candidate 확장 | Batch 2A 8개 검증 완료, ACTIVE promotion 전 |
| Track B | `v8.3-expert-skill-catalog` | 외부 Expert Skill 수집·정적검사·Benchmark 준비 | BENCH-003A 진행 중 |

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

#### Track B 현재 체크포인트

2026-08-24 기준, 아래 수치는 **현재 로컬 미커밋 Evidence**이며 원격 `v8.3-expert-skill-catalog` HEAD와 의도적으로 구분합니다.

```text
INSPECTED                  53
BENCHMARK_READY            43
ECC path-drift REJECTED     4
EXTERNAL_SCRIPTS_EXECUTED  False
focused inspection tests    8/8 PASS
git diff --check            PASS
```

현재 BENCH-003A 목표:

```text
INSPECTED >= 60
BENCHMARK_READY >= 50
inspected domain packs >= 20
external scripts executed = false
ACTIVE import = 0
```

추가로 K-Dense 후보 8개에 대한 pinned upstream 정적검사는 완료했습니다.

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

8개 모두 `BENCHMARK_READY` 판정이 가능한 상태지만, 아직 로컬 `inspections.json`에는 반영하지 않았습니다. 따라서 공식 로컬 수치는 계속 `53 / 43`이며 **현재 재개 지점은 K-Dense Batch A 반영 직전**입니다.

---

## 최근 연구·트러블슈팅에서 확인한 내용

### ECC Candidate path drift

기존 Catalog에 있던 아래 4개 경로는 pinned ECC revision에서 실제로 존재하지 않았습니다.

```text
ecc-aws
ecc-azure-bicep
ecc-api-security
ecc-arm-cortex-m
```

비슷한 다른 Skill로 조용히 바꾸지 않고 4개 모두 `REJECTED` Evidence를 남겼습니다.

반면 ECC 자체에는 다음과 같은 실존 Skill이 확인되어 후속 Catalog correction 후보로 보존했습니다.

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

### K-Dense 저장소 rename 확인

기존 K-Dense 저장소는 현재 다음 정식 이름으로 이동했습니다.

```text
K-Dense-AI/scientific-agent-skills
```

기존 pinned revision:

```text
390f5146bf3c1877cf15636a3dd7b775e4f0f185
```

은 새 정식 저장소에서도 유효함을 확인했습니다.

### 외부 Skill 정적검사 원칙

- 외부 script/install 자동 실행 금지
- API 호출/credential 사용 금지
- per-skill license 우선 확인
- Proprietary 또는 불명확 license는 자동 READY 금지
- path가 없으면 비슷한 Skill로 자동 대체 금지
- Skill 이름만 보고 domain을 추측하지 않음
- pinned revision의 실제 내용으로 판정

자세한 내용은 [트러블슈팅 기록](docs/history/TROUBLESHOOTING_LOG.md)과 [연구기록](docs/history/RESEARCH_LOG.md)을 참고하세요.

---

## 30초 요약

```text
사용자 작업
   ↓
Deterministic Metadata Router
   ↓
필요한 Optional Skill만 선택 (0~3개)
   ↓
Risk / Permission Gate
   ↓
선택된 Skill만 현재 작업에 임시 활성화
   ↓
Codex 실행
   ↓
Repository Verification / Quality Gate
   ↓
privacy-safe Event 기록
   ↓
Runtime Cleanup
```

작은 작업은 **Skill 0개**도 정상입니다.

```text
README 오타 한 줄 수정
→ MINIMAL / Skill 0개

JWT 인증 오류 수정 + regression test
→ STRICT
→ security-review
→ testing
→ root-cause-debugging
```

사용자가 평소 Skill 이름을 직접 고를 필요가 없습니다.

---

## 설치 — Windows CMD

> 설치와 일반 사용은 검증 완료된 안정판 `main`을 기준으로 합니다.

필요한 프로그램:

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

작업 문장만 전달합니다.

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행"
```

Launcher가 자동으로:

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

을 수행합니다.

### 실제 Codex 실행 없이 선택 결과만 확인

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행" --dry-run
```

Windows 검증 결과:

```text
PROFILE     STRICT
SKILLS      security-review,testing,root-cause-debugging
COUNT       3
BRIDGE      true
DRY_RUN     true
RESULT      READY
CLEANUP     BRIDGE_CLEANED
EVENT       EVENT_SKIPPED
RESULT      DRY_RUN_COMPLETE
```

`--dry-run`은 실제 task를 수행하지 않으므로 lifecycle Event도 기록하지 않습니다.

---

## Skill 구성

### Core Skills — 7개

전역 `%USERPROFILE%\.agents\skills\`에 설치되는 공통 Workflow입니다.

| Skill | 용도 |
|---|---|
| `codex-skill-router` | 애매한 비단순 작업에서 최소 Skill / Profile 추천 |
| `ai-agent-development-playbook` | 복잡한 개발, Architecture, Agent/RAG/Tooling |
| `codex-long-run` | 긴 구현/디버깅/검증 작업과 resume/checkpoint |
| `codex-task-router` | Complexity/Risk/Reasoning/병렬성 판단 |
| `human-readable-code` | 읽기 쉽고 유지보수하기 쉬운 코드 작성 |
| `human-centered-project-builder` | 요구→설계→구현→검증 프로젝트 흐름 |
| `guide-ppt-creator` | 기술/프로젝트 가이드 PPT 제작 |

### Optional Skills — 안정판 ACTIVE 10개

Capability Library에 보관하고, 현재 작업에서 필요할 때만 임시 활성화합니다.

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

`github-ops`처럼 external write가 필요한 Capability는 자동 선택되더라도 권한 Gate를 우회하지 않습니다.

전체 Skill 설명은 [docs/SKILLS.md](docs/SKILLS.md)를 참고하세요.

---

## V8.3 Skill Library 확장 전략

V8.3에서는 **많이 모으되 천천히 ACTIVE로 승격**합니다.

```text
Layer 1 — DISCOVERED / Catalog
100~300개 이상 가능

Layer 2 — INSPECTED / BENCHMARK_READY
실제 path / content / license / dependency / permission을 확인한 usable pool

Layer 3 — ACTIVE
실제 routing evidence와 promotion gate를 통과한 Skill
```

병목은 저장된 Skill 개수 자체가 아니라 다음으로 이동합니다.

```text
trigger overlap
routing precision
permission boundary
stale metadata
duplicate workflow
license / dependency burden
```

Runtime은 Library 전체를 읽지 않고 필요한 Skill만 materialize합니다.

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

## Self-Managing Skill Library

V8.2에서는 Skill Library가 커져도 수동 관리 부담이 폭증하지 않도록 Control Plane을 추가했습니다.

### Control Plane — LLM 없이 동작

```text
Router
Event / Evidence
Gap detection
Proposal Queue
Lifecycle
Skill Audit
Protected Regression
Lock / Base Hash
Promotion Gate
Rollback metadata
```

### Intelligence Plane — 필요할 때만 사용

```text
Skill Creator
Skill Evolver
Skill Curator
```

중요한 안전 경계:

- 한 번의 Router miss만으로 Skill 자동 생성 금지
- Candidate가 ACTIVE Skill을 바로 덮어쓰지 않음
- permission/trigger 확대는 Human Gate
- split/merge/archive는 자동 적용 금지
- raw task text는 lifecycle Event에 저장하지 않음
- target Git Repository에는 self-management telemetry를 만들지 않음

### 유지보수 CLI

설치형 Harness 기준:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" audit
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" gaps
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" proposals
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" curate
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" benchmark --repeats 20
```

Creator/Evolver의 semantic spec은 reviewed input을 전제로 하며, 안정판은 LLM provider를 필수 dependency로 만들지 않습니다.

---

## 검증 Profile

```text
MINIMAL
작고 격리된 저위험 변경

STANDARD
일반적인 비단순 개발

STRICT
보안 / 권한 / 배포 / 마이그레이션 / 중요한 Architecture 변경
```

Skill 수와 Profile은 별개입니다.

---

## Quality Gate

일반 작업:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\quality\quality_gate.py" --repo . --profile standard
```

STRICT + 실제 테스트:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\quality\quality_gate.py" --repo . --profile strict --verify "python -m pytest"
```

Exit code:

```text
0 = PASS
1 = FAIL
2 = UNVERIFIED
```

STRICT인데 실행 Evidence가 필요한 상황에서 `--verify`가 없으면 거짓 PASS 대신 `UNVERIFIED`를 반환합니다.

---

## 업데이트

이미 설치했다면 안정판 Repository에서:

```cmd
git switch main
git pull origin main
powershell -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

변경이 없는 동일 버전 재설치는:

```text
OK       capability library
OK       playbook harness
```

처럼 끝나며 불필요한 backup/재복사를 만들지 않습니다.

설치 상태만 확인:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\verify-install.ps1"
```

---

## 제거

Windows:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\uninstall.ps1"
```

Linux/macOS:

```bash
./uninstall.sh
```

Playbook marker 구간, Core managed Skills, Capability Library, Harness만 제거합니다. 사용자가 `AGENTS.md` marker 밖에 직접 작성한 내용과 backup은 보존합니다.

---

## V8.2 실제 Windows 검증 결과

2026-08-23 최종 안정판에서 확인:

```text
Lifecycle Integration          11/11 PASS
Lifecycle Control Plane         4/4 PASS
Creator                        14/14 PASS
Evolver                        13/13 PASS
Curator                        12/12 PASS
Governance                     12/12 PASS
Event Store                     6/6 PASS
Proposal Queue                  7/7 PASS
Skill Audit                     9/9 PASS
Capability Router              28/28 PASS
Capability Manager             12/12 PASS
Skill Materializer             10/10 PASS
Discovery Bridge               10/10 PASS
Playbook Launcher              12/12 PASS
Installed Launcher              2/2 PASS
Harness Audit                  PASS / warnings 0
STRICT Quality Gate            PASS / exit 0
Global install/reinstall       PASS / idempotent
Arbitrary Git repo JWT routing STRICT / exact 3 skills
Final working tree             clean
```

Metadata Router synthetic benchmark, 20회 평균:

```text
10 skills      0.0586 ms
50 skills      0.2308 ms
100 skills     0.4712 ms
500 skills     2.3551 ms
1000 skills    5.0401 ms
```

현재 결과에서는 semantic/embedding Router를 상시 추가할 필요가 없어 metadata-first 방식을 유지합니다.

---

## 개발 기록과 Source of Truth

프로젝트가 왜 현재 구조가 되었는지는 다음 문서에서 추적할 수 있습니다.

| 문서 | 내용 |
|---|---|
| [최신 개발 상태](docs/history/LATEST_STATUS.md) | 지금 어디까지 진행됐는지, 다음 재개 지점 |
| [개발일지](docs/history/DEVELOPMENT_JOURNAL.md) | V4 → V8.3 설계 변화와 구현 흐름 |
| [트러블슈팅 기록](docs/history/TROUBLESHOOTING_LOG.md) | 증상 → 원인 → 조치 → 검증 → 재발 방지 |
| [연구기록](docs/history/RESEARCH_LOG.md) | 외부 Skill 조사, BENCH 실험, 채택 기준 |
| [문서 작성 정책](docs/DOCUMENTATION_POLICY.md) | 한국어 우선 문서 작성 원칙 |

현재 동작과 계약의 최종 기준은 언제나 Repository Source of Truth입니다.

```text
README.md / README_KO.md
docs/
tasks/
evaluation/
harness/
.codex/AGENTS.md
.agents/skills/
```

개발 기록은 Source of Truth를 대체하지 않고, **왜 그런 결정이 만들어졌는지**를 설명합니다.

---

## 다음 개발 순서

현재 승인된 V8.3 Track B 범위에서 다음 순서로 진행합니다.

```text
1. K-Dense Batch A inspection 반영
2. focused inspection test
3. K-Dense Batch B inspection 반영
4. INSPECTED >= 60 / BENCHMARK_READY >= 50 확인
5. domain coverage / shortlist / catalog test
6. normal routing regression
7. Harness Audit
8. STRICT Quality Gate
9. git diff --check / clean working tree
10. BENCH-003A 완료 commit / push
11. ECC 실제 Skill 재카탈로그화는 후속 별도 Task로 진행
```

검증 전에 ACTIVE promotion이나 Router 변경을 하지 않습니다.

---

## 설계 원칙

```text
적은 영구 Context
+ 많은 검증된 Skill Library
+ 필요한 Capability만 선택
+ Metadata-first Routing
+ LLM-independent Control Plane
+ 위험도에 맞는 검증
+ Repository Source of Truth
+ 실제 Test / Diff / Artifact Evidence
- 모든 Skill 상시 로드
- 검증 전 ACTIVE promotion
- 상시 Multi-Agent
- 자기보고 PASS
```

토큰을 줄이기 위해 정확성이나 검증 신뢰성을 희생하는 방식은 사용하지 않습니다.
