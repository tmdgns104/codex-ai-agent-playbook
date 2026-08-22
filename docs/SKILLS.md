# Skills 가이드 - V8.1

V8.1의 Skill은 **Core Skill**과 **Optional Skill** 두 종류로 나뉩니다.

핵심 원칙:

```text
Skill을 많이 가지고 있는 것 ≠ 매 작업에서 모두 읽는 것
```

현재 작업에 필요한 최소 Skill만 사용합니다.

---

## 1. Core Skill

설치 시 `%USERPROFILE%\.agents\skills\`에 관리되는 7개 Skill입니다.

| 상황 | Core Skill |
|---|---|
| 어떤 Skill이 필요한지 애매한 비단순 작업 | `codex-skill-router` |
| 복잡한 기능/Architecture/Agent/RAG/Tool 설계 | `ai-agent-development-playbook` |
| 여러 구현·디버깅·검증 cycle이 필요한 긴 작업 | `codex-long-run` |
| 모델/Reasoning/병렬 실행 판단이 실제로 필요한 작업 | `codex-task-router` |
| 코드 가독성/학습/유지보수성이 중요 | `human-readable-code` |
| 새 프로젝트를 요구부터 체계적으로 시작 | `human-centered-project-builder` |
| 기술/교육/프로젝트 가이드 PPT 제작 | `guide-ppt-creator` |

Core Skill도 항상 전부 사용할 필요는 없습니다.

---

## 2. Optional Skill

Optional Skill은 다음 위치의 Capability Library에 보관합니다.

```text
%USERPROFILE%\.codex\capability-library\skills\optional\
```

현재 V8.1 Library:

| Optional Skill | 대표 용도 |
|---|---|
| `security-review` | 인증, 권한, secret, 외부 입력 등 보안 검토 |
| `testing` | regression, 재현 테스트, 검증 계획 |
| `root-cause-debugging` | 원인 불명 오류의 체계적 원인 추적 |
| `code-review` | 변경 코드의 품질/위험 검토 |

이 Skill들은 `%USERPROFILE%\.agents\skills`에 전부 영구 노출하지 않습니다.

작업이 시작되면 Router가 metadata를 보고 필요한 것만 선택하고, session-scoped bridge로 Codex에 임시 노출합니다.

---

## 3. 자동 선택 예시

### 아주 작은 수정

```text
README 오타 한 줄 수정
```

대표 결과:

```text
PROFILE MINIMAL
SKILLS none
COUNT 0
```

Skill 0개도 정상입니다.

### 보안 + 테스트 + 디버깅

```text
JWT 인증 오류를 수정하고 regression test를 실행
```

실제 Windows 검증 결과:

```text
PROFILE STRICT
SKILLS security-review,testing,root-cause-debugging
COUNT 3
```

### 민감 external write

```text
GitHub에 commit push하고 PR 생성
```

권한 Gate가 필요한 경우:

```text
RESULT HUMAN_GATE_REQUIRED
```

Skill 자동 선택은 권한 자동 승인이 아닙니다.

---

## 4. 자동 Launcher 사용

실제 작업할 Git Repository에서:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행"
```

Skill 선택만 보고 싶다면:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행" --dry-run
```

일반 사용에서는 Optional Skill 이름을 직접 지정하지 않아도 됩니다.

---

# Core Skill 상세

## codex-skill-router

Skill 선택이 애매한 비단순 작업에서 **최소 Core Skill 집합과 검증 Profile**을 추천합니다.

추천 대상:

- 필요한 최소 Skill
- `MINIMAL / STANDARD / STRICT`
- long-run 필요 여부
- capability router 필요 여부
- Human Gate 필요 여부

단순 작업에는 호출하지 않아도 됩니다.

---

## ai-agent-development-playbook

복잡한 소프트웨어 작업을 Repository의 승인된 요구사항과 Architecture 안에서 진행하도록 돕습니다.

주요 역할:

- Requirements / Architecture 확인
- Task Contract 기반 구현
- Agent / RAG / Tool runtime 설계
- State / Tool / Resource 계약
- Human Gate
- Evidence 기반 완료 판단

---

## codex-long-run

긴 Repository 작업을 여러 cycle/session에 걸쳐 안정적으로 이어가기 위한 Skill입니다.

주요 역할:

- minimum sufficient context
- stale state guard
- one coherent outcome
- focused verification budget
- meaningful checkpoint
- repository-based resume

작은 수정에는 사용하지 않습니다.

---

## codex-task-router

하나의 충분히 정의된 작업에서 필요한 Codex capability 수준을 판단합니다.

판단 기준 예:

- Complexity
- Uncertainty
- Risk
- Architecture Impact
- Verification Difficulty
- Parallelizability
- Cost Sensitivity

실제 모델 이름을 영구 hardcode하지 않습니다.

---

## human-readable-code

사람이 읽고 배우고 유지보수하기 쉬운 코드를 만드는 데 집중합니다.

우선순위:

```text
Correctness
→ Understandability
→ Testability
→ Maintainability
→ Performance
→ Cleverness
```

---

## human-centered-project-builder

새 프로젝트나 비단순 프로젝트를 다음 흐름으로 진행할 때 사용합니다.

```text
Problem
→ Requirements
→ Architecture
→ Task
→ Implementation
→ Verification
→ Explanation
```

---

## guide-ppt-creator

기술 문서나 프로젝트를 사람이 이해할 수 있는 가이드 PPT로 만드는 Workflow입니다.

```text
Source Analysis
→ Audience / Goal
→ Storyboard
→ Slide Contract
→ Build
→ Render / Inspect
→ Visual QA
→ Content QA
```

---

## Skill Router와 Capability Router 차이

둘은 비슷해 보이지만 역할이 다릅니다.

```text
codex-skill-router
→ Core Skill / Verification Profile 선택 지원

V8.1 Capability Router
→ capability-library metadata를 보고 optional Capability 자동 선택
```

평소 V8.1 Launcher를 사용하면 Optional Skill은 Capability Router가 자동으로 처리합니다.

---

## 검증 Profile과 Skill 수는 별개

```text
MINIMAL
→ 작고 격리된 저위험 변경

STANDARD
→ 일반 비단순 개발

STRICT
→ 보안/권한/배포/마이그레이션/중요 Architecture 등 고위험 변경
```

Skill을 많이 선택했다고 STRICT가 되는 것도 아니고, 강한 모델을 사용했다고 STRICT 검증을 생략할 수도 없습니다.

---

## 최종 원칙

```text
현재 Task에 직접 필요한 최소 Skill만 사용
```

Repository의 승인된 Requirements, Architecture, Task Contract가 Skill보다 우선합니다.

V8.1의 목표는 Skill 수를 늘리는 것이 아니라 **Capability Library가 커져도 현재 Task의 Context는 작게 유지하는 것**입니다.
