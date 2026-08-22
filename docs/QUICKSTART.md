# 빠른 시작 - V8.1

이 문서는 Codex AI Agent Playbook을 설치하고, 임의의 Git Repository에서 필요한 optional Skill을 자동 선택해 Codex를 실행하는 가장 짧은 흐름을 설명합니다.

V8.1이 `main`에 merge되기 전에는 `v8.1-capability-library` 후보 브랜치에서 검증합니다.

## 1. 준비물

- Git
- Codex CLI
- Python 3
- Windows PowerShell 또는 POSIX shell

버전 확인:

```cmd
git --version
codex --version
python --version
```

## 2. Clone / Update

```cmd
git clone https://github.com/tmdgns104/codex-ai-agent-playbook.git
cd codex-ai-agent-playbook
git switch v8.1-capability-library
```

이미 clone했다면:

```cmd
git switch v8.1-capability-library
git pull origin v8.1-capability-library
```

## 3. Windows 설치

CMD:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

설치 스크립트는 다음을 관리합니다.

1. `%USERPROFILE%\.codex\AGENTS.md`의 Playbook marker 구간
2. `%USERPROFILE%\.agents\skills\`의 7개 Core managed Skill
3. `%USERPROFILE%\.codex\playbook-harness\`
4. `%USERPROFILE%\.codex\capability-library\`
5. 필요 시 `%USERPROFILE%\.codex\playbook-backups\<timestamp>\` 백업

`capability-library\skills\optional\`의 Skill은 `%USERPROFILE%\.agents\skills`에 영구 설치하지 않습니다. 현재 Task에서 Router가 선택한 Skill만 session-scoped bridge에 임시 노출됩니다.

변경이 없는 동일 버전 재설치는 `OK`로 끝나며 불필요한 백업/재복사를 만들지 않습니다.

## 4. 설치 검증

설치 후 자동 검증이 실행됩니다.

직접 다시 확인:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\verify-install.ps1"
```

V8.1 정상 예에는 다음 항목이 포함됩니다.

```text
PASS     global AGENTS.md playbook block
PASS     skill '...'
PASS     capability library
PASS     playbook harness
PASS     harness audit
RESULT   PASS
```

## 5. 자동 Skill 선택 Launcher

설치 후 실제 작업할 **아무 Git Repository**로 이동합니다.

예:

```cmd
cd D:\my-project
```

그 다음 작업 문장만 입력합니다.

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행"
```

사용자가 Skill 이름을 직접 지정하지 않습니다.

내부 흐름:

```text
Task
 -> deterministic Router
 -> 필요한 Skill 0~3개 자동 선택
 -> Risk / Permission Gate
 -> 선택 Skill만 session bridge에 임시 노출
 -> Codex 실행
 -> 같은 Task를 초기 Prompt로 1회 전달
 -> Codex 종료 후 runtime cleanup
```

대표 JWT/regression 요청은 현재 다음 Skill을 자동 선택합니다.

```text
security-review
testing
root-cause-debugging
```

`README 오타 한 줄 수정`처럼 작은 작업은 Skill 0개로 실행할 수 있습니다.

## 6. Codex를 실행하지 않고 먼저 확인

Plus 사용량을 쓰지 않고 Router/Bridge 결과만 확인하려면 `--dry-run`을 사용합니다.

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행" --dry-run
```

정상 예:

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

## 7. 권한 Gate

Skill 자동 선택은 권한 자동 승인과 다릅니다.

예를 들어:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "GitHub에 commit push하고 PR 생성" --dry-run
```

민감 external write가 선택되면 launcher는 자동 진행하지 않고:

```text
RESULT      HUMAN_GATE_REQUIRED
```

로 차단합니다.

Network Review / Manual Only도 같은 원칙으로 우회하지 않습니다.

## 8. 기존 Core Skill

전역으로 관리되는 Core Skill은 계속 사용할 수 있습니다.

```text
codex-skill-router
ai-agent-development-playbook
codex-long-run
codex-task-router
guide-ppt-creator
human-centered-project-builder
human-readable-code
```

V8.1의 optional Skill 자동 선택은 위 Core Skill을 전부 매 Task에 로드하는 방식이 아닙니다.

## 9. Quality Gate

일반적인 비단순 작업:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\quality\quality_gate.py" --repo . --profile standard
```

고위험 작업에서 실제 검증 명령까지 포함:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\quality\quality_gate.py" --repo . --profile strict --verify "python -m pytest"
```

결과:

```text
PASS       exit 0
FAIL       exit 1
UNVERIFIED exit 2
```

## 10. Playbook 자체 Audit

Playbook Repository에서:

```cmd
python harness\security\harness_audit.py --root .
```

정상 마지막 출력:

```text
INFO       warnings: 0
RESULT     PASS
```

## 11. 제거

Windows:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\uninstall.ps1"
```

Playbook marker 구간, managed Core Skills, installed capability library, playbook harness만 제거합니다.
사용자가 marker 밖에 직접 작성한 전역 AGENTS 내용은 보존합니다.

## 문제가 생기면

먼저:

```cmd
git status --short
powershell -NoProfile -ExecutionPolicy Bypass -File ".\verify-install.ps1"
```

을 확인합니다.
