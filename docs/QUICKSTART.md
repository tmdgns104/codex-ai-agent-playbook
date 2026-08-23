# 빠른 시작 - V8.2

이 문서는 Codex AI Agent Playbook V8.2를 **설치 → 검증 → 실제 Git Repository에서 자동 Skill 선택으로 실행**하는 가장 짧은 방법만 설명합니다.

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

설치되는 주요 구성:

```text
%USERPROFILE%\.codex\AGENTS.md
%USERPROFILE%\.agents\skills\<7개 Core managed Skill>
%USERPROFILE%\.codex\capability-library\<10 Optional Skills + 2 wrappers + governance>
%USERPROFILE%\.codex\playbook-harness\<Router / Activation / Quality / Lifecycle>
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
PASS     capability library
PASS     playbook harness
PASS     harness audit
RESULT   PASS
```

직접 다시 확인:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\verify-install.ps1"
```

---

## 4. 실제 프로젝트에서 사용

Playbook 폴더가 아니라 **Codex로 작업할 Git Repository**로 이동합니다.

```cmd
cd /d D:\my-project
git status
```

그 다음 작업 문장만 입력합니다.

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행"
```

V8.2가 자동으로:

```text
Task 분석
→ 필요한 Optional Skill 0~3개 선택
→ MINIMAL / STANDARD / STRICT 판단
→ Risk / Permission Gate
→ 선택 Skill만 임시 활성화
→ Codex 실행
→ privacy-safe Event 기록
→ cleanup
```

을 수행합니다.

Creator/Evolver/Curator는 일반 task마다 실행되지 않습니다.

---

## 5. Codex 실행 전에 Skill 선택만 확인

처음에는 `--dry-run`으로 확인하는 것을 권장합니다.

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
EVENT       EVENT_SKIPPED
RESULT      DRY_RUN_COMPLETE
```

`--dry-run`에서는 실제 task를 실행하지 않으므로 lifecycle Event도 기록하지 않습니다.

---

## 6. 작은 작업은 Skill이 없어도 정상

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

목표는 Skill을 많이 쓰는 것이 아니라 **필요한 Skill만 쓰는 것**입니다.

---

## 7. 현재 Skill 구성

```text
Core Skills        7
Optional Skills   10
Wrappers           2
Registry total    12 capabilities
```

Optional Skills:

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

전체 설명은 [Skills 가이드](SKILLS.md)를 참고합니다.

---

## 8. 민감한 권한 작업

자동 Skill 선택은 권한 자동 승인이 아닙니다.

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "GitHub에 commit push하고 PR 생성" --dry-run
```

민감한 external write가 필요하면:

```text
RESULT      HUMAN_GATE_REQUIRED
```

처럼 자동 진행을 차단합니다.

---

## 9. Quality Gate

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

---

## 10. Self-Managing Skill 상태 확인

설치형 Control Plane audit:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" audit
```

Gap 확인:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" gaps
```

Proposal 확인:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" proposals
```

Library scaling benchmark:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" benchmark --repeats 20
```

Self-Managing maintenance는 LLM provider 없이도 Control Plane 기능을 사용할 수 있습니다.

---

## 11. 업데이트

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

## 12. 제거

Windows:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\uninstall.ps1"
```

Linux/macOS:

```bash
./uninstall.sh
```

Playbook이 관리하는 marker 구간, Core managed Skills, Capability Library, Harness만 제거합니다. 사용자가 `AGENTS.md` marker 밖에 직접 작성한 내용은 보존합니다.

---

## 13. 문제가 생기면

Playbook Repository에서:

```cmd
git status --short
powershell -NoProfile -ExecutionPolicy Bypass -File ".\verify-install.ps1"
python harness\security\harness_audit.py --root .
```

설치형 Self-Managing 상태:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\skills\manage.py" audit
```

더 자세한 설명은 [README_KO.md](../README_KO.md)를 참고합니다.
