# V8.2 Self-Managing Skill Library - Architecture

상태: **DESIGN APPROVED - IMPLEMENTATION NOT STARTED**

## 1. 아키텍처 목표

Self-Managing Skill Library는 기존 V8.1 Dynamic Capability Library 위에 관리 계층을 추가합니다.

핵심 구조:

```text
User Task
  |
  v
Deterministic Metadata Router
  |
  +--> suitable skill(s) found --> Permission Gate --> Task-scoped Activation --> Codex
  |                                                       |
  |                                                       v
  |                                                   Verification
  |                                                       |
  |                                                       v
  |                                                  Evidence Event
  |
  +--> no suitable skill --> Gap Event
                              |
                              v
                         Creator Proposal

Evidence / Gap / Routing Events
              |
              v
       Self-Managing Layer
       +------------------+
       | Skill Creator    |
       | Skill Evolver    |
       | Skill Curator    |
       +--------+---------+
                |
                v
          Change Proposal
                |
                v
        Deterministic Audit
                |
                v
        Regression Fixtures
                |
                v
        Promotion/Human Gate
                |
                v
        Capability Library
```

Self-Managing Layer는 기존 Router/Launcher의 critical path에 상시 LLM 비용을 추가하지 않습니다.

## 2. 구성요소

### 2.1 Event Recorder

책임:

- routing result 기록
- task verification outcome 기록
- gap event 기록
- user correction marker 기록
- skill usage 기록

권장 위치:

```text
harness/skills/events.py
```

MVP에서는 JSONL append-only 형식을 사용합니다.

```text
.playbook-state/
  events/
    skill-events.jsonl
```

Repository에 commit되는 장기 데이터가 아니라 로컬 운영 데이터입니다. 민감정보를 저장하지 않고 task text는 기본적으로 fingerprint/short redacted summary를 사용합니다.

### 2.2 Skill Governance Store

책임:

- lifecycle state
- current version/hash
- proposal state
- promotion history
- archive metadata

권장 구조:

```text
capability-library/
  registry.json
  sources.json
  governance/
    lifecycle.json
    policy.json
    proposals/
      <proposal-id>.json
```

실사용 telemetry는 capability-library에 넣지 않고 `.playbook-state/`에 둡니다.

### 2.3 Skill Audit

권장 위치:

```text
harness/quality/skill_audit.py
```

두 모드:

```text
library audit
candidate audit
```

Candidate audit는 ACTIVE Library를 수정하지 않고 별도 candidate package를 검사합니다.

정적 검사:

- schema
- path
- frontmatter
- provenance
- license
- permission
- trigger overlap
- size
- relative link
- executable resource declaration
- secret/personal path
- lifecycle/version
- fixture presence

### 2.4 Skill Creator

Creator는 Router가 Skill을 못 찾는 모든 경우 자동 호출되지 않습니다.

입력:

```text
GapEvent
current registry metadata
nearby capability metadata
optional source evidence
```

출력:

```text
SkillProposal(type=create)
Candidate package
Positive routing cases
Negative routing cases
```

Creator가 직접 registry ACTIVE entry를 쓰는 것은 금지합니다.

### 2.5 Skill Evolver

입력:

- ACTIVE Skill package snapshot
- observed evidence events
- failure/correction patterns
- existing routing fixtures

출력:

```text
SkillProposal(type=modify)
Candidate vN+1 package
expected improvement
regression cases
```

중요:

- ACTIVE vN은 그대로 유지
- Candidate vN+1만 변경
- 한 proposal에서 가장 큰 문제 1~2개만 수정
- unrelated cleanup 금지

### 2.6 Skill Curator

Library-level maintenance component.

제안 종류:

```text
compress
extract-reference
split
merge
trigger-narrow
trigger-expand
archive
restore
```

Curator는 deterministic report + 선택적 LLM analysis 조합으로 동작합니다.

예:

```text
skill_audit.py
  -> WARN size
  -> WARN trigger overlap
  -> WARN repeated content signature
        |
        v
Curator analyzes only warned candidates
        |
        v
proposal
```

Library 전체 본문을 매번 LLM에 넣지 않습니다.

### 2.7 Promotion Gate

권장 위치:

```text
harness/skills/promotion.py
```

Promotion 조건:

1. candidate audit PASS
2. registry validation PASS
3. positive routing PASS
4. negative routing PASS
5. protected regressions PASS
6. permission delta policy PASS
7. Human Gate 필요 시 승인
8. base hash가 현재 ACTIVE hash와 일치

모두 만족하면 atomic promotion.

### 2.8 Rollback

Git이 최종 Source of Truth입니다.

추가적으로 proposal metadata에 다음을 둡니다.

```text
base_hash
candidate_hash
promotion_commit
```

런타임에서 candidate promotion 실패 시 파일을 부분적으로 남기지 않아야 합니다.

## 3. 디렉터리 설계

V8.2 목표 구조:

```text
capability-library/
  registry.json
  sources.json
  governance/
    lifecycle.json
    policy.json
    proposals/
  skills/
    optional/
      <skill-id>/
        SKILL.md
        references/
        scripts/
        templates/
        tests/
          routing.json

harness/
  skills/
    events.py
    gap_detector.py
    proposal.py
    creator.py
    evolver.py
    curator.py
    promotion.py
    locking.py
  quality/
    skill_audit.py
  router/
    ... existing V8.1 router ...

.playbook-state/             # gitignored
  events/
    skill-events.jsonl
  locks/
  candidates/
    <proposal-id>/
  reports/
```

MVP 구현에서 불필요한 파일은 Task별로 단계적으로 추가합니다.

## 4. 데이터 모델

### 4.1 Lifecycle entry

```json
{
  "skill_id": "docker-container",
  "state": "active",
  "version": 1,
  "active_hash": "sha256:...",
  "pinned": false,
  "last_promoted_at": "2026-08-22T00:00:00Z"
}
```

### 4.2 Skill Event

```json
{
  "event_id": "evt-...",
  "event_type": "verified_usage",
  "skill_ids": ["docker-container"],
  "task_fingerprint": "sha256:...",
  "router_selected": ["docker-container"],
  "verification": "pass",
  "user_correction": false,
  "timestamp": "..."
}
```

### 4.3 Gap Event

```json
{
  "event_id": "gap-...",
  "event_type": "capability_gap",
  "task_fingerprint": "sha256:...",
  "task_summary": "ROS2 CAN-MQTT integration",
  "router_count": 0,
  "nearby_skill_ids": [],
  "candidate_domain": ["ros2", "robotics", "integration"],
  "timestamp": "..."
}
```

### 4.4 Proposal

```json
{
  "proposal_id": "prop-...",
  "change_type": "modify",
  "skill_id": "docker-container",
  "base_version": 1,
  "base_hash": "sha256:...",
  "proposed_version": 2,
  "reason": "Repeated compose-network omission",
  "evidence_refs": ["evt-1", "evt-7"],
  "trigger_delta": {"add": [], "remove": []},
  "permission_delta": {"add": [], "remove": []},
  "requires_human_gate": false,
  "status": "candidate"
}
```

## 5. Lifecycle State Machine

```text
                +------------+
                | CANDIDATE  |
                +-----+------+
                      |
                      v
                +------------+
                | VALIDATING |
                +--+------+--+
                   |      |
                 fail    pass
                   |      |
                   v      v
             +---------+ +--------+
             |REJECTED | | ACTIVE |
             +---------+ +---+----+
                              |
                    evidence/problem
                              |
                              v
                    +-----------------+
                    | REVIEW_REQUIRED |
                    +--------+--------+
                             |
                       proposal vN+1
                             |
                             v
                        VALIDATING

ACTIVE -> STALE -> ARCHIVED
ARCHIVED -> restore CANDIDATE -> VALIDATING -> ACTIVE
```

ACTIVE package는 validation 도중에도 불변입니다.

## 6. Creator Decision Flow

```text
router no/weak fit
      |
      v
record gap
      |
      v
can existing skill be safely extended?
  | yes                      | no
  v                          v
Evolver candidate       reusable workflow?
                           | no -> stop
                           | yes
                           v
                    enough distinct scope?
                           | no -> stop/merge
                           | yes
                           v
                    Creator candidate
```

V8.2 MVP에서는 자동 외부 web research를 Creator에 넣지 않습니다. 외부 근거가 필요하면 명시적 research/human-approved source intake 경로를 사용합니다.

## 7. Evolver Flow

```text
ACTIVE vN
  |
  +--> success events
  +--> failure events
  +--> user corrections
  +--> routing mistakes
        |
        v
pattern extraction
        |
        v
minimal proposal
        |
        v
candidate vN+1
        |
        v
clean audit context
        |
        v
regression
        |
      pass?
     /    \
   no      yes
 reject   promote
```

한 번의 작업 결과를 Skill 일반 규칙으로 과잉 일반화하지 않도록 evidence count와 pattern consistency를 기록합니다.

## 8. Curator Flow

```text
Deterministic library report
  |
  +-- size warning ------------> compress/extract-reference candidate
  +-- trigger overlap ---------> narrow/merge candidate
  +-- responsibility signals --> split candidate
  +-- stale evidence ----------> archive review candidate
  +-- broken package ----------> repair/block
                                  |
                                  v
                            Human Gate if structural
```

## 9. Risk Boundaries

다음 경계를 유지합니다.

### Auto-safe

- metrics/event append
- lifecycle report generation
- exact duplicate detection
- candidate static audit
- reference integrity scan
- proposal generation only

### Validation-required

- Skill body modification candidate
- trigger narrowing
- reference extraction
- new Skill candidate

### Human Gate

- permission expansion
- trigger expansion
- split/merge
- archive
- Core promotion/demotion
- executable external script introduction
- source/license ambiguity

## 10. Scaling Strategy

V8.2는 기존 deterministic Router를 보존합니다.

```text
Stage A: current
registry metadata scan + deterministic score

Stage B: measured need
precomputed domain/trigger inverted index

Stage C: larger library
metadata candidate retrieval -> deterministic rerank -> max 3

Stage D: only with evidence
semantic candidate retrieval -> deterministic policy rerank -> max 3
```

Semantic retrieval이 추가되어도 Permission Gate와 final deterministic constraints는 유지해야 합니다.

## 11. Context Budget

Self-Managing 구성요소는 normal task마다 모두 로드하지 않습니다.

```text
Normal Task
  -> Router metadata
  -> selected Skills only

Gap observed
  -> lightweight gap event only

Maintenance task
  -> Creator/Evolver/Curator loaded on demand
```

따라서 Library의 전체 Skill body 수가 증가해도 permanent context는 증가하지 않습니다.

## 12. 구현 순서

```text
V8_2-SKILL-001  Optional Skill Batch 1 (현재 Windows verification pending)
V8_2-SKILL-002  Governance Foundation + skill_audit.py
V8_2-SKILL-003  Skill Creator
V8_2-SKILL-004  Skill Evolver
V8_2-SKILL-005  Skill Curator
V8_2-SKILL-006  Lifecycle Integration + end-to-end evidence
```

대량 Skill 흡수 Batch 2는 SKILL-006 이후를 권장합니다.
