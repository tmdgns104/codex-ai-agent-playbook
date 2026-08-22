# Skills 가이드 - V8

V8에는 7개의 managed Skill이 있습니다.

중요한 원칙은 **모든 Skill을 항상 같이 쓰지 않는 것**입니다.
현재 작업에 필요한 최소 조합만 선택합니다.

## 빠른 선택표

| 상황 | 추천 Skill |
|---|---|
| 어떤 Skill이 필요한지 애매한 비단순 작업 | `codex-skill-router` |
| 복잡한 기능/Architecture/Agent/RAG/Tool 설계 | `ai-agent-development-playbook` |
| 코드 가독성/학습/유지보수성이 중요 | `human-readable-code` |
| 새 프로젝트를 처음부터 체계적으로 시작 | `human-centered-project-builder` |
| 기술/교육용 PPT 제작 | `guide-ppt-creator` |
| 여러 구현·디버깅·검증 사이클이 필요한 긴 작업 | `codex-long-run` |
| 모델/Reasoning/병렬 topology 선택이 실제로 중요한 작업 | `codex-task-router` |

---

## 1. codex-skill-router

### 역할

Skill 선택이 애매한 비단순 작업에서 **최소 Skill 집합과 검증 Profile**을 추천합니다.

### 추천 결과

- 필요한 최소 Skill
- `MINIMAL / STANDARD / STRICT`
- long-run 필요 여부
- capability router 필요 여부
- Human Gate 필요 여부

### 사용하지 않을 때

- 오타 한 줄 수정
- 명확한 단일 파일 수정
- 이미 사용할 Skill이 분명한 작업
- 단순 질문

### 사용 예

```text
$codex-skill-router

현재 작업에 필요한 최소 Skill과 검증 Profile만 추천해.
구현은 하지 마.
```

Router 자체는 구현을 대신하지 않습니다.

---

## 2. ai-agent-development-playbook

### 역할

복잡한 소프트웨어 작업을 Human-approved engineering process 안에서 진행하도록 합니다.

### 주로 하는 일

- Requirements/Architecture 확인
- Task Contract 기반 구현
- Agent/RAG/Tool runtime 설계 검토
- State/Tool/Resource 계약
- Human Gate
- Evidence 기반 완료

### 사용 예

```text
$ai-agent-development-playbook

ARCHITECTURE.md와 현재 Task를 읽고
승인된 범위만 구현해.
완료 전 Verification을 실제 실행해.
```

---

## 3. human-readable-code

### 역할

작동만 하는 코드가 아니라 사람이 읽고 배우고 유지보수하기 쉬운 코드를 만들도록 합니다.

### 우선순위

```text
Correctness
-> Understandability
-> Testability
-> Maintainability
-> Performance
-> Cleverness
```

### 주요 원칙

- 의미 있는 이름
- 명확한 함수/모듈 책임
- 추적 가능한 데이터 흐름
- 불필요한 abstraction 금지
- WHY 중심 comment/docstring
- 구현 후 설명과 Readability Review

### 사용 예

```text
$human-readable-code

이 모듈을 동작은 유지하면서
초보 개발자가 흐름을 따라갈 수 있도록 refactor하고 설명해.
```

---

## 4. human-centered-project-builder

### 역할

새 프로젝트 또는 비단순 프로젝트를 구조적으로 시작합니다.

```text
Problem
-> Requirements
-> Architecture
-> Task
-> Readable Implementation
-> Verification
-> Explanation
```

### 언제 좋은가

- 새 Repository 시작
- 설계 문서가 아직 없음
- 구현뿐 아니라 구조와 설명까지 필요
- 학습 목적 프로젝트

---

## 5. guide-ppt-creator

### 역할

기술 자료를 단순 텍스트 슬라이드가 아니라 사람이 이해할 수 있는 가이드 PPT로 변환합니다.

### 기본 흐름

```text
Source Analysis
-> Audience / Goal
-> Storyboard
-> Slide Contract
-> Diagram Plan
-> Speaker Notes
-> PPTX Build
-> Render / Inspect
-> Visual QA
-> Content QA
```

### 특징

- Storyboard 먼저 작성
- 발표자 노트는 지시문이 아니라 실제 설명문
- 가능한 경우 렌더링 후 시각 검증
- 렌더링하지 못했으면 `VISUAL QA: UNVERIFIED`

---

## 6. codex-long-run

### 역할

긴 Repository 작업을 여러 cycle/session에 걸쳐 안정적으로 이어갑니다.

### 담당

- minimum sufficient context
- stale state guard
- one coherent outcome
- focused verification budget
- meaningful checkpoint
- repository-based resume
- pause/stop handoff

### 담당하지 않음

- 프로젝트 Architecture 새로 결정
- 기술 stack 임의 선택
- Repository 규칙 대체

### 사용 시점

- repository-level feature
- difficult bug investigation
- migration/refactor
- repeated test/debug cycles
- 여러 세션이 필요할 수 있는 작업

### 사용하지 않을 때

- typo
- 작은 isolated edit
- 단순 질문
- 한 번에 바로 끝나는 수정

---

## 7. codex-task-router

### 역할

하나의 충분히 정의된 work unit에 대해 최소 충분한 Codex capability를 추천합니다.

**구현은 하지 않습니다.**

### 판단 기준

- Complexity
- Uncertainty
- Risk
- Project Criticality
- Architecture Impact
- Breadth
- Verification Difficulty
- Parallelizability
- Routing Confidence
- Cost Sensitivity

### 논리적 Route

```text
LIGHT
STANDARD
DEEP
CRITICAL
PARALLEL COMPLEX
```

실제 모델 이름이나 reasoning option은 바뀔 수 있으므로 현재 runtime/product 상태를 확인하도록 설계되어 있습니다.

---

# Skill Router와 Task Router의 차이

둘은 역할이 다릅니다.

```text
codex-skill-router
-> 어떤 Skill/검증 Profile이 필요한가?

codex-task-router
-> 충분히 정의된 작업에 어떤 Codex capability가 적절한가?
```

작은 작업에서는 둘 다 사용하지 않아도 됩니다.

---

# 조합 예

## 작은 수정

```text
Skill 없음
또는 해당 작업에 직접 필요한 Skill 1개
```

## 일반 복잡 기능

```text
ai-agent-development-playbook
+ 필요하면 human-readable-code
```

## 새 프로젝트

```text
human-centered-project-builder
```

## 복잡하고 긴 프로젝트 작업

```text
ai-agent-development-playbook
+ codex-long-run
```

## Skill 선택부터 애매한 작업

먼저:

```text
codex-skill-router
```

그 결과에 따라 필요한 Skill만 로드합니다.

## 모델/Reasoning 선택까지 중요한 작업

필요한 경우에만:

```text
codex-task-router
```

## 기술 PPT

```text
guide-ppt-creator
```

---

# V8 검증 Profile과 Skill의 관계

Skill 수와 검증 강도는 같은 개념이 아닙니다.

```text
MINIMAL
-> 작은 저위험 변경

STANDARD
-> 일반적인 비단순 개발

STRICT
-> 보안/권한/배포/마이그레이션/중요 Architecture 등 고위험 변경
```

강한 모델을 썼다고 STRICT 검증을 생략할 수 없고,
작은 작업이라고 불필요하게 많은 Skill을 로드할 필요도 없습니다.

---

# 선택 원칙

```text
현재 Task에 직접 필요한 최소 Skill만 사용
```

Skill 자체보다 Repository의 승인된 Requirements, Architecture, Task가 우선합니다.

V8의 목표는 Skill을 많이 추가하는 것이 아니라 **필요한 순간에만 필요한 Skill을 읽어 Context 비용을 줄이는 것**입니다.
