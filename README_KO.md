# Codex AI Agent Playbook Kit

Codex를 **더 적은 반복 설명과 더 적은 고정 컨텍스트로**, 여러 프로젝트에서 일관되게 사용하기 위한 전역 Playbook + Skills 세트입니다.

현재 개발 버전: **V7 Candidate (`v7-context-efficient`)**

## 핵심 구조

```text
.codex/AGENTS.md
  매 세션에 필요한 최소 전역 원칙만 유지

.agents/skills/
  ai-agent-development-playbook/
  codex-long-run/
  codex-task-router/
  guide-ppt-creator/
  human-centered-project-builder/
  human-readable-code/

install.ps1
  전역 설치/업데이트

verify-install.ps1
  GitHub 저장소 버전과 PC 전역 설치 상태 비교

uninstall.ps1
  Playbook이 관리하는 전역 항목 제거
```

설치 위치:

```text
%USERPROFILE%\.codex\AGENTS.md
%USERPROFILE%\.agents\skills\<skill-name>\
```

## V7에서 달라진 점

### 1. 전역 AGENTS.md 경량화

항상 주입되는 전역 파일은 상세 매뉴얼이 아니라 **작업 원칙과 Skill 라우팅용 인덱스**로 사용합니다.

상세 절차는 필요한 순간에만 Skill에서 읽습니다.

목표:

```text
항상 필요한 규칙 -> AGENTS.md
상황별 상세 워크플로 -> Skills
프로젝트 전용 지식 -> 각 Repository
```

### 2. 모델 라우터의 고정 모델표 제거

`codex-task-router`는 모델 이름/가격을 장기간 하드코딩하지 않습니다.

라우팅이 실제로 필요한 경우에만:

1. 현재 세션 설정
2. 현재 제품에 노출된 모델/Reasoning 옵션
3. 필요할 때 최신 OpenAI Codex 공식 문서

순서로 확인합니다.

### 3. 설치 스크립트 멱등화

이미 같은 Skill이 설치되어 있으면 다시 복사하거나 백업하지 않습니다.

변경이 있을 때만 교체합니다.

### 4. Skill 백업 위치 변경

V6까지는 기존 Skill 백업이 다음처럼 Skill 검색 경로 안에 생길 수 있었습니다.

```text
%USERPROFILE%\.agents\skills\skill-name.backup-YYYYMMDD-HHMMSS
```

이 구조는 백업 안의 `SKILL.md`가 중복 Skill로 탐색될 가능성이 있습니다.

V7부터 백업은 다음 위치로 이동합니다.

```text
%USERPROFILE%\.codex\playbook-backups\<timestamp>\
```

기존 `*.backup-*` 폴더도 설치 시 Skill 검색 경로 밖으로 이동합니다.

### 5. 설치 검증 추가

```powershell
.\verify-install.ps1
```

을 실행하면 Repository 버전과 전역 설치본을 비교해:

```text
PASS
DRIFT
MISSING
```

으로 확인합니다.

---

# Windows 설치

## 처음 설치

```powershell
git clone https://github.com/tmdgns104/codex-ai-agent-playbook.git
cd codex-ai-agent-playbook
git switch v7-context-efficient

Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

설치 후 자동 검증이 실행됩니다.

직접 다시 확인하려면:

```powershell
.\verify-install.ps1
```

## 기존 설치를 V7 후보로 업데이트

이미 Repository를 내려받아 둔 경우:

```powershell
cd <codex-ai-agent-playbook 폴더>

git status
git fetch origin
git switch v7-context-efficient
git pull

Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
.\verify-install.ps1
```

`git status`에 직접 수정한 파일이 있다면 먼저 확인한 뒤 진행합니다.

## V7이 main에 병합된 뒤

```powershell
cd <codex-ai-agent-playbook 폴더>
git switch main
git pull origin main

Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
.\verify-install.ps1
```

그 다음 **새 Codex 세션**을 시작합니다.

---

# 포함 Skills

| Skill | 용도 |
| --- | --- |
| `ai-agent-development-playbook` | 비단순 개발, 설계, Agent/RAG/tooling, 계약, 검증 |
| `codex-long-run` | 여러 구현/디버깅/검증 사이클이 필요한 장기 작업 |
| `codex-task-router` | 모델/Reasoning/병렬 실행 선택이 실제로 필요한 경우의 추천 |
| `human-readable-code` | 사람이 읽고 배우기 쉬운 코드, 구조, 설명 |
| `human-centered-project-builder` | 요구부터 구현·검증까지 한 번에 진행하는 프로젝트 워크플로 |
| `guide-ppt-creator` | 기술 문서/프로젝트를 가이드 PPTX로 변환 |

기본 원칙은 **전부 사용하지 않는 것**입니다.

현재 작업에 필요한 최소 Skill만 사용합니다.

---

# 추천 사용 방식

작은 수정:

```text
버그 원인을 확인하고 최소 수정 후 관련 테스트까지 실행해.
```

일반적인 비단순 개발:

```text
$ai-agent-development-playbook

현재 Repository의 요구사항/아키텍처를 먼저 확인하고
현재 Task 범위만 구현한 뒤 Evidence로 완료 여부를 판단해.
```

장기 작업:

```text
$codex-long-run

현재 Repository 상태를 기준으로 하나의 결과만 끝까지 진행해.
불필요한 전체 스캔과 반복 로그 출력을 줄이고
필요한 검증 Evidence를 남겨.
```

라우팅이 정말 필요한 경우:

```text
$codex-task-router

이 작업에 현재 Codex의 어떤 capability가 적절한지만 추천해.
구현은 하지 마.
```

---

# 제거

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\uninstall.ps1
```

전역 `AGENTS.md`에서는 `AI_AGENT_PLAYBOOK_KIT` 마커 구간만 제거하고,
이 Repository가 관리하는 Skill만 제거합니다.

백업은 자동 삭제하지 않습니다.

```text
%USERPROFILE%\.codex\playbook-backups\
```

에서 필요 없는 백업을 사용자가 직접 정리할 수 있습니다.

---

# 설계 원칙

- Chat 기록보다 Repository를 지속 가능한 Source of Truth로 사용
- 한 번에 하나의 coherent outcome
- 자기 보고 PASS가 아니라 Test/Diff/Artifact Evidence로 완료 판단
- 전역 규칙은 짧게 유지
- 세부 워크플로는 Skill로 Progressive Disclosure
- 프로젝트 전용 규칙은 프로젝트 Repository에 유지
- 토큰 절감이 정확성이나 검증 신뢰성을 낮추면 채택하지 않음
