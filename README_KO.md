# Codex AI Agent Playbook Kit — 상세 한글 가이드

> **안정 버전: V8.2 (`main`) — COMPLETE / VERIFIED**  
> **현재 개발 버전: V8.3 — Skill Library Expansion 진행 중**

Codex를 **적은 고정 Context**, **필요한 Capability만 선택하는 구조**, **실제 Evidence 기반 검증**, **Self-Managing Skill Control Plane**으로 여러 프로젝트에서 일관되게 사용하기 위한 전역 Playbook + Skills + Harness입니다.

설치와 일반 사용은 검증 완료된 **V8.2 `main`**을 기준으로 합니다. V8.3은 안정판을 깨지 않고 Skill Library를 확장하기 위한 개발 브랜치에서 진행합니다.

[메인 README](README.md) · [빠른 시작](docs/QUICKSTART.md) · [최신 개발 상태](docs/history/LATEST_STATUS.md) · [개발일지](docs/history/DEVELOPMENT_JOURNAL.md) · [트러블슈팅](docs/history/TROUBLESHOOTING_LOG.md) · [연구기록](docs/history/RESEARCH_LOG.md)

---

## 1. 이 프로젝트가 해결하려는 문제

Codex에 좋은 규칙과 Skill을 계속 추가하면 기능은 늘지만, 모든 내용을 매 작업마다 읽히면 다음 문제가 생깁니다.

```text
Context 증가
→ 토큰 증가
→ 오래된 규칙과 중복 규칙 증가
→ 잘못된 Skill 선택 가능성 증가
→ 유지보수 비용 증가
```

그래서 이 프로젝트는 다음 방향을 사용합니다.

```text
많이 보유한다
→ 상시 로드하지 않는다
→ Metadata만 보고 먼저 선택한다
→ 필요한 Skill만 임시 활성화한다
→ 실제 Test/Git Evidence로 완료를 확인한다
```

최우선 기준은 **정확성/검증 신뢰성을 해치지 않는 범위에서 Context와 토큰을 줄이는 것**입니다.

---

## 2. 안정판 V8.2

```text
Stable branch         main
Stable version        V8.2
Status                COMPLETE - VERIFIED
Core Skills           7
Optional Skills       10
Wrapper Capabilities  2
Registry total        12 capabilities
Global AGENTS.md      4579 bytes
```

V8.2의 정상 실행 경로:

```text
사용자 Task
→ deterministic Metadata Router
→ 필요한 Skill 0~3개 선택
→ MINIMAL / STANDARD / STRICT
→ Permission / Risk Gate
→ 필요한 Skill만 temporary materialization
→ Codex 실행
→ Repository-defined verification
→ deterministic supplemental checks
→ privacy-safe event
→ cleanup
```

작은 작업은 Skill 0개도 정상입니다.

### Self-Managing Skill Library

Skill Library 자체의 유지보수는 정상 실행 경로와 분리합니다.

```text
Evidence / Gap
→ Creator / Evolver / Curator Proposal
→ Candidate
→ Skill Audit
→ Protected Regression
→ Promotion Gate
→ Human Gate
```

자동화가 있다고 해서 Candidate가 ACTIVE를 바로 덮어쓰지 않습니다.

---

## 3. V8.3 개발판

V8.3은 두 트랙으로 나눕니다.

### Track A — 내부 Candidate 확장

브랜치:

```text
v8.3-skill-library-expansion
```

Batch 2A 후보 8개를 등록하고 검증했습니다.

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

Evidence:

```text
Candidate                8/8
activation regression   72/72
Skill Audit               9/9
skills                   79/79
Harness Audit            PASS
STRICT Gate              PASS / exit 0
```

아직 ACTIVE promotion은 하지 않았습니다.

### Track B — External Expert Skill Catalog

브랜치:

```text
v8.3-expert-skill-catalog
```

외부 Skill을 무작정 복사하지 않고 아래 상태를 거칩니다.

```text
DISCOVERED
→ INSPECTED
→ BENCHMARK_READY
→ ADOPT_CANDIDATE / ADAPT_CANDIDATE / REFERENCE_ONLY / REJECTED
→ PROMOTED
```

---

## 4. BENCH-003A 완료 상태

Task baseline:

```text
d8e801f2b668027baafb51f3fbf73507e9e659fe
V8.3: define 50+ expert skill inspection expansion
```

완료 commit:

```text
4e1d92531cebb32a995562e922db50b35e0bcb5f
V8.3: expand expert skill inspection to 50+ ready candidates
```

GitHub 원격 `v8.3-expert-skill-catalog` HEAD도 위 SHA와 동일합니다.

최종 수치:

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

Acceptance Evidence:

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

따라서 BENCH-003A의 목표는 모두 충족했습니다.

---

## 5. 외부 Skill 검사 원칙

외부 Skill은 다음 정보를 확인한 뒤에만 `BENCHMARK_READY` 여부를 판단합니다.

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

안전 규칙:

- 외부 script/install 자동 실행 금지
- API 호출 및 credential 사용 금지
- pinned revision resolve 확인
- path 존재 확인
- per-skill license 우선 확인
- Proprietary/불명확 license 자동 READY 금지
- path가 없으면 비슷한 Skill로 조용히 대체 금지
- Skill 이름만 보고 domain 추측 금지
- inspection 단계에서 ACTIVE registry/router/global AGENTS 변경 금지

---

## 6. BENCH-003A에서 새로 확인한 내용

### K-Dense 저장소 rename

현재 정식 저장소:

```text
K-Dense-AI/scientific-agent-skills
```

pinned revision:

```text
390f5146bf3c1877cf15636a3dd7b775e4f0f185
```

추가 검사한 8개:

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

모두 외부 script/API를 실행하지 않고 정적으로 검사했습니다.

### Anthropic `anth-claude-api`

기존 100 Candidate 중 `anth-claude-api`를 추가 검사해 `backend-api` domain coverage를 채웠습니다.

```text
license       Apache-2.0
decision      BENCHMARK_READY
network       live 사용 시 필요 가능
API key       live 사용 시 필요 가능
inspection    network/API/install/script 실행 없음
```

### ECC path drift

다음 기존 후보는 pinned revision에서 경로가 존재하지 않아 `REJECTED` 처리했습니다.

```text
ecc-aws
ecc-azure-bicep
ecc-api-security
ecc-arm-cortex-m
```

실제 ECC 트리에서 별도로 확인된 후보:

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

현재 BENCH-003A의 기존 100 Candidate 범위를 지키기 위해 새 후보 등록은 별도 catalog-correction Task로 분리합니다.

---

## 7. 테스트 fixture와 CRLF 트러블슈팅

### fixture 하드코딩

기존 테스트는 `anth-claude-api`를 영구적인 미검사 candidate처럼 하드코딩했습니다.

실제로 `anth-claude-api`를 inspection에 추가하자 테스트가 실패했습니다.

Validator를 약화하지 않고 다음 방식으로 바꿨습니다.

```text
duplicate cluster의 실제 member 선택
→ temp inspections에서 해당 member 제거
→ validator가 uninspected member를 거부하는지 확인
```

수정 후:

```text
Inspection Wave 8/8 PASS
```

### LF → CRLF

Windows에서 테스트 파일이 LF로 저장되며 Git 경고가 발생했습니다.

```text
LF will be replaced by CRLF
```

Quality Gate가 이 경고를 conflict 파일처럼 읽어 한 차례 FAIL했지만 실제 Git conflict는 아니었습니다.

테스트/검증 강도를 낮추지 않고 파일만 CRLF로 복구했습니다.

```text
CRLF 복구
→ Inspection Wave 8/8 PASS
→ STRICT Quality Gate PASS
```

---

## 8. 설치 방법

> 일반 사용자는 안정판 `main`을 설치합니다.

### 준비 확인

```cmd
git --version
python --version
codex --version
```

### Clone

```cmd
git clone https://github.com/tmdgns104/codex-ai-agent-playbook.git
cd codex-ai-agent-playbook
git switch main
```

### 설치

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

설치 후 위치:

```text
%USERPROFILE%\.codex\AGENTS.md
%USERPROFILE%\.agents\skills\
%USERPROFILE%\.codex\capability-library\
%USERPROFILE%\.codex\playbook-harness\
%USERPROFILE%\.codex\.playbook-state\
```

동일 버전을 다시 설치해도 변경이 없으면 불필요한 backup/복사를 만들지 않도록 멱등화되어 있습니다.

---

## 9. 실제 사용 방법

작업할 Repository로 이동합니다.

```cmd
cd /d D:\my-project
```

Launcher 실행:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행"
```

실제 Codex 실행 없이 routing만 보고 싶으면:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행" --dry-run
```

예상 흐름:

```text
PROFILE     STRICT
SKILLS      security-review,testing,root-cause-debugging
COUNT       3
BRIDGE      true
DRY_RUN     true
RESULT      READY
CLEANUP     BRIDGE_CLEANED
RESULT      DRY_RUN_COMPLETE
```

---

## 10. Quality Gate

Quality Gate는 Repository의 실제 test를 대체하지 않습니다.

STRICT에서는 명시적인 실행 Evidence가 없으면 `UNVERIFIED`를 반환합니다.

```text
0 = PASS
1 = FAIL
2 = UNVERIFIED
```

예:

```cmd
python harness\quality\quality_gate.py --repo . --profile strict --verify "python -m unittest"
```

핵심은 다음입니다.

```text
Repository-defined verification
+
Deterministic supplemental checks
```

---

## 11. Skill 구성

### Core Skills 7개

```text
codex-skill-router
ai-agent-development-playbook
codex-long-run
codex-task-router
human-readable-code
human-centered-project-builder
guide-ppt-creator
```

### V8.2 Optional ACTIVE 10개

```text
security-review
testing
root-cause-debugging
code-review
api-design
sql-optimization
docker-container
dependency-upgrade
performance-profiling
resilient-error-handling
```

### Wrapper 2개

```text
documentation-lookup
github-ops
```

V8.3 Candidate가 많아져도 일반 사용 시 이 목록 전체를 Context에 넣지 않습니다.

---

## 12. V8.3 Library 확장 목표

```text
Layer 1  DISCOVERED        100~300+
Layer 2  VERIFIED/USABLE   50~100+
Layer 3  ACTIVE            처음에는 20~30 수준부터 점진 확대
```

병목은 저장 개수보다 다음에 있습니다.

```text
routing precision
trigger overlap
permission boundary
stale metadata
duplicate workflow
license/dependency burden
```

그래서 ACTIVE 확대는 반드시 benchmark와 promotion evidence를 거칩니다.

---

## 13. 다음 단계

Track B의 다음 단계는 **BENCH-004 controlled benchmark / adoption decision**입니다.

```text
BENCH-003A COMPLETE - VERIFIED
→ BENCH-004
→ 실제 비교 benchmark
→ ADOPT / ADAPT / REFERENCE / REJECT
→ promotion 후보 선정
```

새 ECC 실존 Skill 등록은 별도 catalog-correction Task로 분리합니다.

---

## 14. 문서 위치

```text
README.md
README_KO.md
docs/QUICKSTART.md
docs/HOW_IT_WORKS.md
docs/SKILLS.md
docs/DOCUMENTATION_POLICY.md
docs/history/README.md
docs/history/LATEST_STATUS.md
docs/history/DEVELOPMENT_JOURNAL.md
docs/history/TROUBLESHOOTING_LOG.md
docs/history/RESEARCH_LOG.md
```

GitHub에 표시되는 설명 문서는 한국어를 기본으로 하고, 코드/명령/경로/Skill ID/status enum/SHA처럼 정확성이 필요한 식별자는 원문을 유지합니다.