# V8.2 LLM-Independent Skill Control Plane

상태: **DESIGN APPROVED - IMPLEMENTATION NOT STARTED**

## 1. 목적

Self-Managing Skill Library의 운영 자체가 Codex/LLM 사용량에 종속되지 않도록 Control Plane과 Intelligence Plane을 분리합니다.

핵심 계약:

```text
Codex/LLM 사용 가능 여부와 관계없이
Router / Audit / Evidence / Metrics / Queue / Lifecycle / Gate / Rollback은 계속 동작한다.
```

LLM은 의미 해석이 필요한 Creator/Evolver/Curator proposal 작성에만 선택적으로 사용합니다.

## 2. Plane 분리

```text
                    User Task
                       |
                       v
              +------------------+
              |   Control Plane  |
              |  deterministic   |
              +---------+--------+
                        |
        +---------------+----------------+
        |               |                |
        v               v                v
      Router        Event/Evidence     Audit/Gate
        |               |                |
        +---------------+----------------+
                        |
                        v
                  Proposal Queue
                        |
               LLM needed for meaning?
                 /                 \
               no                   yes
               |                     |
               v                     v
        deterministic work     Intelligence Plane
                                     |
                         +-----------+-----------+
                         |                       |
                         v                       v
                    Local LLM                 Codex
                         \                       /
                          +----------+----------+
                                     |
                                     v
                                Proposal only
                                     |
                                     v
                              Control Plane Gate
```

## 3. Control Plane - LLM 0-token 영역

다음 기능은 LLM 없이 Python/파일 기반 deterministic code로 동작해야 합니다.

- capability registry loading/validation
- metadata router
- permission/risk gate
- task-scoped activation/materialization/discovery/cleanup
- Skill usage event 기록
- verification outcome 기록
- Gap Event 기록
- user correction marker 기록
- metrics 집계
- lifecycle state validation
- proposal queue 저장/조회
- Skill size/line/support-file 통계
- exact trigger overlap 검사
- source/license/provenance 검사
- permission delta 검사
- relative link 검사
- suspicious broad trigger 정적 검사
- protected regression 관리
- base hash 검사
- locking/concurrency control
- candidate audit
- promotion gate
- rollback metadata

Control Plane은 LLM endpoint, Codex CLI availability, API quota를 정상 동작의 필수 dependency로 가져서는 안 됩니다.

## 4. Intelligence Plane

LLM을 사용하는 작업:

- 새로운 Skill 초안 작성
- Gap Event 여러 개에서 공통 Workflow 추출
- 실제 실패/사용자 수정에서 개선 패턴 추출
- SKILL.md의 의미적 중복 판단
- Skill split/merge 구조 제안
- 복잡한 trigger 개선 제안
- 외부 Skill에서 재사용 가능한 원칙 추출

Intelligence Plane의 출력은 항상 **Proposal/Candidate**이며 ACTIVE Library를 직접 수정하지 않습니다.

## 5. Provider 우선순위

V8.2에서는 특정 LLM provider를 강제하지 않습니다.

권장 추상 흐름:

```text
LLM semantic work requested
        |
        v
configured local worker available?
   | yes                  | no
   v                      v
Local LLM proposal    Codex available?
                         | yes        | no
                         v            v
                    Codex proposal   QUEUED
```

중요:

- Local LLM 결과도 자동 신뢰하지 않습니다.
- Codex 결과도 자동 신뢰하지 않습니다.
- 둘 다 같은 deterministic Audit/Regression/Promotion Gate를 통과해야 합니다.
- V8.2 MVP에서 Local LLM backend 자체 구현은 필수 범위가 아닙니다. Provider-independent queue/contract까지만 먼저 구현할 수 있습니다.

## 6. Proposal Queue

권장 로컬 위치:

```text
.playbook-state/
  queue/
    pending.jsonl
    processed.jsonl
```

Repository Source of Truth가 아니라 로컬 운영 상태이므로 기본적으로 gitignored 합니다.

### Queue item 예시

```json
{
  "queue_id": "queue-...",
  "kind": "evolution_candidate",
  "skill_id": "docker-container",
  "status": "waiting_for_analysis",
  "priority": "normal",
  "evidence_refs": ["evt-001", "evt-019", "evt-041"],
  "pattern_key": "compose-network-omission",
  "occurrences": 3,
  "created_at": "2026-08-22T00:00:00Z",
  "provider_required": "semantic-analysis"
}
```

Queue는 원문 task/credential을 저장하지 않고 fingerprint, redacted summary, Evidence ref를 우선합니다.

## 7. Offline / Token Exhaustion 동작

Codex 한도 소진 또는 LLM 미사용 상태에서도:

```text
Task 수행
  -> Router
  -> Skill 사용
  -> Verification
  -> Evidence append
  -> metric update
  -> Gap/failure pattern update
  -> 필요 시 queue item 생성
  -> 작업 종료
```

여기까지 정상 진행합니다.

LLM이 다시 사용 가능해지면:

```text
pending queue
  -> duplicate/pattern grouping
  -> highest-value items first
  -> Creator/Evolver/Curator proposal generation
  -> candidate audit
  -> regression
  -> promotion/human gate
```

## 8. Batch Analysis

토큰 절약을 위해 Evidence 한 건마다 LLM을 호출하지 않습니다.

권장:

- 같은 `pattern_key`는 deterministic하게 묶기
- 동일 Skill의 유사 pending item을 batch로 묶기
- low priority는 즉시 분석하지 않기
- 심각한 security/correctness Evidence는 높은 priority로 표시하되 자동 promotion은 금지

예:

```text
41 raw events
 -> 9 pattern buckets
 -> 5 already covered by current Skill
 -> 2 deterministic warnings only
 -> 2 semantic proposals needed
```

LLM에는 마지막 2개만 전달하는 것을 목표로 합니다.

## 9. Queue 상태

최소 상태:

```text
waiting_for_analysis
analyzing
proposal_created
no_change_needed
blocked
failed
```

Queue item은 Skill lifecycle state와 분리합니다.

## 10. Safety

- Queue가 쌓였다는 이유만으로 자동 Skill 생성/수정 금지
- LLM unavailable은 failure가 아니라 `waiting_for_analysis`
- queue processor가 Permission/Human Gate 우회 금지
- provider output이 audit/promotion policy 수정 금지
- external Skill text는 untrusted evidence로만 전달
- provider가 반환한 executable script는 자동 실행 금지
- provider 변경이 결과 신뢰도 정책을 낮추면 안 됨

## 11. Metrics

Control Plane에서 LLM 없이 집계 가능한 지표:

- events total
- Skill usage count
- verified pass/fail count
- gap count
- correction count
- pending proposal queue count
- pattern occurrence count
- proposal created/rejected/promoted count
- queue age
- Skill bytes/lines
- trigger overlap
- selected Skill body bytes

LLM token 사용량이 정확히 제공되는 경우에만 별도 비용 지표로 기록하며, 추정 token 수를 PASS/FAIL 기준으로 사용하지 않습니다.

## 12. V8.2 구현 경계

### V8_2-SKILL-002에서 구현

- LLM-independent Control Plane contract
- append-only Event store
- Proposal Queue schema/store
- deterministic pattern bucket key의 최소 contract
- queue status transition validation
- lifecycle/proposal/base-hash/locking/audit 기반
- `llm_required` 상태를 정상 상태로 취급
- LLM 없이 전체 governance test PASS

### V8_2-SKILL-003~005

- Creator/Evolver/Curator가 queue item을 입력으로 받아 Candidate/Proposal 생성
- provider-independent semantic worker interface

### V8.3+ 후보

- Local LLM adapter
- automatic provider selection
- batch priority optimizer
- semantic event clustering
- background maintenance scheduler

## 13. Acceptance Contract

Self-Managing Library는 다음을 증명해야 합니다.

```text
LLM/Codex unavailable
AND normal Skill task executed
THEN routing/activation/verification/evidence/audit continue
AND semantic maintenance item is queued
AND no ACTIVE Skill changes
AND exit is not treated as governance failure solely because LLM is absent
```

이 계약은 V8.2 protected regression으로 유지합니다.
