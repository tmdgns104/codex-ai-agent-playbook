# 빠른 시작 - V8

이 문서는 Codex AI Agent Playbook V8을 가장 짧게 설치하고 확인하는 방법입니다.

현재 안정 버전은 `main`입니다.

## 1. 준비물

- Git
- Codex CLI
- Python 3
- Windows PowerShell 또는 POSIX shell

버전 확인 예:

```cmd
git --version
codex --version
python --version
```

## 2. Clone

```cmd
git clone https://github.com/tmdgns104/codex-ai-agent-playbook.git
cd codex-ai-agent-playbook
```

별도 후보 브랜치로 이동할 필요 없이 `main`을 사용합니다.

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
2. `%USERPROFILE%\.agents\skills\`의 7개 managed Skill
3. `%USERPROFILE%\.codex\playbook-harness\`
4. 필요 시 `%USERPROFILE%\.codex\playbook-backups\<timestamp>\` 백업

변경이 없는 동일 버전 재설치는 `OK`로 끝나며 불필요한 백업/재복사를 만들지 않습니다.

## 4. 설치 검증

설치 후 자동 검증이 실행됩니다.

직접 다시 확인하려면:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\verify-install.ps1"
```

정상 예:

```text
PASS     global AGENTS.md playbook block
PASS     skill 'ai-agent-development-playbook'
PASS     skill 'codex-long-run'
PASS     skill 'codex-skill-router'
PASS     skill 'codex-task-router'
PASS     skill 'guide-ppt-creator'
PASS     skill 'human-centered-project-builder'
PASS     skill 'human-readable-code'
PASS     playbook harness
PASS     harness audit
RESULT   PASS
```

## 5. V8의 7개 Skill

```text
codex-skill-router
ai-agent-development-playbook
codex-long-run
codex-task-router
guide-ppt-creator
human-centered-project-builder
human-readable-code
```

모든 Skill을 같이 쓰지 않습니다.
현재 작업에 필요한 최소 Skill만 사용합니다.

## 6. Skill 선택이 애매할 때

```text
$codex-skill-router

현재 작업에 필요한 최소 Skill과 검증 Profile만 추천해.
구현은 하지 마.
```

작은 수정처럼 선택이 명확하면 Router를 사용하지 않아도 됩니다.

## 7. 비단순 개발

```text
$ai-agent-development-playbook

현재 Repository의 요구사항과 Architecture, 현재 Task를 먼저 확인해.
승인된 범위만 구현하고 실제 Verification Evidence로 완료 여부를 판단해.
```

## 8. 긴 작업

```text
$codex-long-run

현재 Repository 상태를 기준으로 하나의 coherent outcome만 끝까지 진행해.
불필요한 전체 스캔과 반복 로그를 줄이고 필요한 Evidence를 남겨.
```

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

STRICT에서 필요한 실행 Evidence 없이 구조 검사만 통과한 경우 거짓 PASS 대신 `UNVERIFIED`가 됩니다.

## 10. Harness Audit

Playbook Repository 자체 확인:

```cmd
python harness\security\harness_audit.py --root .
```

정상 마지막 출력:

```text
INFO       warnings: 0
RESULT     PASS
```

## 11. 기존 설치 업데이트

```cmd
git switch main
git pull origin main
powershell -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

## 12. 제거

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\uninstall.ps1"
```

Playbook marker 구간, managed Skills, playbook harness만 제거합니다.
사용자가 marker 밖에 직접 작성한 전역 AGENTS 내용은 보존하도록 설계되어 있으며 V8에서 실제 Windows 검증을 완료했습니다.

## 문제가 생기면

먼저 다음을 확인합니다.

```cmd
git status --short
powershell -NoProfile -ExecutionPolicy Bypass -File ".\verify-install.ps1"
```

그리고 [V8 변경사항 및 검증 기록](../V8_CHANGES_KO.md)을 확인합니다.
