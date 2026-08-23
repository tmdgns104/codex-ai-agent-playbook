# 동작 원리 - V8.2

Codex AI Agent Playbook V8.2는 하나의 거대한 Prompt가 아니라 **항상 필요한 작은 전역 규칙**, **필요할 때만 활성화되는 Capability**, **LLM 없이 동작하는 Self-Managing Control Plane**을 분리합니다.

핵심 목표:

```text
Context 비용은 줄이고
검증 신뢰성은 유지하거나 높이며
Skill Library가 커져도 정상 task path는 가볍게 유지
```

---

## 전체 구조

### Normal Task Path

```text
User Task
   ↓
Global Working Agreement
   ↓
Deterministic Capability Router
   ↓
Minimum Capability Plan
   ↓
Risk / Permission Gate
   ↓
Selected Optional Skill Materialization
   ↓
Task-scoped Codex Discovery Bridge
   ↓
Codex Execution
   ↓
Repository Verification
   ↓
Deterministic Quality Gate
   ↓
privacy-safe Event
   ↓
Managed Cleanup
```

### Self-Managing Maintenance Path

```text
Events / Gap / Failure / Correction
              ↓
Deterministic Control Plane
              ↓
Proposal Queue / Lifecycle
              ↓
Creator / Evolver / Curator
              ↓
Candidate
              ↓
Skill Audit
              ↓
Protected Regression
              ↓
Promotion Gate / Human Gate
              ↓
ACTIVE Library
```

Creator/Evolver/Curator는 정상 task 시작 시 상시 실행되지 않습니다.

---

## 1. Global Working Agreement

전역 `.codex/AGENTS.md`에는 모든 작업에서 정말 필요한 원칙만 둡니다.

대표 원칙:

- Repository를 durable Source of Truth로 사용
- 현재 Task 밖 변경 최소화
- Architecture/요구사항/보안 경계 변경은 Human Gate
- 자기 보고가 아니라 Test/Evidence로 완료 판단
- 필요한 Skill만 사용
- Context를 제한된 자원으로 취급
- 단순 작업에 과한 절차를 강제하지 않음

설치 스크립트는 사용자 `AGENTS.md` 전체를 덮어쓰지 않고 Playbook marker 구간만 관리합니다.

V8.2 최종 Windows 검증 기준 Playbook 전역 영역은 **4579 bytes**입니다.

---

## 2. Core Skill과 Optional Capability 분리

### Core Skills

`%USERPROFILE%\.agents\skills\`에 설치되는 **7개 managed Skill**입니다.

```text
ai-agent-development-playbook
codex-long-run
codex-skill-router
codex-task-router
guide-ppt-creator
human-centered-project-builder
human-readable-code
```

### Optional Skills

`%USERPROFILE%\.codex\capability-library\skills\optional\`에 보관하는 **10개 Skill**입니다.

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

### Wrappers

Registry에는 Skill 외에 두 Capability가 더 있습니다.

```text
documentation-lookup   rest-wrapper
github-ops             cli-wrapper
```

따라서 Registry 전체는 **12 capabilities**입니다.

Library에 존재한다고 해서 Codex가 매 작업에서 모두 읽는 것은 아닙니다.

---

## 3. Deterministic Capability Router

Router는 Capability 본문이 아니라 짧은 `registry.json` metadata를 먼저 읽습니다.

대표 metadata:

```text
id
type
summary
domains
triggers
risk
recommended_profile
permissions
context_cost
path
```

초기 판단에는 LLM API를 사용하지 않습니다.

작업 문장과 trigger/domain metadata를 비교해 필요한 Capability를 점수화합니다.

기본 원칙:

```text
Capability 0개 허용
Optional Skill 최대 3개
Metadata-first
Semantic router는 기본 path에 없음
```

2026-08-23 Windows synthetic benchmark 20회 평균:

```text
10 skills      0.0586 ms
50 skills      0.2308 ms
100 skills     0.4712 ms
500 skills     2.3551 ms
1000 skills    5.0401 ms
```

현재 결과에서는 semantic/embedding Router를 상시 추가할 근거가 없어 metadata-first 방식을 유지합니다.

---

## 4. 선택 예시

### 단순 작업

```text
README 오타 한 줄 수정
```

대표 결과:

```text
PROFILE MINIMAL
SKILLS none
COUNT 0
```

### 보안/테스트/디버깅 작업

```text
JWT 인증 오류를 수정하고 regression test를 실행
```

실제 Windows 검증 결과:

```text
PROFILE STRICT
SKILLS security-review,testing,root-cause-debugging
COUNT 3
```

필요한 것만 선택합니다.

---

## 5. Risk / Permission Gate

Router가 Skill을 골랐다고 해서 민감 권한까지 자동 승인하지 않습니다.

대표 Gate:

```text
AUTO_ALLOWED
PROFILE_GATED
NETWORK_REVIEW
MANUAL_ONLY
HUMAN_GATE_REQUIRED
```

민감 권한 예:

```text
credential_access
external_write
database_write
destructive
production
network
browser_control
```

따라서:

```text
Skill 자동 선택
≠
권한 자동 승인
```

입니다.

`github-ops`처럼 external write가 필요한 Capability는 Gate가 자동 실행을 막을 수 있습니다.

---

## 6. Skill Materialization

Gate를 통과한 Optional Skill만 현재 session runtime으로 복사합니다.

개념:

```text
<target-repo>/.playbook-runtime/<session>/
```

안전 조건:

- target repo에 전체 capability-library를 복사하지 않음
- Optional Skill을 전역 `.agents/skills`에 모두 영구 설치하지 않음
- 선택되지 않은 Skill은 session에 노출하지 않음
- source path가 capability-library 밖으로 escape하지 못함

---

## 7. Codex Discovery Bridge

Codex가 Repository hierarchy의 `.agents/skills`를 탐색할 수 있는 특성을 이용해 task-scoped bridge를 만듭니다.

```text
Target Repository
└─ .playbook-runtime/
   └─ <session>/
      └─ cwd/
         └─ .agents/
            └─ skills/
               └─ <선택된 Optional Skill만>
```

Launcher는 대략 다음 구조로 Codex를 실행합니다.

```text
codex -C <bridge-cwd> --add-dir <target-repo> -- "<task>"
```

이 방식으로 기존 Repository 작업 범위는 유지하면서 선택된 Optional Skill만 추가 discovery합니다.

---

## 8. Installed Launcher

실제 작업할 Git Repository에서:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "<작업>"
```

Launcher는 자기 설치 위치를 기준으로 자동으로:

```text
%USERPROFILE%\.codex\capability-library
```

를 찾습니다.

Playbook source Repository와 실제 작업 Repository는 서로 달라도 됩니다.

V8.2는 별도의 임의 Git Repository에서도 이 동작을 검증했습니다.

---

## 9. Dry-run

실제 Codex를 실행하지 않고 Router / Gate / Bridge 결과만 확인할 수 있습니다.

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행" --dry-run
```

V8.2에서는 dry-run이면 실제 task가 실행되지 않았으므로:

```text
EVENT EVENT_SKIPPED
```

가 정상입니다.

---

## 10. Post-task Event

실제 Codex 실행 후 Self-Managing Layer가 사용할 최소 Event를 best-effort로 기록합니다.

대표 Event:

```text
selected Skill + exit 0   → verified_usage
selected Skill + exit !=0 → verification_failure
no Skill                  → capability_gap
explicit correction       → user_correction
```

저장 대상:

- task fingerprint
- selected Skill ids
- verification outcome
- explicit correction marker
- timestamp / issue code

저장하지 않는 것:

- raw task text
- credential
- 대화 전체 원문

Event 기록 실패는 정상 Codex task의 exit/result를 변경하지 않습니다.

---

## 11. Runtime State 위치

Self-Managing telemetry는 target Git Repository가 아니라 catalog root에 둡니다.

Global 설치:

```text
%USERPROFILE%\.codex\.playbook-state\
```

따라서 임의 target Repository에 lifecycle telemetry 때문에 untracked 파일을 만들지 않습니다.

---

## 12. LLM-Independent Control Plane

다음은 LLM 없이 Python/파일 기반으로 동작합니다.

```text
Registry loading/validation
Metadata Router
Permission/Risk Gate
Event/Evidence append
Gap detection
Proposal Queue
Lifecycle state validation
Skill statistics
Trigger overlap inspection
Source/license/provenance inspection
Candidate Audit
Protected Regression
Base Hash
One-writer Lock
Promotion Gate
Rollback metadata
```

Codex/API quota가 없어도 Control Plane은 계속 동작할 수 있게 설계되어 있습니다.

---

## 13. Creator

Creator는 반복되는 실제 Capability Gap에서 새 Skill Candidate를 제안합니다.

주요 계약:

- 한 번의 Router miss만으로 자동 생성하지 않음
- distinct Evidence가 반복되어야 함
- reusable workflow가 아니면 생성하지 않음
- 기존/근접 Skill로 해결 가능하면 새 Skill보다 extension 검토 우선
- source/license/provenance 확인
- Candidate만 생성
- ACTIVE registry를 자동 변경하지 않음

Permission/trigger 확대가 있으면 Human Gate를 요구합니다.

---

## 14. Evolver

Evolver는 ACTIVE Skill의 반복 실패/수정 Evidence를 바탕으로 다음 버전 Candidate를 만듭니다.

```text
ACTIVE vN
→ Evidence
→ Proposal
→ Candidate vN+1
→ Audit
→ Protected Regression
→ Promotion
```

보호 계약:

- ACTIVE vN은 Candidate 작성 중 immutable
- base hash 검사
- bounded edit
- routing fixture 필요
- permission/trigger expansion Human Gate
- one-writer lock
- atomic promotion
- promotion history

---

## 15. Curator

Curator는 Library가 커질 때의 운영 비용을 감시합니다.

검토 대상:

- Skill size
- support file 수
- usage/success/failure metadata
- routing false positive/negative
- trigger overlap
- body signature
- protection flag

정상 작업마다 전체 Skill 본문을 읽지 않고 metadata/report를 우선합니다.

중요한 정책:

- low usage/time alone으로 archive하지 않음
- split/merge/archive는 Human Gate
- V8.2에서 자동 delete 없음
- `compress` / `extract-reference`만 제한된 low-risk package promotion 대상

---

## 16. Candidate Audit / Protected Regression

새 Skill 또는 수정된 Skill은 ACTIVE에 들어가기 전에 검사합니다.

Audit 예:

- required files
- frontmatter
- source/license/provenance
- relative link
- executable permission
- routing fixture
- base hash
- Human Gate contract

Protected Regression은 기존 핵심 routing behavior를 유지하는지 확인합니다.

Repository Source of Truth:

```text
evaluation/self-managing/protected-routing.json
```

Global install fallback:

```text
capability-library/governance/protected-routing.json
```

---

## 17. Promotion / Human Gate

자동으로 ACTIVE를 바꾸지 않는 대표 작업:

```text
create registry insertion
split
merge
archive
trigger expansion
permission expansion
structural registry change
```

Human Gate approval 자체도 silent mutation 권한이 아닙니다. V8.2에서 일부 구조 변경은 승인 후에도 `MANUAL_ONLY`입니다.

---

## 18. Maintenance CLI

Repository source:

```cmd
python harness\skills\manage.py audit
python harness\skills\manage.py gaps
python harness\skills\manage.py proposals
python harness\skills\manage.py curate
python harness\skills\manage.py benchmark --repeats 20
```

설치형:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" audit
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" gaps
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" proposals
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" curate
```

Semantic Candidate spec 작성은 reviewed input을 전제로 하며, Control Plane 자체는 특정 LLM provider를 요구하지 않습니다.

---

## 19. Repository Source of Truth

프로젝트별 사실과 계약은 각 Repository가 소유합니다.

예:

```text
PROJECT.md
REQUIREMENTS.md
ARCHITECTURE.md
DECISIONS.md
STATUS.md
tasks/TASK-001.md
```

Global Playbook이나 Skill이 Repository의 승인된 Architecture/Task Contract를 임의로 덮어쓰지 않습니다.

---

## 20. Verification Profile

```text
MINIMAL
작고 격리된 저위험 변경

STANDARD
일반적인 비단순 개발

STRICT
보안/권한/배포/마이그레이션/중요 Architecture/Public Contract 변경
```

Capability가 recommended profile을 제안할 수 있지만 검증 강도를 임의로 낮출 수는 없습니다.

---

## 21. Deterministic Quality Gate

```cmd
python "%USERPROFILE%\.codex\playbook-harness\quality\quality_gate.py" --repo . --profile strict --verify "python -m pytest"
```

검사 예:

- unstaged/staged whitespace 문제
- unresolved Git conflict
- conflict marker
- suspicious secret pattern
- 실제 Repository verification command 결과

결과:

```text
0 PASS
1 FAIL
2 UNVERIFIED
```

실행 Evidence가 필요한 STRICT 작업에서 검증 명령이 없으면 거짓 PASS가 아니라 `UNVERIFIED`입니다.

---

## 22. Audit

### Skill Audit

```cmd
python harness\quality\skill_audit.py --root .
```

Registry/lifecycle/provenance/Skill hygiene/routing signal을 검사합니다.

### Harness Audit

```cmd
python harness\security\harness_audit.py --root .
```

검사 예:

- 전역 `AGENTS.md` Context budget
- Core Skill metadata
- Profile JSON
- Capability sources / registry
- Optional Skill integrity
- Python syntax
- MANIFEST
- backup discovery path 오염 여부

---

## 23. Cleanup

Codex session이 끝나면 Launcher가 관리한 bridge/runtime을 정리합니다.

실제 Windows 검증에서:

```text
Target repo capability-library copy 없음
.playbook-runtime/launch-* residue 없음
```

을 확인했습니다.

Self-Managing state는 target repo가 아니라 global catalog state에 저장됩니다.

---

## 24. 왜 모든 것을 항상 켜지 않는가

V8.2는 기능이 많다는 이유만으로 무거운 계층을 항상 활성화하지 않습니다.

```text
Metadata
→ Skill
→ Wrapper
→ 필요한 경우에만 semantic maintenance
```

정상 task마다 Creator/Evolver/Curator나 상시 Multi-Agent를 기본 실행하지 않습니다.

핵심은:

```text
성장은 AI가 하고
비대화 감시는 deterministic code가 한다
```

입니다.

---

## 최종 원칙

```text
많은 Capability를 보유할 수 있다.
하지만 현재 Task에는 필요한 최소 Capability만 노출한다.

Self-Managing Layer를 가질 수 있다.
하지만 정상 Task path에 상시 LLM 비용을 추가하지 않는다.

토큰을 줄인다.
하지만 정확성과 검증 신뢰성을 낮추지는 않는다.
```
