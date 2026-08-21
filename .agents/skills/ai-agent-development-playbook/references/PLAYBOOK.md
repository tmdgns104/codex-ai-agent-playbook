# AI Agent Development Playbook v3
## Human + GPT + Codex + Agent Runtime Engineering

> **핵심 철학**
>
> AI가 무작정 코드를 만들어내는 것이 아니라,
>
> **Human이 목적과 최종 판단을 소유하고, GPT와 상위 시스템을 설계하며,
> Codex가 합의된 경계 안에서 구현하고,
> 구현된 AI Agent는 State / Node / Tool / Resource / Verification / Persistence 규칙에 따라 동작한다.**
>
> 모든 완료는 **Evidence + Verification + Review**로 증명한다.

---

# 0. V3에서 달라진 점

V2는 주로 다음 문제에 답했다.

> "Human, GPT, Codex가 어떻게 협업하여 소프트웨어를 개발할 것인가?"

V3는 여기에 하나를 더 추가한다.

> "우리가 만드는 AI Agent 자체는 어떤 구조와 통제 규칙으로 설계할 것인가?"

따라서 V3는 세 개의 Layer로 나뉜다.

```text
┌──────────────────────────────────────────────┐
│ PART A. Agent-Assisted Software Engineering  │
│                                              │
│ Human + GPT + Codex가                        │
│ 프로젝트를 어떻게 설계/구현/검증하는가      │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│ PART B. Agent Runtime Engineering            │
│                                              │
│ 우리가 만드는 Agent가                       │
│ State / Node / Tool / RAG / MCP / Verify /  │
│ Checkpoint 구조로 어떻게 동작하는가          │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│ PART C. Agent Operations                     │
│                                              │
│ Security / Observability / Cost / Failure /  │
│ Recovery / Evaluation / Learning Loop        │
└──────────────────────────────────────────────┘
```

---

# 1. 전체 운영 모델

```text
                       HUMAN
             Problem / Goal / Approval
                         │
                         ▼
                        GPT
          Requirements / Architecture / Review
                         │
                         ▼
             Shared Project Knowledge
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
 Software Architecture             Agent Architecture
 ARCHITECTURE.md                    AGENT_ARCHITECTURE.md
        │                                 │
        └────────────────┬────────────────┘
                         ▼
                   TASK CONTRACT
                         │
                         ▼
                       CODEX
           Implement / Execute / Test
                         │
                         ▼
                  Runtime Agent
                         │
                State / Graph
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
        Tools         Resources       Memory
        MCP            RAG          Checkpoint
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                     VERIFY
                         │
             PASS / RETRY / HUMAN / FAIL
                         │
                         ▼
                 Evidence / Result
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
            GPT                    HUMAN
      Technical Review        Product Acceptance
             │                       │
             └───────────┬───────────┘
                         ▼
                       DONE
                         │
                         ▼
                   LEARNING LOOP
```

---

# PART A. AGENT-ASSISTED SOFTWARE ENGINEERING

# 2. 역할

## 2.1 Human

Human은 다음을 소유한다.

- 해결할 문제
- 프로젝트 목적
- 사용자 가치
- 범위와 우선순위
- 위험 허용 수준
- Production 영향 승인
- 주요 Architecture 승인
- Release 승인
- 최종 Acceptance

Human은 코드 전체를 직접 작성할 필요는 없다.

하지만 다음 질문에는 답할 수 있어야 한다.

```text
무엇을 만드는가?
왜 만드는가?
무엇이 성공인가?
Agent가 무엇을 해도 되는가?
Agent가 무엇을 하면 안 되는가?
결과를 신뢰할 근거가 있는가?
```

---

# 2.2 GPT

GPT의 역할:

```text
Problem Framing
Requirements Engineering
Architecture Design
Trade-off Analysis
Task Decomposition
Contract Design
Agent Runtime Design
Review
Failure Analysis
```

GPT는 상위 설계자이자 Reviewer다.

GPT가 Repository의 실제 실행 결과를 추측으로 대신해서는 안 된다.

---

# 2.3 Codex

Codex는 Implementation Agent다.

허용되는 역할:

```text
Repository 탐색
코드 이해
구현
테스트 작성
명령 실행
오류 분석
작은 범위 리팩터링
Evidence 작성
```

핵심 원칙:

> **상위 Architecture를 존중하면서 내부 구현 방식은 자율적으로 판단한다.**

---

# 3. Agent Autonomy Level

## L0 — READ ONLY

분석만 수행.

## L1 — PROPOSE

변경 제안만 수행.

## L2 — SCOPED EDIT

지정 파일 수정.

## L3 — IMPLEMENT + TEST

일반적인 구현 기본 권한.

## L4 — MULTI-MODULE REFACTOR

여러 모듈 변경 가능.

## L5 — ARCHITECTURE CHANGE

Human 승인 필수.

---

# 4. Definition of Ready

Task가 READY가 되려면 최소한 다음이 정의되어야 한다.

- [ ] Goal
- [ ] Related Requirement
- [ ] Input
- [ ] Output
- [ ] Allowed Changes
- [ ] Forbidden Changes
- [ ] Acceptance Criteria
- [ ] Verification
- [ ] Autonomy Level
- [ ] Change Budget
- [ ] Architecture 영향

---

# 5. Definition of Done

DONE 조건:

- [ ] 기능 구현
- [ ] Acceptance Criteria 만족
- [ ] Unit/Integration Test 통과
- [ ] Regression Test 통과
- [ ] Architecture Invariant 위반 없음
- [ ] Change Budget 위반 없음
- [ ] Security 위반 없음
- [ ] Evidence 존재
- [ ] GPT Review 완료
- [ ] 필요 시 Human Acceptance 완료

---

# 6. 표준 Repository 구조

```text
project/
│
├── PROJECT.md
├── REQUIREMENTS.md
├── ARCHITECTURE.md
├── AGENT_ARCHITECTURE.md
├── STATE.md
├── AGENTS.md
├── DECISIONS.md
│
├── docs/
│   ├── INVARIANTS.md
│   ├── TESTING.md
│   ├── SECURITY.md
│   ├── PERSISTENCE.md
│   ├── OBSERVABILITY.md
│   ├── OPERATIONS.md
│   └── CONVENTIONS.md
│
├── contracts/
│   ├── nodes/
│   ├── tools/
│   └── resources/
│
├── tasks/
│   ├── TASK-001.md
│   └── TASK-002.md
│
├── results/
├── reviews/
├── evaluation/
├── src/
└── tests/
```

작은 프로젝트에서는 다음부터 시작해도 된다.

```text
PROJECT.md
ARCHITECTURE.md
AGENT_ARCHITECTURE.md
AGENTS.md
tasks/
```

---

# 7. PROJECT.md

```markdown
# Project

## Problem

## Goal

## Users

## Scope

## Out of Scope

## Success Criteria

## Constraints

## Risk Level
```

---

# 8. REQUIREMENTS.md

Requirement에는 ID를 붙인다.

```markdown
# Requirements

## Functional

FR-001
사용자는 PDF 문서를 등록할 수 있다.

FR-002
질문에 관련된 문서를 검색할 수 있다.

## Non-Functional

NFR-001
Secret은 Source Code에 저장되지 않는다.

## Agent Requirements

AR-001
Agent는 Tool 실행 전 위험도를 확인해야 한다.

AR-002
HIGH Risk Tool은 Human Approval 없이 실행하지 않는다.
```

---

# 9. ARCHITECTURE.md

일반 Software Architecture를 정의한다.

예:

```text
Frontend
  ↓
FastAPI
  ↓
Agent Service
  ↓
Database
Vector Store
External API
```

여기서는 다음을 정의한다.

- Component
- 책임
- Interface
- Dependency
- Data Flow
- Infrastructure
- Deployment Boundary

---

# 10. DECISIONS.md

중요 결정은 ADR로 남긴다.

```markdown
## ADR-004 Agent Orchestration

Status:
Accepted

Decision:
LangGraph StateGraph 사용

Reason:
State 기반 Node/Edge/Conditional Edge와
Checkpoint 관리가 필요하기 때문.

Alternatives:
- 직접 Python Loop
- 다른 orchestration framework

Trade-offs:
Framework 의존성이 증가한다.
```

---

# 11. Task Contract

```markdown
# TASK-XXX

Status: READY

## Goal

## Related Requirements

## Context

## Input

## Output

## Allowed Changes

## Forbidden Changes

## Autonomy Level

L3

## Change Budget

- Max modified files:
- New dependency:
- Public API change:
- DB migration:
- Architecture change:

## Acceptance Criteria

### AC-001

### AC-002

## Verification

## Completion Evidence
```

---

# 12. Change Budget

Task가 수정할 수 있는 범위를 제한한다.

```text
Max modified files: 4
New dependencies: 0
Public API changes: 0
DB migrations: 0
Architecture changes: 0
```

초과 시:

```text
CHANGE BUDGET EXCEEDED
```

를 보고하고 승인 전에는 범위를 확장하지 않는다.

---

# PART B. AGENT RUNTIME ENGINEERING

# 13. Agent Architecture의 기본 개념

Agent는 단순 LLM 호출이 아니다.

Agent는 다음 구성 요소를 가진 **상태 기반 실행 시스템**으로 본다.

```text
User Input
    ↓
State
    ↓
Plan
    ↓
Execute
    ↓
Tools / Resources
    ↓
Verify
    ↓
Conditional Route
    ├ PASS → Complete
    ├ RETRY → Execute/Replan
    ├ HUMAN_REQUIRED → Human Gate
    └ FAIL → Fail
    ↓
Checkpoint
```

---

# 14. AGENT_ARCHITECTURE.md

Agent의 Runtime Architecture를 일반 Software Architecture와 분리한다.

```markdown
# Agent Architecture

## Goal

## State

## Nodes

## Edges

## Conditional Routes

## Tools

## Resources

## Checkpoint Strategy

## Human Approval Gates

## Execution Budget

## Failure States

## Observability

## Evaluation
```

---

# 15. State Contract

Agent는 결국 State를 변화시키는 프로그램이다.

예:

```python
AgentState = {
    "user_request": ...,
    "plan": ...,
    "current_step": ...,
    "retrieved_context": ...,
    "tool_results": ...,
    "verification_result": ...,
    "retry_count": ...,
    "human_feedback": ...,
    "status": ...
}
```

State 설계 원칙:

```text
1. State는 Agent 실행에 필요한 최소 정보만 가진다.
2. 동일 의미 데이터를 여러 필드에 중복 저장하지 않는다.
3. Node별 수정 책임을 정의한다.
4. 복구에 필요한 정보는 persistence 대상에 포함한다.
5. 민감정보는 State에 무분별하게 저장하지 않는다.
```

---

# 16. STATE.md 템플릿

```markdown
# Agent State

## State Schema

### user_request
Owner: INPUT
Persistence: YES

### plan
Owner: PLAN
Persistence: YES

### current_step
Owner: EXECUTE
Persistence: YES

### retrieved_context
Owner: RETRIEVE
Persistence: MAYBE

### tool_results
Owner: EXECUTE
Persistence: YES

### verification_result
Owner: VERIFY
Persistence: YES

### retry_count
Owner: SYSTEM
Persistence: YES

### status
Owner: SYSTEM
Persistence: YES

## Mutation Rules

PLAN:
- plan 수정 가능

EXECUTE:
- current_step
- tool_results

VERIFY:
- verification_result

그 외 State는 임의 변경하지 않는다.
```

---

# 17. Node Contract

Agent 내부 Node도 책임을 명확히 정의한다.

## PLAN Node

```markdown
# NODE-PLAN

## Responsibility

사용자 목표를 실행 가능한 단계로 분해.

## Reads

- user_request
- available_tools
- resource_catalog

## Writes

- plan

## Must Not

- 실제 Tool 실행
- 최종 성공 판정
- Production 변경

## Output

PlanResult
```

---

# 18. EXECUTE Node

```markdown
# NODE-EXECUTE

## Responsibility

현재 Plan Step을 수행.

## Reads

- plan
- current_step
- relevant_context

## May Use

- MCP Tools
- Retriever
- Local Functions

## Writes

- tool_results
- current_step

## Must Not

- 최종 완료 판정
- Human Approval이 필요한 Tool을 승인 없이 호출
```

---

# 19. VERIFY Node

```markdown
# NODE-VERIFY

## Responsibility

현재 실행 결과가 목표와 정책을 만족하는지 검증.

## Reads

- goal
- acceptance_criteria
- tool_results
- policy
- retry_count

## Writes

- verification_result

## Output

PASS
RETRY
REPLAN
HUMAN_REQUIRED
FAIL
```

---

# 20. Human Approval Node

```markdown
# NODE-HUMAN-APPROVAL

## Responsibility

위험한 행동 전에 사람의 명시적 승인을 받는다.

## Trigger

- Data deletion
- Production write
- Email/message send
- 비용 발생
- External side effect
- 설비 제어
- 권한 변경

## Output

APPROVED
REJECTED
MODIFIED
```

---

# 21. Graph 설계

Node를 만든 뒤 Edge를 정의한다.

예:

```text
START
  ↓
PLAN
  ↓
EXECUTE
  ↓
VERIFY
  │
  ├ PASS ─────────→ COMPLETE
  │
  ├ RETRY ────────→ EXECUTE
  │
  ├ REPLAN ───────→ PLAN
  │
  ├ HUMAN_REQUIRED→ HUMAN_APPROVAL
  │                   │
  │                   ├ APPROVED → EXECUTE
  │                   └ REJECTED → FAIL
  │
  └ FAIL ─────────→ FAIL
```

Node를 코드보다 먼저 설계한다.

---

# 22. Node Ownership of State

중요 원칙:

> **Node는 State 전체를 마음대로 수정하지 않는다.**

예:

```text
PLAN
→ plan

EXECUTE
→ current_step, tool_results

RETRIEVE
→ retrieved_context

VERIFY
→ verification_result

SYSTEM
→ retry_count, status
```

이 규칙은 Agent의 예측 가능성을 크게 높인다.

---

# 23. Tool Contract

MCP Tool 또는 내부 Tool은 반드시 계약을 가진다.

```markdown
# TOOL-send-email

## Purpose

메일 전송

## Input

recipient
subject
body

## Output

message_id

## Side Effect

YES

## Risk

MEDIUM

## Human Approval

YES

## Retry Safe

NO

## Idempotent

NO

## Timeout

10s

## Failure Behavior

FAIL하고 재시도하지 않음.
Human에게 상태 보고.
```

---

# 24. Tool Risk Level

## LOW

읽기 전용.

예:

```text
read_file
search_document
get_sensor_value
```

## MEDIUM

외부 변경이 있으나 복구 가능.

예:

```text
create_issue
write_draft
update_noncritical_record
```

## HIGH

중대한 Side Effect.

예:

```text
delete_data
production_deploy
send_payment
shutdown_machine
change_permission
```

HIGH는 Human Approval을 기본으로 한다.

---

# 25. Idempotency

Tool Contract에 반드시 다음을 표시한다.

```text
Side Effect?
Retry Safe?
Idempotent?
```

예:

```text
read_file
Side Effect = NO
Retry Safe = YES
Idempotent = YES

send_email
Side Effect = YES
Retry Safe = NO
Idempotent = NO

upsert_record(id)
Side Effect = YES
Retry Safe = YES
Idempotent = YES
```

Checkpoint 복구 시 중복 실행 방지를 위해 중요하다.

---

# 26. Resource Contract

Tool은 행동이고 Resource는 Context다.

```text
Tool
= "무엇을 한다"

Resource
= "무엇을 참고한다"
```

Resource 예:

```text
PROJECT.md
설비 매뉴얼
DB Schema
Policy
RAG Retriever
Sensor Metadata
```

Resource Contract:

```markdown
# RESOURCE-equipment-manual

## Type

RAG

## Purpose

설비 사용/장애 매뉴얼 검색

## Freshness

Static

## Trust Level

HIGH

## Access

Read only

## Citation Required

YES
```

---

# 27. RAG의 위치

RAG는 Agent 그 자체가 아니다.

RAG는 Agent의 Context Source 중 하나다.

```text
Agent Context

├ Static Resources
│  ├ Policy
│  └ Architecture Docs
│
├ Dynamic Resources
│  ├ DB
│  ├ API
│  └ Sensor
│
└ Retrieval Resources
   └ RAG
      ├ Embedding
      ├ Vector DB
      └ Retriever
```

---

# 28. MCP의 위치

MCP는 Agent가 외부 Tool/Resource와 연결되는 표준 인터페이스 계층으로 본다.

```text
LLM / Agent
     │
     ▼
 MCP Client
     │
     ▼
 MCP Server
 ├ Tools
 └ Resources
```

MCP 사용 자체가 좋은 Architecture를 보장하지는 않는다.

Tool Contract와 Risk Policy가 함께 있어야 한다.

---

# 29. Verification을 3개로 분리

## 29.1 Execution Verification

실제 행동 성공 여부.

```text
파일 생성?
API 200?
DB 변경?
Tool Result 존재?
```

## 29.2 Reasoning Verification

결론의 근거 확인.

```text
답변이 Context에 근거?
RAG Source와 결론 일치?
필요 정보 누락?
환각 가능성?
```

## 29.3 Policy Verification

행동 정책 준수 여부.

```text
권한 초과?
Human Approval 누락?
금지 Tool 사용?
민감정보 외부 전송?
Execution Budget 초과?
```

---

# 30. Verify Gate

Verify Gate는 단순 bool 검사보다 풍부해야 한다.

권장 출력:

```text
PASS
RETRY
REPLAN
HUMAN_REQUIRED
FAIL
```

그리고 이유를 포함한다.

```json
{
  "status": "RETRY",
  "reason": "retrieved context is insufficient",
  "next_action": "retrieve_more_context"
}
```

---

# 31. Execution Budget

Change Budget은 코드 수정 범위를 제한한다.

Execution Budget은 Agent Runtime을 제한한다.

예:

```text
Max iterations: 10
Max node retries: 3
Max tool calls: 20
Max LLM calls: 15
Max retrieval calls: 5
Max runtime: 60 seconds
Max estimated cost: ...
```

초과 시:

```text
BUDGET_EXCEEDED
```

상태로 종료하거나 Human에게 넘긴다.

---

# 32. Retry Policy

Retry는 모든 오류에 적용하지 않는다.

## Retry 가능

```text
Temporary network error
Rate limit
Transient timeout
Incomplete retrieval
```

## Retry 금지

```text
잘못된 사용자 권한
잘못된 입력
Data deletion 실패 후 상태 불명
Non-idempotent Tool 결과 불명
Human rejection
```

---

# 33. Failure Protocol

```text
Attempt 1
→ 원인 확인
→ 최소 수정/재시도

Attempt 2
→ 가설 재평가
→ 추가 Evidence

Attempt 3
→ BLOCKED / FAIL
```

무한 Loop 금지.

---

# 34. Checkpoint / Persistence

Agent가 중간 상태를 저장할 수 있어야 한다.

예:

```text
PLAN 완료
→ checkpoint

외부 Side Effect Tool 실행 전
→ checkpoint

Tool 실행 후
→ result + checkpoint

VERIFY 후
→ checkpoint
```

---

# 35. PERSISTENCE.md

```markdown
# Persistence

## Backend

SQLite / Postgres / etc.

## Persisted State

- plan
- current_step
- tool_results
- verification
- retry_count
- status

## Checkpoint Timing

- after PLAN
- before risky Tool
- after Tool result
- after VERIFY

## Recovery Rule

Crash 후 마지막 확정 checkpoint에서 복구.

## Non-Idempotent Tool Rule

Tool execution ID를 저장하고
중복 실행 여부를 확인한다.

## Retention

## Sensitive Data Policy
```

---

# 36. Human-in-the-Loop

Human은 마지막 승인자만이 아니다.

Runtime 중간에도 등장할 수 있다.

```text
Agent
 ↓
Execute
 ↓
HIGH RISK ACTION
 ↓
INTERRUPT
 ↓
Human
 ↓
APPROVE / REJECT / MODIFY
```

---

# 37. Human Approval Trigger

기본 Human Approval 대상:

```text
Data deletion
Production DB write
Production deployment
외부 메일/메시지 전송
비용 발생
권한 변경
Secret 변경
설비 제어
계약/결제
법적 영향이 있는 행위
```

---

# 38. Observability

Agent Debugging을 위해 다음을 추적한다.

```text
run_id
thread_id
user_id 또는 actor
node
node_input
node_output
tool_call
tool_result
retrieval_query
retrieved_source
latency
retry_count
verification
human_decision
final_status
```

---

# 39. OBSERVABILITY.md

```markdown
# Observability

## Trace Fields

- run_id
- thread_id
- node
- status
- latency

## Tool Trace

- tool
- input summary
- output summary
- duration
- side effect

## Retrieval Trace

- query
- top_k
- source
- score

## Verification Trace

- status
- reason

## Privacy

민감정보는 로그에 그대로 남기지 않는다.
```

---

# 40. Agent Evaluation

Agent는 Unit Test만으로 충분하지 않다.

평가 계층:

```text
Software Test
Agent Behavior Test
RAG Evaluation
Tool Execution Test
Policy Test
Recovery Test
Human Acceptance
```

---

# 41. RAG Evaluation

```text
Retrieval Recall
Context Relevance
Faithfulness
Citation Accuracy
Answer Relevance
No-Answer Behavior
```

---

# 42. Agent Behavior Evaluation

예:

```text
계획이 지나치게 긴가?
불필요한 Tool을 호출하는가?
위험 Tool 전에 승인을 요청하는가?
실패 후 무한 반복하는가?
정보가 부족할 때 사람에게 넘기는가?
```

---

# 43. Failure Recovery Test

반드시 일부 실패를 의도적으로 테스트한다.

```text
LLM timeout
Tool timeout
MCP server down
Vector DB unavailable
Checkpoint restore
Crash after Tool
Human reject
Budget exceeded
```

---

# PART C. AGENT OPERATIONS

# 44. Security

Agent는 일반 애플리케이션보다 공격면이 넓을 수 있다.

검토 대상:

```text
Secret
Prompt Injection
Tool Injection
RAG Poisoning
Path Traversal
SQL Injection
Unauthorized Tool
Cross-user data access
Sensitive log
External data exfiltration
```

---

# 45. Prompt Injection과 Resource 신뢰도

외부 Resource의 텍스트를 System Instruction처럼 취급하면 안 된다.

Resource에는 Trust Level을 둔다.

```text
HIGH
공식 정책 / 내부 승인 문서

MEDIUM
회사 문서 / 검증된 DB

LOW
사용자 업로드
외부 웹 문서
메일
```

LOW Resource의 명령형 텍스트는 Tool Policy를 변경할 수 없다.

---

# 46. Tool Authorization

Tool 실행 권한은 LLM의 말이 아니라 Policy로 결정한다.

나쁜 구조:

```text
LLM이 "실행해도 된다"고 판단
→ 실행
```

좋은 구조:

```text
LLM Request
 ↓
Policy Check
 ↓
Risk Check
 ↓
Human Gate if needed
 ↓
Tool Execute
```

---

# 47. Cost Control

추적:

```text
LLM call count
Input tokens
Output tokens
Embedding calls
Retrieval calls
Tool calls
Runtime
```

Execution Budget과 연결한다.

---

# 48. Performance

Agent Performance는 LLM 속도만이 아니다.

```text
Planning latency
Retrieval latency
Tool latency
Verification latency
Checkpoint latency
End-to-end latency
```

---

# 49. Release Gate

- [ ] Functional Requirements
- [ ] Agent Requirements
- [ ] Software Test
- [ ] Agent Behavior Test
- [ ] Security
- [ ] Persistence
- [ ] Recovery
- [ ] Observability
- [ ] Cost Limit
- [ ] Human Approval Policy
- [ ] Rollback

---

# 50. Rollback

Agent Runtime 변경도 Task 단위로 관리한다.

예:

```text
TASK-010
PLAN node 변경

TASK-011
VERIFY policy 변경

TASK-012
Tool risk policy 변경
```

작은 Commit을 유지한다.

---

# 51. Learning Loop

```text
Incident
 ↓
Root Cause
 ↓
Fix
 ↓
Regression Test
 ↓
Agent Behavior Test
 ↓
어떤 Contract가 부족했나?
 ↓
Task?
State?
Node?
Tool?
Policy?
 ↓
Playbook / Repository Rule 업데이트
```

---

# 52. Contract-Driven Agent Engineering

V3의 핵심은 네 개의 Contract다.

```text
                TASK CONTRACT
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
 STATE CONTRACT  NODE CONTRACT  TOOL CONTRACT
        │            │            │
        └────────────┼────────────┘
                     ▼
             AGENT ARCHITECTURE
                     │
                     ▼
               VERIFY GATE
```

---

# 53. Task Contract

무엇을 구현할 것인가?

---

# 54. State Contract

Agent가 무엇을 기억하고,
누가 어떤 State를 수정할 것인가?

---

# 55. Node Contract

각 Node가 정확히 어떤 책임을 갖는가?

---

# 56. Tool Contract

Agent가 어떤 행동을 할 수 있고,
그 행동의 위험과 Side Effect는 무엇인가?

---

# 57. Contract 간 연결

예:

```text
Requirement
FR-010
"Agent는 매뉴얼 기반으로 장애 원인을 분석한다."

↓

Task Contract
TASK-020
Retriever Node 구현

↓

Node Contract
NODE-RETRIEVE

Reads:
user_query

Writes:
retrieved_context

↓

Resource Contract
RESOURCE-MANUAL-RAG

↓

Tool Contract
없음
(Read-only Resource)

↓

Verify
검색 결과 0건이면
RETRY / NO_ANSWER
```

---

# 58. V3 권장 파일 구조

```text
project/
│
├── PROJECT.md
├── REQUIREMENTS.md
├── ARCHITECTURE.md
├── AGENT_ARCHITECTURE.md
├── STATE.md
├── AGENTS.md
├── DECISIONS.md
│
├── docs/
│   ├── INVARIANTS.md
│   ├── TESTING.md
│   ├── SECURITY.md
│   ├── PERSISTENCE.md
│   ├── OBSERVABILITY.md
│   └── OPERATIONS.md
│
├── contracts/
│   ├── nodes/
│   │   ├── NODE-PLAN.md
│   │   ├── NODE-EXECUTE.md
│   │   └── NODE-VERIFY.md
│   │
│   ├── tools/
│   │   ├── TOOL-read-file.md
│   │   └── TOOL-send-email.md
│   │
│   └── resources/
│       └── RESOURCE-manual-rag.md
│
├── tasks/
├── results/
├── reviews/
├── evaluation/
├── src/
└── tests/
```

---

# 59. AGENTS.md V3 핵심 규칙

```markdown
# AGENTS.md

## Role

너는 이 Repository의 Implementation Agent다.

## Priority

1. Human latest approved decision
2. DECISIONS.md
3. REQUIREMENTS.md
4. ARCHITECTURE.md
5. AGENT_ARCHITECTURE.md
6. STATE.md
7. INVARIANTS.md
8. Current TASK
9. AGENTS.md
10. Existing code

## Rules

1. 상위 Architecture를 임의로 변경하지 않는다.
2. Agent Graph를 임의로 확장하지 않는다.
3. State field를 임의로 추가하지 않는다.
4. Node Contract 책임을 벗어나지 않는다.
5. Tool Risk/Approval Policy를 우회하지 않는다.
6. Non-idempotent Tool 재실행을 주의한다.
7. Execution Budget을 무시하지 않는다.
8. Checkpoint/Recovery 의미를 깨뜨리지 않는다.
9. Test 없이 완료 선언하지 않는다.
10. 실행하지 않은 결과는 UNVERIFIED라고 표시한다.

## Before Work

- Task Contract
- Architecture
- Agent Architecture
- State Contract
- 관련 Node/Tool Contract
- Change Budget

확인.

## After Work

STATUS:
CHANGED:
TESTS:
AGENT_BEHAVIOR:
ACCEPTANCE:
INVARIANTS:
BUDGET:
UNVERIFIED:
RISKS:
NEXT:
```

---

# 60. Codex Runtime 구현 Prompt

```text
AGENTS.md를 먼저 읽어.

그리고 다음을 읽어.

PROJECT.md
REQUIREMENTS.md
ARCHITECTURE.md
AGENT_ARCHITECTURE.md
STATE.md
docs/INVARIANTS.md
docs/TESTING.md
docs/SECURITY.md
docs/PERSISTENCE.md

현재 TASK와 관련 Node/Tool Contract를 읽어.

Task Contract의 범위를 벗어나지 마.

특히 다음을 검증해.

- State mutation ownership
- Node responsibility
- Tool risk
- Idempotency
- Human approval
- Execution budget
- Checkpoint semantics

구현 후 실제 테스트를 실행하고
RESULT Evidence를 작성해.
```

---

# 61. GPT Agent Architecture Review Prompt

```text
너는 AI Agent System Architect / Reviewer다.

다음을 검토해.

PROJECT.md
REQUIREMENTS.md
ARCHITECTURE.md
AGENT_ARCHITECTURE.md
STATE.md
INVARIANTS.md
Node Contracts
Tool Contracts
Task
Result
git diff

검토 기준:

1. Requirement
2. Graph 구조
3. State ownership
4. Node responsibility
5. Tool 권한
6. Side Effect
7. Idempotency
8. Human approval
9. Retry loop
10. Execution budget
11. Persistence
12. Recovery
13. Observability
14. Security
15. Evaluation

결론:

APPROVE
APPROVE WITH NOTES
REQUEST CHANGES
```

---

# 62. RAG Agent 예시

```text
User
 ↓
PLAN
 ↓
RETRIEVE
 ↓
ANALYZE
 ↓
VERIFY
 │
 ├ context 충분 → ANSWER
 └ 부족 → RETRIEVE
```

State:

```text
user_query
plan
retrieved_context
analysis
verification
retry_count
```

Resource:

```text
Manual RAG
Vector DB
Equipment History
```

Tool:

```text
read_sensor
query_alarm_history
```

Verify:

```text
Execution
→ Tool 성공?

Reasoning
→ 답변이 Manual에 근거?

Policy
→ 권한 범위 내 조회?
```

---

# 63. 산업용 Agent 예시

```text
사용자:
"3번 설비 진동이 이상해. 원인을 분석해."
```

Agent:

```text
PLAN

1. 센서 상태 조회
2. 진동 데이터 조회
3. 장애 이력 조회
4. 설비 매뉴얼 검색
5. 원인 후보 생성
6. 근거 검증
```

Runtime:

```text
              PLAN
                │
                ▼
             EXECUTE
          ┌─────┼─────┐
          ▼     ▼     ▼
       Sensor  History RAG
          │     │     │
          └─────┼─────┘
                ▼
             ANALYZE
                │
                ▼
             VERIFY
            /    |    \
         PASS  RETRY  HUMAN
           │
           ▼
         ANSWER
```

설비 제어 Tool이 포함된다면:

```text
shutdown_machine
Risk = HIGH
Human Approval = REQUIRED
Idempotent = NO
```

로 별도 통제한다.

---

# 64. Multi-Agent 확장

V3의 Contract 구조는 Multi-Agent에도 적용한다.

```text
Supervisor Agent
      │
 ┌────┼────┐
 ▼    ▼    ▼
RAG  Data  Control
Agent Agent Agent
```

각 Agent에:

```text
Role Contract
State Boundary
Tool Boundary
Handoff Contract
```

를 둔다.

---

# 65. Handoff Contract

```markdown
# HANDOFF-analysis-to-control

## From

Analysis Agent

## To

Control Agent

## Required Input

- diagnosis
- confidence
- evidence

## Forbidden

Analysis Agent가 직접 설비 제어 Tool 호출 금지.

## Trigger

confidence >= threshold
AND Human Approval
```

---

# 66. Multi-Agent에서 중요한 원칙

> Agent 수가 많다고 좋은 시스템이 아니다.

다음 질문에 YES일 때 분리한다.

```text
책임이 다른가?
권한이 다른가?
Tool이 다른가?
Context가 다른가?
독립 평가가 필요한가?
```

아니면 Single Agent + 여러 Node가 더 단순하다.

---

# 67. V2 → V3 Migration

V2를 사용 중이라면 다음 순서로 확장한다.

```text
1. 기존 V2 유지

2. ARCHITECTURE.md에서
   Agent Runtime 부분 분리

3. AGENT_ARCHITECTURE.md 생성

4. STATE.md 생성

5. 주요 Node에 Node Contract 추가

6. 외부 행동 Tool에 Tool Contract 추가

7. HIGH Risk Tool에 Human Gate 추가

8. Execution Budget 정의

9. PERSISTENCE.md 작성

10. OBSERVABILITY.md 작성

11. Agent Behavior Evaluation 추가
```

---

# 68. V3를 모든 프로젝트에 전부 적용할 필요는 없다

## 단순 Script

필요:

```text
PROJECT
TASK
TEST
```

## 일반 Web Application

필요:

```text
PROJECT
REQUIREMENTS
ARCHITECTURE
TASK
AGENTS
```

## RAG Application

추가:

```text
RAG Evaluation
Resource Contract
```

## Tool-Using Agent

추가:

```text
AGENT_ARCHITECTURE
STATE
Node Contract
Tool Contract
Execution Budget
```

## Production Agent

추가:

```text
Persistence
Observability
Security
Human-in-the-Loop
Recovery
Cost
```

복잡성은 Requirement에 맞게 증가시킨다.

---

# 69. 최종 개발 사이클

```text
HUMAN
Problem
   ↓
GPT
Requirements
   ↓
Software Architecture
   ↓
Agent Architecture
   ↓
Contracts
   ├ Task
   ├ State
   ├ Node
   └ Tool
   ↓
CODEX
Implementation
   ↓
Runtime
   ↓
Verification
   ├ Execution
   ├ Reasoning
   └ Policy
   ↓
Evidence
   ↓
GPT Review
   ↓
Human Acceptance
   ↓
Release
   ↓
Observe
   ↓
Learn
```

---

# 70. V3의 한 문장

> **Human이 목적과 권한을 소유하고, GPT가 상위 시스템과 Agent Runtime을 설계하며, Codex가 Contract 안에서 구현하고, Runtime Agent는 State·Node·Tool·Resource·Checkpoint·Verification 규칙에 따라 행동하며, 모든 결과는 Evidence와 Review로 검증한다.**

---

# APPENDIX A. STATE CONTRACT TEMPLATE

```markdown
# STATE.md

## State Schema

### field_name

Purpose:
Owner:
Persistence:
Sensitive:
Default:

## Mutation Rules

## Validation Rules

## Serialization Rules

## Recovery Rules
```

---

# APPENDIX B. NODE CONTRACT TEMPLATE

```markdown
# NODE-XXX

## Responsibility

## Reads

## Writes

## May Use

## Must Not

## Retry Policy

## Timeout

## Output

PASS / ...

## Failure Behavior
```

---

# APPENDIX C. TOOL CONTRACT TEMPLATE

```markdown
# TOOL-XXX

## Purpose

## Input

## Output

## Side Effect

YES / NO

## Risk

LOW / MEDIUM / HIGH

## Human Approval

YES / NO

## Retry Safe

YES / NO

## Idempotent

YES / NO

## Timeout

## Authorization

## Logging

## Failure Behavior
```

---

# APPENDIX D. RESOURCE CONTRACT TEMPLATE

```markdown
# RESOURCE-XXX

## Type

Static / Dynamic / RAG / API / DB

## Purpose

## Trust Level

HIGH / MEDIUM / LOW

## Freshness

## Access

## Citation Required

## Sensitive Data

## Injection Risk
```

---

# APPENDIX E. EXECUTION BUDGET TEMPLATE

```markdown
# Execution Budget

Max iterations:
Max LLM calls:
Max Tool calls:
Max Retrieval calls:
Max retries per node:
Max runtime:
Max estimated cost:

On exceed:
FAIL / HUMAN_REQUIRED
```

---

# APPENDIX F. RESULT TEMPLATE V3

```markdown
# RESULT-XXX

STATUS:

## Changed Files

## Implementation

## Commands

## Software Tests

## Agent Behavior Tests

## Acceptance Criteria

## Architecture Invariants

## State Contract

## Node Contract

## Tool Contract

## Change Budget

## Execution Budget

## Security

## Persistence

## Unverified

## Risks

## Next
```

---

# APPENDIX G. REVIEW TEMPLATE V3

```markdown
# REVIEW-XXX

Decision:
APPROVE / APPROVE WITH NOTES / REQUEST CHANGES

## Requirements

## Software Architecture

## Agent Architecture

## State

## Nodes

## Tools

## Resources

## Verification

## Human Approval

## Retry / Budget

## Persistence

## Observability

## Security

## Evaluation

## Findings

### HIGH

### MEDIUM

### LOW

## Required Changes

## Optional Improvements

## Next
```

---

# APPENDIX H. AGENT DESIGN CHECKLIST

## Problem

- [ ] Agent가 정말 필요한가?
- [ ] 일반 함수/Workflow로 충분하지 않은가?

## State

- [ ] State가 최소화되었는가?
- [ ] Node별 mutation owner가 있는가?

## Graph

- [ ] Node 책임이 분리되었는가?
- [ ] 무한 Loop 가능성이 없는가?
- [ ] 종료 상태가 명확한가?

## Tools

- [ ] Side Effect가 표시되었는가?
- [ ] Risk가 분류되었는가?
- [ ] Idempotency가 정의되었는가?
- [ ] Approval Policy가 있는가?

## Resources

- [ ] Trust Level이 있는가?
- [ ] RAG Source가 검증되는가?
- [ ] Prompt Injection을 고려했는가?

## Verification

- [ ] Execution 검증
- [ ] Reasoning 검증
- [ ] Policy 검증

## Persistence

- [ ] 어디서 checkpoint 하는가?
- [ ] Crash 복구가 가능한가?
- [ ] 중복 Tool 실행을 막는가?

## Operations

- [ ] Trace가 남는가?
- [ ] 비용 제한이 있는가?
- [ ] Failure Test가 있는가?
- [ ] Human Escalation이 가능한가?

---

# APPENDIX I. 가장 중요한 사고 순서

Agent 구현을 시작하기 전에:

```text
1. 이 문제에 Agent가 필요한가?

2. Agent의 State는 무엇인가?

3. 어떤 Node가 필요한가?

4. Node 사이 Edge는 무엇인가?

5. 어떤 Tool이 필요한가?

6. Tool의 Side Effect는 무엇인가?

7. 어떤 Resource가 필요한가?

8. 무엇을 Verify할 것인가?

9. 실패하면 어디로 가는가?

10. 언제 Human을 부를 것인가?

11. 어디서 Checkpoint할 것인가?

12. 어떻게 관찰하고 평가할 것인가?
```

이 질문에 답한 뒤 구현을 시작한다.

---

# FINAL PRINCIPLE

```text
AI가 많이 생각하게 하는 것이
좋은 Agent Architecture가 아니다.

AI가 무엇을 생각하고,
무엇을 실행할 수 있고,
무엇을 기억하고,
어디서 멈추고,
무엇으로 검증받아야 하는지를

명확히 설계하는 것이
좋은 Agent Architecture다.
```
