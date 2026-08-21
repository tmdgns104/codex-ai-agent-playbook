# Codex AI Agent Playbook Kit v6

Codex를 단순한 코드 생성기가 아니라 **설계, Task, 검증, 설명, Evidence를 갖춘 개발 파트너**로 사용하기 위한 전역 Playbook + Skill Kit입니다.

핵심 흐름은 다음과 같습니다.

```text
Problem
→ Requirements
→ Architecture
→ Task
→ Implementation
→ Verification
→ Evidence / Explanation
```

v6는 기존 v5의 4개 Skill을 유지하면서, 긴 개발 작업을 안정적으로 이어가는 `codex-long-run`과 작업별 적절한 Codex capability를 고르는 `codex-task-router`를 추가합니다.

## 처음이라면 여기부터

| 하고 싶은 일 | 먼저 볼 문서 |
|---|---|
| 설치하고 바로 써보고 싶다 | [Quick Start](docs/QUICKSTART.md) |
| Playbook이 어떻게 작동하는지 알고 싶다 | [How It Works](docs/HOW_IT_WORKS.md) |
| 6개 Skill의 역할과 사용 시점을 알고 싶다 | [Skills Guide](docs/SKILLS.md) |
| Playbook 자체를 수정하거나 발전시키고 싶다 | [Development Guide](docs/DEVELOPMENT.md) |
| v5에서 무엇이 바뀌었는지 보고 싶다 | [V6 변경사항](V6_CHANGES_KO.md) |

## 왜 만들었나

AI Coding Agent는 빠르지만 다음 문제가 생길 수 있습니다.

- 요구사항이 정리되기 전에 바로 구현한다.
- Architecture를 조용히 바꾼다.
- 현재 Task 밖까지 수정한다.
- 테스트하지 않은 결과를 완료라고 보고한다.
- 긴 작업에서 Context와 현재 상태를 잃는다.
- 단순 작업에도 과도한 모델/절차를 사용하거나, 반대로 어려운 작업에 부족한 capability를 사용한다.
- 코드는 동작하지만 사람이 읽고 배우기 어렵다.

이 Kit는 이런 문제를 프롬프트 한 줄이 아니라 **전역 개발 원칙 + 역할별 Skill + Repository Source of Truth + 실제 Verification**으로 줄이는 것을 목표로 합니다.

## v6에 포함된 6개 Skill

| Skill | 역할 |
|---|---|
| `ai-agent-development-playbook` | 복잡한 개발, Architecture, RAG/Agent/Tool 설계, Contract와 Evidence |
| `human-readable-code` | 사람이 읽고 배우기 쉬운 코드, 구조, 이름, 설명, Readability Review |
| `human-centered-project-builder` | Problem부터 구현·테스트·설명까지 한 번에 시작하는 통합 워크플로 |
| `guide-ppt-creator` | 기술/교육 PPT를 Storyboard → Build → Render → QA 순서로 제작 |
| `codex-long-run` | 긴 Repository 작업의 Context, Verification Budget, Checkpoint/Resume 관리 |
| `codex-task-router` | 정의된 작업의 위험·복잡도에 맞는 모델/Reasoning/Topology 추천 |

각 Skill은 모든 작업에 동시에 쓰지 않습니다. 현재 작업에 필요한 최소 Skill만 선택합니다.

## 5분 설치 - Windows

PowerShell에서:

```powershell
git clone https://github.com/tmdgns104/codex-ai-agent-playbook.git
cd codex-ai-agent-playbook
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

설치되면 기본적으로 다음 위치를 사용합니다.

```text
$HOME\.codex\AGENTS.md
$HOME\.agents\skills\ai-agent-development-playbook\
$HOME\.agents\skills\human-readable-code\
$HOME\.agents\skills\human-centered-project-builder\
$HOME\.agents\skills\guide-ppt-creator\
$HOME\.agents\skills\codex-long-run\
$HOME\.agents\skills\codex-task-router\
```

기존 `$HOME\.codex\AGENTS.md`가 있다면 설치 스크립트는 `AI_AGENT_PLAYBOOK_KIT` marker 구간만 추가하거나 갱신하여 다른 사용자 전역 규칙을 보존합니다.

## 설치 확인

새 터미널에서 Codex를 실행한 뒤 예를 들어:

```text
$ai-agent-development-playbook

이 Skill의 목적과 현재 프로젝트에서 언제 사용해야 하는지 설명해.
코드는 수정하지 마.
```

또는:

```text
$human-centered-project-builder

현재 Repository를 읽고 아직 구현하지 말고
Problem, Requirements, Architecture 상태와 첫 Task 후보만 정리해.
```

처럼 확인할 수 있습니다.

## 가장 간단한 실제 사용법

새 프로젝트라면:

```text
$human-centered-project-builder

이 프로젝트를 시작해.
바로 구현하지 말고 Problem → Requirements → Architecture → Task 순서로 진행해.
```

이미 설계된 프로젝트의 구현이라면:

```text
$ai-agent-development-playbook
$human-readable-code

Repository 문서와 현재 Task를 읽고 승인된 범위만 구현해.
완료 전 테스트와 Acceptance Criteria를 실제로 검증해.
```

긴 작업이라면 `codex-long-run`이 Repository 상태와 Verification을 중심으로 작업을 이어가도록 돕습니다. 모델/Reasoning 선택 자체가 중요한 경우에만 `codex-task-router`를 사용합니다.

## Human + ChatGPT + Work + Codex

이 Playbook은 다음 역할 분리를 권장합니다.

```text
Human
  목적 / 범위 / 중요한 결정 / 최종 승인
        ↓
ChatGPT / Work
  설계 / 기술 판단 / 명세 / 문서 / Review
        ↓
Repository
  PROJECT / REQUIREMENTS / ARCHITECTURE / DECISIONS / STATUS / TASK
        ↓
Codex
  구현 / 테스트 / 디버깅 / Evidence
```

대화 기록 자체를 프로젝트의 공식 상태로 사용하지 않고, 가능한 한 Repository 문서를 Source of Truth로 유지합니다.

## 프로젝트 크기에 따라 최소 구조 사용

모든 프로젝트에 모든 문서를 강제로 만들지 않습니다.

- 작은 수정: inspect → edit → focused test → report
- 일반 기능: Requirements → Architecture impact → Task → implement → verify
- 복잡한 Agent/RAG: State/Tool/Resource/Verification/Evaluation 계약 추가
- 장기 작업: `codex-long-run`으로 Context와 Evidence 유지
- capability 선택이 중요한 경우: `codex-task-router`

핵심은 절차를 많이 만드는 것이 아니라 **현재 위험과 복잡성에 맞는 최소 충분한 구조**를 사용하는 것입니다.

## Repository 구조

```text
codex-ai-agent-playbook/
├─ README.md
├─ V6_CHANGES_KO.md
├─ docs/
│  ├─ QUICKSTART.md
│  ├─ HOW_IT_WORKS.md
│  ├─ SKILLS.md
│  └─ DEVELOPMENT.md
├─ .codex/
│  └─ AGENTS.md
├─ .agents/
│  └─ skills/
│     ├─ ai-agent-development-playbook/
│     ├─ human-readable-code/
│     ├─ human-centered-project-builder/
│     ├─ guide-ppt-creator/
│     ├─ codex-long-run/
│     └─ codex-task-router/
├─ install.ps1
├─ install.sh
├─ uninstall.ps1
└─ uninstall.sh
```

## 제거

Windows PowerShell:

```powershell
.\uninstall.ps1
```

Kit가 추가한 전역 marker 구간과 설치된 Skill을 제거하도록 설계되어 있습니다. 기존 개인 지침은 marker 밖에 있으면 유지됩니다.

## 버전

현재 개발 버전: **v6 candidate**

v6의 핵심 변화는 `codex-long-run`, `codex-task-router`, 전역 개발 규칙 정리, GitHub 사용자 문서 추가입니다.
