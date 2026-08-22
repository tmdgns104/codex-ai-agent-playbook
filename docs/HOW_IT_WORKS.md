# 동작 원리 - V8.1

Codex AI Agent Playbook V8.1은 하나의 거대한 Prompt가 아니라 **항상 필요한 작은 전역 규칙**과 **필요할 때만 활성화되는 Capability**를 분리합니다.

핵심 목표는:

```text
Context 비용은 줄이고
검증 신뢰성은 유지하거나 높이는 것
```

입니다.

---

## 전체 흐름

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
Evidence
   ↓
Managed Cleanup
```

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

```text
<!-- BEGIN AI_AGENT_PLAYBOOK_KIT -->
...
<!-- END AI_AGENT_PLAYBOOK_KIT -->
```

---

## 2. Core Skill과 Optional Capability를 분리

### Core Skill

`%USERPROFILE%\.agents\skills\`에 설치되는 7개 managed Skill입니다.

이들은 여러 Repository에서 공통으로 사용할 수 있는 운영/개발 Workflow입니다.

### Optional Capability

`%USERPROFILE%\.codex\capability-library\`에 보관합니다.

현재 optional Skill:

```text
security-review
testing
root-cause-debugging
code-review
```

중요한 점은 Library에 존재한다고 해서 Codex가 매 작업에서 모두 읽는 것이 아니라는 것입니다.

---

## 3. Deterministic Capability Router

V8.1 Router는 먼저 Capability 본문이 아니라 짧은 `registry.json` metadata를 읽습니다.

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

Router의 초기 판단에는 LLM API를 사용하지 않습니다.

작업 문장과 trigger/domain metadata를 비교해 필요한 Capability를 점수화합니다.

기본 원칙:

```text
Capability 0개 허용
전체 선택 기본 상한 3개
Skill 최대 3개
MCP 최대 1개
Agent 최대 1개
```

V8.1 현재 실제 자동 실행 경로는 optional Skill 중심이며 MCP/Agent를 자동 spawn하지 않습니다.

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

즉 필요한 것만 선택합니다.

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
```

이런 권한은 자동 진행을 막습니다.

즉:

```text
Skill 자동 선택
≠
권한 자동 승인
```

입니다.

---

## 6. Skill Materialization

Gate를 통과한 optional Skill만 현재 session runtime으로 복사합니다.

예:

```text
<target-repo>/.playbook-runtime/<session>/
```

여기서 중요한 안전 조건:

- target repo에 전체 capability-library를 복사하지 않음
- optional Skill을 전역 `.agents/skills`에 영구 설치하지 않음
- 선택되지 않은 Skill은 session에 노출하지 않음
- source path가 capability-library 밖으로 escape하지 못함

---

## 7. Codex Discovery Bridge

Codex는 Repository hierarchy의 `.agents/skills`를 탐색할 수 있습니다.

V8.1은 이를 이용해 task-scoped bridge를 만듭니다.

개념:

```text
Target Repository
├─ 기존 Repository 내용
└─ .playbook-runtime/
   └─ <session>/
      └─ cwd/
         └─ .agents/
            └─ skills/
               └─ <선택된 optional Skill만>
```

Launcher는 대략 다음 구조로 Codex를 실행합니다.

```text
codex -C <bridge-cwd> --add-dir <target-repo> -- "<task>"
```

이 방식으로:

- 기존 Repository Core context 유지
- 선택된 optional Skill만 추가 discovery
- target repo 전체 작업 권한 유지
- optional Skill 영구 설치 방지

를 동시에 만족합니다.

---

## 8. Installed Launcher

설치 후 사용자는 Capability Library 위치를 알 필요가 없습니다.

실제 작업할 Git Repository에서:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "<작업>"
```

Launcher는 자기 설치 위치를 기준으로 자동으로:

```text
%USERPROFILE%\.codex\capability-library
```

를 찾습니다.

따라서 Playbook source Repository와 실제 작업 Repository는 서로 달라도 됩니다.

이 분리 구조는 실제 Windows의 별도 Git Repository에서 검증했습니다.

---

## 9. Dry-run

실제 Codex를 실행하지 않고 Router / Gate / Bridge 결과만 확인할 수 있습니다.

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행" --dry-run
```

이 기능은 새로운 trigger나 Capability를 추가했을 때 선택 결과를 검증하는 데도 유용합니다.

---

## 10. Repository Source of Truth

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

## 11. Verification Profile

작업마다 같은 검증 비용을 사용하지 않습니다.

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

## 12. Deterministic Quality Gate

Quality Gate는 LLM의 자기 판단과 분리된 코드로 실행합니다.

예:

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

## 13. Harness Audit

Playbook 자체도 결정론적으로 검사합니다.

```cmd
python harness\security\harness_audit.py --root .
```

V8.1 검사에는 다음이 포함됩니다.

- 전역 `AGENTS.md` Context budget
- Core Skill metadata
- Profile JSON
- Capability sources
- Capability registry
- optional Skill integrity
- Python syntax
- MANIFEST
- Skill discovery path의 backup 오염 여부

---

## 14. Cleanup

Codex session이 끝나면 Launcher가 관리한 bridge/runtime을 정리합니다.

실제 V8.1 Windows 검증에서:

```text
Target repo capability-library copy 없음
.playbook-runtime/launch-* residue 없음
```

을 확인했습니다.

---

## 15. 왜 MCP/Agent를 항상 켜지 않는가

V8.1은 기능이 많다는 이유만으로 무거운 계층을 항상 활성화하지 않습니다.

우선순위:

```text
Skill
→ CLI/REST wrapper
→ MCP
→ Agent
```

MCP는 stateful structured interaction 가치가 분명할 때만 고려하고, Agent는 독립 검증/병렬성이 실제로 필요한 경우에만 고려합니다.

상시 Planner/Coder/Tester/Reviewer 멀티에이전트를 기본 구조로 사용하지 않습니다.

---

## 최종 원칙

```text
많은 Capability를 보유할 수 있다.
하지만 현재 Task에는 필요한 최소 Capability만 노출한다.

토큰을 줄인다.
하지만 정확성과 검증 신뢰성을 낮추지는 않는다.
```
