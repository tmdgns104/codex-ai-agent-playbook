# Quick Start

이 문서는 Codex AI Agent Playbook Kit v6를 처음 설치하고 확인하는 가장 짧은 경로입니다.

## 1. 준비물

- Git
- Codex CLI
- Windows PowerShell 또는 POSIX shell

버전 확인 예:

```powershell
git --version
codex --version
```

## 2. Clone

```powershell
git clone https://github.com/tmdgns104/codex-ai-agent-playbook.git
cd codex-ai-agent-playbook
```

v6가 아직 `main`에 병합되기 전이라면:

```powershell
git switch v6-candidate
```

## 3. Windows 설치

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

설치 스크립트는:

1. `$HOME\.codex\AGENTS.md`의 Kit marker 구간을 추가/갱신하고,
2. `.agents\skills`의 각 Skill을 `$HOME\.agents\skills`에 설치하며,
3. 기존 동일 Skill이 있으면 timestamp 백업을 만든 뒤 교체합니다.

## 4. 설치된 위치 확인

```powershell
Get-Content $HOME\.codex\AGENTS.md
Get-ChildItem $HOME\.agents\skills
```

v6 기준 핵심 Skill은 다음 6개입니다.

```text
ai-agent-development-playbook
human-readable-code
human-centered-project-builder
guide-ppt-creator
codex-long-run
codex-task-router
```

## 5. Codex에서 확인

새 터미널을 열고 프로젝트 Repository로 이동한 뒤:

```powershell
codex
```

첫 확인 예:

```text
$ai-agent-development-playbook

이 Skill이 담당하는 역할을 설명해.
현재 Repository는 수정하지 마.
```

가독성 Skill 확인:

```text
$human-readable-code

이 Skill의 핵심 원칙을 5개로 요약해.
코드는 수정하지 마.
```

## 6. 새 프로젝트 시작

가장 간단한 통합 시작은:

```text
$human-centered-project-builder

이 Repository를 새 프로젝트로 시작하려고 해.
바로 구현하지 말고 Problem → Requirements → Architecture → Task 순서로 진행해.
```

중요한 Architecture가 정해지면 Repository 문서에 기록하고, 구현은 Task 단위로 진행하는 것을 권장합니다.

## 7. 기존 프로젝트에서 사용

이미 `PROJECT.md`, `REQUIREMENTS.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `STATUS.md`, `tasks/`가 있다면:

```text
$ai-agent-development-playbook
$human-readable-code

Repository 문서와 현재 Task를 읽어.
승인된 범위만 구현하고 완료 전 Verification과 Acceptance Criteria를 실제로 확인해.
```

## 8. 긴 작업

여러 구현/디버깅/검증 사이클이 필요한 Repository 작업에는:

```text
$codex-long-run

현재 Repository와 작업 상태를 읽고
하나의 coherent outcome을 끝까지 이어가.
```

이 Skill은 Architecture를 새로 정하는 역할이 아니라, 이미 승인된 범위 안에서 긴 실행을 Context 효율적으로 이어가기 위한 orchestration 역할입니다.

## 9. 모델/Reasoning 선택이 중요한 경우

작업 자체가 충분히 정의되어 있고 capability 선택을 검토하고 싶다면:

```text
$codex-task-router

현재 Task에 필요한 최소 충분한 Codex capability를 추천해.
구현은 하지 마.
```

Router는 작업을 구현하지 않고 추천만 합니다.

## 10. 제거

Windows:

```powershell
.\uninstall.ps1
```

Kit marker 구간과 설치 Skill을 제거합니다.

## 설치 후 문제가 생기면

먼저 다음을 확인합니다.

```powershell
git status
Get-Content $HOME\.codex\AGENTS.md
Get-ChildItem $HOME\.agents\skills
```

기존 사용자 전역 규칙이 있다면 marker 밖 내용은 보존되어야 합니다.
