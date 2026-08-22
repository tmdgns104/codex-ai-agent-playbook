# Codex AI Agent Playbook

> **현재 안정 버전: V8.1 (`main`)**  
> 적은 고정 Context + 필요한 Skill만 자동 선택 + 실제 Evidence 기반 검증

Codex를 여러 프로젝트에서 사용할 때 **매번 거대한 지침을 읽게 하지 않고**, 현재 작업에 필요한 기능만 골라서 사용하도록 만든 경량 Playbook + Skills + Harness입니다.

Windows 실제 환경에서 설치, 자동 Skill 선택, 별도 Git Repository 실행, cleanup, 재설치 멱등성, STRICT Quality Gate까지 검증했습니다.

[상세 한글 가이드](README_KO.md) · [빠른 시작](docs/QUICKSTART.md) · [동작 원리](docs/HOW_IT_WORKS.md) · [Skills 가이드](docs/SKILLS.md)

---

## 30초 요약

기존 방식은 Skill과 규칙이 많아질수록 매 작업의 Context가 커질 수 있습니다.

V8.1은 다음처럼 동작합니다.

```text
사용자 작업
   ↓
가벼운 Metadata Router
   ↓
필요한 optional Skill만 자동 선택 (0~3개)
   ↓
Risk / Permission Gate
   ↓
선택된 Skill만 현재 작업에 임시 활성화
   ↓
Codex 실행
   ↓
Repository Verification / Quality Gate
   ↓
작업 종료 후 임시 Skill cleanup
```

작은 작업은 **Skill 0개**도 정상입니다.

예를 들어:

```text
README 오타 한 줄 수정
→ Skill 0개 / MINIMAL

JWT 인증 오류 수정 + regression test
→ security-review
→ testing
→ root-cause-debugging
→ STRICT
```

사용자가 Skill 이름을 직접 고를 필요가 없습니다.

---

## 설치 - Windows CMD

필요한 것:

- Git
- Python 3
- Codex CLI
- Windows PowerShell

버전 확인:

```cmd
git --version
python --version
codex --version
```

처음 설치:

```cmd
git clone https://github.com/tmdgns104/codex-ai-agent-playbook.git
cd codex-ai-agent-playbook
powershell -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

설치가 끝나면 검증도 자동 실행됩니다.

정상 예:

```text
PASS     global AGENTS.md playbook block
PASS     skill '...'
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

그리고 작업 문장만 전달합니다.

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행"
```

V8.1이 내부에서:

1. 작업을 분류하고
2. 필요한 optional Skill만 선택하고
3. 위험도에 맞는 Profile을 정하고
4. 선택된 Skill만 임시로 Codex에 보이게 만들고
5. 같은 작업 문장을 Codex에 전달하고
6. Codex 종료 후 임시 runtime을 정리합니다.

### Codex를 실행하지 않고 선택 결과만 보기

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "JWT 인증 오류를 수정하고 regression test를 실행" --dry-run
```

정상 예:

```text
PROFILE     STRICT
SKILLS      security-review,testing,root-cause-debugging
COUNT       3
BRIDGE      true
RESULT      READY
CLEANUP     BRIDGE_CLEANED
RESULT      DRY_RUN_COMPLETE
```

`--dry-run`은 실제 Codex를 실행하지 않고 Router / Gate / Bridge 결과만 확인할 때 유용합니다.

---

## 권한이 필요한 작업은 자동으로 밀어붙이지 않음

Skill 자동 선택과 권한 자동 승인은 다른 개념입니다.

예:

```cmd
python "%USERPROFILE%\.codex\playbook-harness\activation\playbook_launch.py" --root . --task "GitHub에 commit push하고 PR 생성" --dry-run
```

민감한 external write가 필요하면:

```text
RESULT      HUMAN_GATE_REQUIRED
```

처럼 멈춥니다.

Network Review / Manual Only / Human Gate를 Router가 우회하지 않습니다.

---

## V8.1 구조

설치 후 주요 위치:

```text
%USERPROFILE%\.codex\AGENTS.md
    항상 필요한 짧은 전역 원칙

%USERPROFILE%\.agents\skills\
    7개 Core managed Skill

%USERPROFILE%\.codex\capability-library\
    optional Capability 원본 Library

%USERPROFILE%\.codex\playbook-harness\
    Router / Activation / Quality / Audit 실행 코드
```

Optional Skill은 `%USERPROFILE%\.agents\skills`에 전부 영구 설치하지 않습니다.

현재 Library의 optional Skill:

```text
security-review
testing
root-cause-debugging
code-review
```

필요한 작업에서만 임시 활성화됩니다.

---

## Core Skills

전역으로 관리되는 Core Skill은 7개입니다.

| Skill | 용도 |
|---|---|
| `codex-skill-router` | 애매한 비단순 작업에서 최소 Skill / Profile 추천 |
| `ai-agent-development-playbook` | 복잡한 개발, Architecture, Agent/RAG/Tooling |
| `codex-long-run` | 긴 구현/디버깅/검증 작업 |
| `codex-task-router` | 모델/Reasoning/병렬 실행 판단이 필요한 작업 |
| `human-readable-code` | 읽기 쉽고 유지보수하기 쉬운 코드 |
| `human-centered-project-builder` | 요구→설계→구현→검증 프로젝트 흐름 |
| `guide-ppt-creator` | 기술/프로젝트 가이드 PPT 제작 |

Core Skill도 매번 전부 쓰는 것이 아니라 필요한 것만 사용합니다.

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

### Quality Gate

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

이미 설치했다면:

```cmd
cd /d <codex-ai-agent-playbook 경로>
git switch main
git pull origin main
powershell -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

변경이 없는 동일 버전 재설치는:

```text
OK       capability library
OK       playbook harness
```

처럼 끝나며 불필요한 백업/재복사를 만들지 않습니다.

직접 설치 상태만 확인하려면:

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

Playbook이 관리하는 marker 구간, Core Skills, Capability Library, Harness만 제거합니다.

사용자가 전역 `AGENTS.md`의 marker 밖에 직접 작성한 내용은 보존하도록 설계되어 있습니다.

백업 위치:

```text
%USERPROFILE%\.codex\playbook-backups\<timestamp>\
```

---

## 실제 Windows 검증 결과

2026-08-22 V8.1 최종본에서 확인:

```text
CAP-001 ~ CAP-008            COMPLETE - VERIFIED
Focused / regression tests   34 PASS
Capability Library install   PASS
Playbook Harness install     PASS
Harness Audit                PASS / warnings 0
Detached Git repo launcher   PASS
JWT task Skill auto-select   exact 3 PASS
Runtime cleanup              PASS
Reinstall idempotency        PASS
STRICT Quality Gate          PASS / exit 0
Final working tree           clean
```

V8.1은 PR #5 검증 후 `main`에 Squash Merge되었습니다.

---

## 설계 원칙

```text
적은 영구 Context
+ 필요한 Capability만 선택
+ Metadata-first Routing
+ 위험도에 맞는 검증
+ Repository Source of Truth
+ 실제 Test / Diff / Artifact Evidence
- 모든 Skill 상시 로드
- 상시 Multi-Agent
- 자기보고 PASS
```

토큰을 줄이기 위해 정확성이나 검증 신뢰성을 희생하는 방식은 사용하지 않습니다.
