# V5 변경사항

V5는 V4에 두 개의 Skill을 추가한다.

## `human-readable-code`

Codex가 작동만 하는 코드가 아니라 사람이 읽고 배우고 유지보수하기 쉬운
코드를 작성하도록 한다.

핵심:
- 의미 있는 이름
- 명확한 함수/모듈 책임
- 핵심 실행/데이터 흐름 가시성
- 불필요한 추상화 금지
- WHY 중심 주석
- README 코드 읽는 순서
- 구현 후 설명
- 휴리스틱 readability audit

## `human-centered-project-builder`

프로젝트 설계 + Task 분해 + 사람이 이해하기 쉬운 구현 + 테스트 + 설명을
한 번의 Skill 호출로 시작하는 통합 워크플로.

```text
Problem
→ Requirements
→ Architecture
→ Task Contract
→ Human-Readable Implementation
→ Test
→ Acceptance Check
→ README / Explanation
→ Evidence
```

## V5 Skills

```text
$ai-agent-development-playbook
$human-readable-code
$human-centered-project-builder
$guide-ppt-creator
```

가장 간단한 통합 사용:

```text
$human-centered-project-builder

BUILD_REQUEST.md를 읽고 이 프로젝트를 설계하고 구현해.
```
