# 빠른 시작 - V8.1

이 문서는 Codex AI Agent Playbook V8.1을 **설치 → 검증 → 실제 Git Repository에서 자동 Skill 선택으로 실행**하는 가장 짧은 방법만 설명합니다.

현재 안정 버전은 `main`입니다.

---

## 1. 준비물

필요한 프로그램:

- Git
- Python 3
- Codex CLI
- Windows PowerShell 또는 POSIX shell

Windows CMD에서 확인:

```cmd
git --version
python --version
codex --version
```

세 명령이 모두 버전을 출력하면 준비 완료입니다.

---

## 2. 처음 설치 - Windows

```cmd
git clone https://github.com/tmdgns104/codex-ai-agent-playbook.git
cd codex-ai-agent-playbook
powershell -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

설치 스크립트가 다음을 관리합니다.

```text
%USERPROFILE%\.codex\AGENTS.md
%USERPROFILE%\.agents\skills\<7개 Core managed Skill>
%USERPROFILE%\.codex\capability-library\
%USERPROFILE%\.codex\playbook-harness\
```

기존 managed 내용이 바뀌는 경우에는:

```text
%USERPROFILE%\.codex\playbook-backups\<timestamp>\
```

아래에 백업합니다.

Optional Skill은 `%USERPROFILE%\.agents\skills`에 전부 영구 설치하지 않습니다.

---

## 3. 설치가 잘 됐는지 확인

`install.ps1`이 끝나면 자동 검증이 실행됩니다.

정상 예:

```text
PASS     global AGENTS.md playbook block
PASS     skill '...'
PASS     capability library
PASS     playbook harness
PASS     harness audit
RESULT   PASS
```

직접 다시 확인하고 싶다면:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\verify-install.ps1"
```

---

## 4. 실제 프로젝트에서 사용

이제 Playbook 폴더를 떠나서 **Codex로 작업할 Git Repository**로 이동합니다.

예:

```cmd
cd /d D:\my-project
```

현재 폴더가 Git Repository인지 확인:

```cmd
git status
```

그 다음 작업 문장만 입력합니다.

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행"
```

사용자가 Skill 이름을 직접 지정할 필요가 없습니다.

V8.1이 자동으로:

```text
Task 분석
→ 필요한 optional Skill 0~3개 선택
→ MINIMAL / STANDARD / STRICT 판단
→ Risk / Permission Gate
→ 선택된 Skill만 임시 활성화
→ Codex 실행
→ Codex 종료 후 cleanup
```

을 수행합니다.

---

## 5. 실제 Codex 실행 전에 Skill 선택만 확인

처음에는 `--dry-run`으로 확인하는 것을 권장합니다.

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

이 상태에서는 실제 Codex 작업을 시작하지 않습니다.

---

## 6. 작은 작업은 Skill이 없어도 정상

예:

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

V8.1의 목표는 Skill을 많이 쓰는 것이 아니라 **필요한 Skill만 쓰는 것**입니다.

---

## 7. 민감한 권한 작업

자동 Skill 선택은 권한 자동 승인이 아닙니다.

예:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "GitHub에 commit push하고 PR 생성" --dry-run
```

민감한 external write가 필요하면:

```text
RESULT      HUMAN_GATE_REQUIRED
```

처럼 자동 진행을 차단합니다.

---

## 8. Quality Gate

일반적인 비단순 작업:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\quality\quality_gate.py" --repo . --profile standard
```

STRICT 검증 + 실제 테스트 명령:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\quality\quality_gate.py" --repo . --profile strict --verify "python -m pytest"
```

결과:

```text
0 = PASS
1 = FAIL
2 = UNVERIFIED
```

STRICT인데 필요한 실제 검증이 없으면 `UNVERIFIED`가 정상입니다.

---

## 9. 업데이트

이미 설치되어 있다면 Playbook Repository에서:

```cmd
git switch main
git pull origin main
powershell -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

변경이 없는 동일 버전이면:

```text
OK       capability library
OK       playbook harness
```

처럼 끝납니다.

---

## 10. 제거

Windows:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\uninstall.ps1"
```

Linux/macOS:

```bash
./uninstall.sh
```

Playbook이 관리하는 marker 구간, Core managed Skills, Capability Library, Harness만 제거합니다.

사용자가 `AGENTS.md` marker 밖에 직접 작성한 내용은 보존합니다.

---

## 11. 문제가 생기면

Playbook Repository에서:

```cmd
git status --short
powershell -NoProfile -ExecutionPolicy Bypass -File ".\verify-install.ps1"
python harness\security\harness_audit.py --root .
```

먼저 이 세 결과를 확인하면 설치 drift와 Playbook 자체 문제를 구분하기 쉽습니다.

더 자세한 설명은 [README_KO.md](../README_KO.md)를 참고합니다.
