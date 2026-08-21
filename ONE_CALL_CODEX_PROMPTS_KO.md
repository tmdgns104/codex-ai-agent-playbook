# Codex CLI 한 번 호출용 Prompt

## 1. 새 프로젝트를 설계부터 시작

```text
$human-centered-project-builder

BUILD_REQUEST.md를 읽어.

이 프로젝트는 결과물만 얻는 것이 아니라
내가 코드를 읽으면서 시스템을 이해할 수 있어야 한다.

먼저 문제/요구사항/성공기준/Architecture/주요 기술 선택을 정리하고
PROJECT.md, REQUIREMENTS.md, ARCHITECTURE.md, DECISIONS.md,
AGENTS.md, TASK-001.md를 작성해.

중요한 불확실성이 있으면 질문해.
지금은 설계 승인 전까지 코딩하지 마.
```

## 2. 설계부터 TASK-001 구현까지

```text
$human-centered-project-builder

BUILD_REQUEST.md와 현재 저장소를 읽어.

먼저 설계와 Task 범위를 정리한 뒤
승인된 범위에서 TASK-001을 구현해.

코드는 다른 개발자가 처음 읽어도 이해할 수 있게:
- 의미 있는 이름
- 단순한 제어 흐름
- 명확한 함수/모듈 책임
- 불필요한 추상화 금지
- WHY 중심 주석
- 핵심 데이터 흐름 가시화
- README 코드 읽는 순서
를 지켜.

구현 후 실제 테스트를 실행하고
Acceptance Criteria, Readability Review, UNVERIFIED 항목을 보고해.
```

## 3. 이미 설계된 프로젝트에서 Task 구현

```text
$human-centered-project-builder

tasks/TASK-001.md를 구현해.

AGENTS.md, REQUIREMENTS.md, ARCHITECTURE.md, DECISIONS.md를 먼저 확인하고
Task 범위를 벗어나지 마.

구현 → 테스트 → diff/review → README 갱신 → 코드 설명 순서로 진행해.
```

## 4. 세부 Skill을 직접 함께 사용

```text
$ai-agent-development-playbook
$human-readable-code

TASK-001을 구현해.
설계 규칙과 사람이 이해하기 쉬운 코드 규칙을 모두 적용해.
```
