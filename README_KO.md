# Codex AI Agent Playbook Kit - V8.1

Codex를 **적은 고정 Context**, **필요한 Capability만 선택하는 구조**, **실제 Evidence 기반 검증**으로 여러 프로젝트에서 일관되게 사용하기 위한 전역 Playbook + Skills + Harness입니다.

현재 안정 버전: **V8.1 (`main`)**  
Windows 실환경 검증 완료 / PR #5 Squash Merge 완료

> 처음 사용하는 경우에는 [빠른 시작 문서](docs/QUICKSTART.md)부터 보는 것을 권장합니다.

---

## 1. 이 프로젝트가 해결하려는 문제

Codex를 오래 사용하면서 기능과 지침을 계속 추가하면 다음 문제가 생길 수 있습니다.

- 모든 작업에서 큰 전역 Prompt를 반복해서 읽음
- Skill이 많아질수록 필요하지 않은 Context까지 노출됨
- 작은 수정에도 복잡한 절차가 적용됨
- Agent가 스스로 `PASS`라고 말한 것을 실제 검증으로 착각할 수 있음
- 긴 작업이 Chat history에 의존해 재시작/재개가 어려워짐
- 보안/권한 작업과 단순 오타 수정에 같은 검증 비용을 씀

V8.1은 **기능은 Library에 많이 보유할 수 있지만 현재 작업에는 필요한 것만 꺼내 쓰는 구조**를 목표로 합니다.

```text
Capability는 많이 보유
        ↓
항상 읽지는 않음
        ↓
Task마다 필요한 최소 Capability만 선택
```

---

## 2. V8.1 핵심 흐름

```text
사용자 작업
    ↓
Deterministic Metadata Router
    ↓
최소 Capability Plan
    ↓
Risk / Permission Gate
    ↓
필요한 optional Skill만 임시 활성화
    ↓
Codex 실행
    ↓
Repository Verification
    ↓
Quality Gate / Evidence
    ↓
Codex 종료 후 Runtime Cleanup
```

중요한 점은 **Skill 0개도 정상적인 결과**라는 것입니다.

예:

```text
README 오타 한 줄 수정
→ MINIMAL
→ optional Skill 0개

JWT 인증 오류 수정 + regression test
→ STRICT
→ security-review
→ testing
→ root-cause-debugging
```

사용자가 평소에 Skill 이름을 직접 고를 필요가 없습니다.

---

## 3. V8.1 설치 구조

Windows 설치 후:

```text
%USERPROFILE%\.codex\
├─ AGENTS.md
├─ capability-library\
├─ playbook-harness\
└─ playbook-backups\

%USERPROFILE%\.agents\skills\
├─ ai-agent-development-playbook\
├─ codex-long-run\
├─ codex-skill-router\
├─ codex-task-router\
├─ guide-ppt-creator\
├─ human-centered-project-builder\
└─ human-readable-code\
```

역할은 다음과 같습니다.

### `~/.codex/AGENTS.md`

항상 필요한 최소 전역 운영 원칙만 유지합니다.

V8.1 최종 Windows 검증 기준 Playbook 전역 영역은 **4579 bytes**였습니다.

### `~/.agents/skills/`

항상 사용할 수 있는 7개의 Core managed Skill입니다.

### `~/.codex/capability-library/`

작업별로 선택할 optional Capability의 원본 Library입니다.

현재 optional Skill:

```text
security-review
testing
root-cause-debugging
code-review
```

이 네 Skill을 모두 전역 Skill discovery 경로에 설치하지 않습니다.

### `~/.codex/playbook-harness/`

다음 결정론적 기능이 들어 있습니다.

```text
Router
Activation Manager
Skill Materializer
Codex Discovery Bridge
Auto Launcher
Quality Gate
Harness Audit
```

---

## 4. 설치 - Windows

### 준비물

```cmd
git --version
python --version
codex --version
```

세 명령이 정상적으로 버전을 출력하는지 확인합니다.

### 처음 설치

CMD:

```cmd
git clone https://github.com/tmdgns104/codex-ai-agent-playbook.git
cd codex-ai-agent-playbook
powershell -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

PowerShell:

```powershell
git clone https://github.com/tmdgns104/codex-ai-agent-playbook.git
cd codex-ai-agent-playbook
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

설치 스크립트는 기존 사용자 설정을 무조건 덮어쓰지 않습니다.

- 전역 `AGENTS.md`는 Playbook marker 구간만 관리
- Core Skill은 managed Skill만 관리
- 기존 managed 파일이 바뀌면 backup 생성
- Capability Library 설치
- Harness 설치
- 설치 직후 verification 자동 실행

정상 설치의 마지막 부분에는 다음이 포함됩니다.

```text
PASS     global AGENTS.md playbook block
PASS     skill '...'
PASS     capability library
PASS     playbook harness
PASS     harness audit
RESULT   PASS
```

---

## 5. 기존 설치 업데이트

Playbook Repository에서:

```cmd
git switch main
git pull origin main
powershell -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

같은 버전을 다시 설치하고 내용이 동일하면:

```text
OK       capability library
OK       playbook harness
```

처럼 나오며 새 backup이나 불필요한 재복사가 발생하지 않습니다.

설치 상태만 다시 확인하려면:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\verify-install.ps1"
```

---

## 6. 가장 쉬운 실제 사용법

설치가 끝났다면 Playbook Repository가 아니라 **실제로 수정할 프로젝트의 Git Repository**로 이동합니다.

예:

```cmd
cd /d D:\my-project
```

그 다음 작업 문장만 전달합니다.

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행"
```

사용자는 보통 다음을 직접 하지 않아도 됩니다.

- Skill 이름 선택
- Capability Library 경로 지정
- 임시 `.agents/skills` 구성
- Codex `-C` bridge 경로 계산
- session cleanup

Launcher가 이 과정을 자동으로 연결합니다.

---

## 7. 실제 Codex 실행 전에 결과만 확인하기

먼저 어떤 Skill이 선택되는지만 보고 싶다면 `--dry-run`을 사용합니다.

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행" --dry-run
```

실제 Windows 검증 결과:

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

작은 작업:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "README 오타 한 줄 수정" --dry-run
```

대표 결과:

```text
PROFILE     MINIMAL
SKILLS      none
COUNT       0
BRIDGE      false
```

즉 단순 작업에 억지로 Skill을 붙이지 않습니다.

---

## 8. 자동 Skill 선택은 자동 권한 승인이 아님

V8.1은 다음과 같은 민감 권한을 Router가 임의로 승인하지 않습니다.

```text
credential_access
external_write
database_write
destructive
production
network
browser_control
```

예:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "GitHub에 commit push하고 PR 생성" --dry-run
```

민감 external write가 필요한 경우:

```text
RESULT      HUMAN_GATE_REQUIRED
```

으로 자동 진행을 차단합니다.

Skill 자동 선택과 실제 권한 부여는 분리되어 있습니다.

---

## 9. Core Skill과 Optional Skill 차이

### Core Skill

전역으로 설치되고 여러 프로젝트에서 직접 사용할 수 있습니다.

| Skill | 역할 |
|---|---|
| `codex-skill-router` | 애매한 비단순 작업에서 최소 Skill/Profile 추천 |
| `ai-agent-development-playbook` | 복잡한 개발/Architecture/Agent/RAG/Tooling |
| `codex-long-run` | 여러 구현·디버깅·검증 cycle이 필요한 긴 작업 |
| `codex-task-router` | 모델/Reasoning/병렬 topology 판단이 필요한 작업 |
| `human-readable-code` | 가독성/유지보수성 중심 코드 |
| `human-centered-project-builder` | 요구→설계→구현→검증 프로젝트 workflow |
| `guide-ppt-creator` | 기술/프로젝트 가이드 PPT 제작 |

### Optional Skill

Capability Library 안에 보관하고 Router가 현재 Task에서 필요하다고 판단할 때만 session-scoped bridge로 노출합니다.

```text
security-review
testing
root-cause-debugging
code-review
```

V8.1의 핵심은 **Library에 있다는 이유만으로 Context에 넣지 않는 것**입니다.

---

## 10. 검증 Profile

### MINIMAL

작고 격리된 저위험 변경.

### STANDARD

일반적인 비단순 개발의 기본 검증 수준.

### STRICT

보안, 권한, 마이그레이션, 배포, 중요 Architecture/Public Contract, 파괴적 변경처럼 실패 비용이 큰 작업.

Skill 수와 검증 Profile은 같은 개념이 아닙니다.

---

## 11. Deterministic Quality Gate

일반적인 작업:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\quality\quality_gate.py" --repo . --profile standard
```

STRICT + 실제 검증 명령:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\quality\quality_gate.py" --repo . --profile strict --verify "python -m pytest"
```

주요 검사:

- unstaged/staged `git diff --check`
- unresolved Git conflict
- conflict marker
- suspicious secret pattern
- 변경 파일 상태
- 전달된 실제 Repository verification command

결과:

```text
0 = PASS
1 = FAIL
2 = UNVERIFIED
```

STRICT인데 필요한 실행 Evidence가 없으면 `PASS`라고 추측하지 않고 `UNVERIFIED`로 종료합니다.

Quality Gate는 Repository 자체 테스트와 Acceptance Criteria를 대체하지 않습니다.

---

## 12. Harness Audit

Playbook Repository 자체를 검증할 때:

```cmd
python harness\security\harness_audit.py --root .
```

V8.1에서는 다음도 확인합니다.

- 전역 `AGENTS.md` Context 예산
- managed Skill metadata
- Profile JSON
- Capability source / registry schema
- optional Skill integrity
- optional Skill이 Core discovery path에 잘못 노출됐는지
- Harness Python syntax
- MANIFEST drift

정상 마지막 출력:

```text
INFO       warnings: 0
RESULT     PASS
```

---

## 13. V8.1 실제 Windows 검증

2026-08-22 실제 Windows 환경에서 확인했습니다.

```text
CAP-001 ~ CAP-008              COMPLETE - VERIFIED
CAP-008 focused tests          2 PASS
CAP-005 regression             10 PASS
CAP-006 regression             10 PASS
CAP-007 regression             12 PASS
합계                            34 PASS

Capability Library install     PASS
Playbook Harness install       PASS
Harness Audit                  PASS / warnings 0
별도 Git Repository launcher   PASS
JWT 자동 Skill 선택            exact 3 PASS
Target repo catalog copy       없음
Runtime residue                없음
동일 버전 reinstall            idempotent PASS
STRICT Quality Gate            PASS
Exit code                      0
Working tree                   clean
```

최종 V8.1은 PR #5를 Squash Merge하여 `main`에 반영했습니다.

---

## 14. 제거

Windows:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\uninstall.ps1"
```

Linux/macOS:

```bash
./uninstall.sh
```

관리되는 다음 항목을 제거합니다.

```text
Playbook AGENTS marker block
Core managed Skills
~/.codex/capability-library
~/.codex/playbook-harness
```

사용자가 `AGENTS.md` marker 밖에 작성한 내용은 보존합니다.

백업은 자동으로 지우지 않습니다.

```text
%USERPROFILE%\.codex\playbook-backups\
```

---

## 15. 문제가 생겼을 때

Playbook Repository에서 먼저:

```cmd
git status --short
powershell -NoProfile -ExecutionPolicy Bypass -File ".\verify-install.ps1"
```

Playbook 자체 검사:

```cmd
python harness\security\harness_audit.py --root .
```

설치 상태가 꼬였다면 최신 `main`을 받은 뒤 `install.ps1`을 다시 실행합니다.

---

## 16. 관련 문서

- [빠른 시작](docs/QUICKSTART.md)
- [동작 원리](docs/HOW_IT_WORKS.md)
- [Skills 가이드](docs/SKILLS.md)
- [개발 가이드](docs/DEVELOPMENT.md)
- [V8.1 요구사항](V8_1_REQUIREMENTS.md)
- [V8.1 Architecture](V8_1_ARCHITECTURE.md)
- [V8.1 Capability Policy](V8_1_CAPABILITY_POLICY.md)
- [V8.1 Evaluation Plan](V8_1_EVALUATION_PLAN.md)
- [V8 변경사항](V8_CHANGES_KO.md)
- [V7 변경사항](V7_CHANGES_KO.md)

---

## 설계 원칙

- Chat 기록보다 Repository를 지속 가능한 Source of Truth로 사용
- 한 번에 하나의 coherent outcome에 집중
- 자기 보고 PASS가 아니라 Test/Diff/Artifact Evidence로 완료 판단
- 전역 Context는 짧게 유지
- 상세 Workflow는 Progressive Disclosure
- Capability Router는 body가 아니라 metadata부터 읽음
- Capability 0개도 허용
- optional Skill은 필요할 때만 session-scoped 활성화
- 고위험 권한은 Human/Network/Manual Gate 유지
- 상시 Multi-Agent와 무거운 Agent framework는 기본 Core에서 제외
- 토큰 절감이 정확성이나 검증 신뢰성을 낮추면 채택하지 않음
