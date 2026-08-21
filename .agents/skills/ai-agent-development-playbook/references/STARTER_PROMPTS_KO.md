# Codex Starter Prompts

## 1. New project discovery — do not code yet

```text
$ai-agent-development-playbook

새 프로젝트를 시작한다.

지금은 코드를 작성하지 마.
먼저 문제와 요구사항을 정리하고, 필요한 질문을 해.

다음을 확정하자:
1. Problem
2. Goal
3. Users
4. Scope
5. Out of Scope
6. Functional Requirements
7. Non-Functional Requirements
8. Success Criteria
9. Architecture
10. Major technical decisions

합의된 내용만 문서에 기록하고,
설계 승인 전에는 구현 단계로 넘어가지 마.
```

## 2. Implement one task

```text
$ai-agent-development-playbook

현재 작업은 tasks/TASK-001.md다.

AGENTS.md와 관련 Architecture/Decision 문서를 먼저 확인해.
Task Contract 범위를 벗어나지 마.

구현 후:
- Verification을 실제 실행
- Acceptance Criteria별 PASS/FAIL
- 변경 파일
- 실행 명령
- 테스트 결과
- UNVERIFIED
- 위험
을 보고해.
```

## 3. Bug analysis first

```text
$ai-agent-development-playbook

다음 오류를 분석해.

[ERROR LOG]

바로 수정하지 말고 먼저:
1. 재현 조건
2. 최초 오류 위치
3. 직접 원인
4. 근본 원인
5. 영향 범위
6. 최소 수정 후보

를 정리해.

그 다음 최소 수정으로 해결하고 regression test를 추가해.
```

## 4. Architecture change

```text
현재 구현은 승인된 Architecture와 충돌하는 것 같다.

코드를 변경하지 말고 DESIGN CHANGE REQUIRED 형식으로:
- current design
- problem
- proposed design
- alternatives
- affected interfaces
- risks
- migration impact
을 작성해.
```

## 5. GPT/Reviewer handoff package

Codex에게 아래를 준비시키고 ChatGPT에 가져온다.

```text
현재 Task에 대한 Review package를 만들어.

포함:
- Task
- relevant architecture/decision excerpts
- RESULT
- git diff
- tests
- unresolved risks
```
