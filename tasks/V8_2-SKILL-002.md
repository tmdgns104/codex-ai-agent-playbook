# V8.2-SKILL-002 - Skill Governance Foundation

상태: **COMPLETE - VERIFIED**

선행 조건:

- V8_2-SKILL-001 — COMPLETE - VERIFIED
- V8.1 Dynamic Capability Library contracts preserved

참조:

- `V8_2_SELF_MANAGING_SKILLS_REQUIREMENTS.md`
- `V8_2_SELF_MANAGING_SKILLS_ARCHITECTURE.md`
- `V8_2_SELF_MANAGING_SKILLS_POLICY.md`
- `V8_2_SELF_MANAGING_SKILLS_EVALUATION.md`
- `V8_2_LLM_INDEPENDENT_CONTROL_PLANE.md`

## 목적

Creator/Evolver/Curator보다 먼저 Skill 자기관리의 안전 경계를 구현합니다.

이 Task에서는 LLM 기반 Skill 생성/수정을 구현하지 않습니다.

핵심 계약:

```text
Codex/LLM이 없거나 사용량이 소진되어도
Router / Evidence / Queue / Lifecycle / Audit / Gate / Rollback은 계속 동작한다.
```

Semantic 판단이 필요한 작업은 실패 처리하지 않고 Proposal Queue에 `waiting_for_analysis` 상태로 보관합니다.

## 구현 내용

### 1. Lifecycle

추가:

```text
capability-library/governance/lifecycle.json
harness/skills/lifecycle.py
```

상태:

```text
candidate
validating
active
review_required
rejected
stale
archived
```

잘못된 상태 전이는 deterministic code가 거부합니다. ACTIVE Skill은 validation 도중 immutable이라는 계약을 schema에서 유지합니다.

### 2. Proposal Contract

추가:

```text
harness/skills/proposal.py
```

검사:

- required proposal fields
- change/status enum
- base/proposed version
- base hash
- evidence refs
- trigger delta
- permission delta
- trigger/permission/structural expansion의 Human Gate 강제

### 3. Lock / Base Hash / Promotion

추가:

```text
harness/skills/locking.py
harness/skills/promotion.py
```

보장:

- one writer per Skill
- cross-platform exclusive lock file
- stale lock recovery
- base hash mismatch rejection
- validation 실패 시 ACTIVE package 변경 없음
- required Human Gate 미승인 시 promotion 금지
- staged package rename + rollback backup

### 4. Append-only Event Store

추가:

```text
harness/skills/events.py
.playbook-state/events/skill-events.jsonl
```

지원 event:

- verified_usage
- verification_failure
- capability_gap
- user_correction
- routing_false_positive
- routing_false_negative

전체 task text/raw prompt/credential 필드는 저장할 수 없습니다. task fingerprint와 짧은 redacted summary를 사용합니다.

반복 Evidence의 LLM 호출 전 grouping을 위해 다음 deterministic key를 지원합니다.

```text
sorted(skill_ids) + event_type + normalized_issue_code
```

### 5. Proposal Queue

추가:

```text
harness/skills/queue.py
.playbook-state/queue/pending.jsonl
.playbook-state/queue/processed.jsonl
```

상태:

```text
waiting_for_analysis
analyzing
proposal_created
no_change_needed
blocked
failed
```

Queue에는 Codex/OpenAI/Ollama adapter가 없습니다. Provider availability와 무관하게 생성/조회/상태 검증이 가능합니다.

### 6. Deterministic Skill Audit

추가:

```text
harness/quality/skill_audit.py
```

검사:

- capability registry/source/license validation 재사용
- lifecycle schema
- protected regression presence
- path/frontmatter/name/description consistency
- Optional Skill isolation
- SKILL.md byte statistics + soft warning
- relative link integrity
- personal path / obvious secret
- executable resource permission/declaration
- local 또는 centralized routing fixture signal
- exact trigger overlap report
- suspicious broad trigger review

기존 `quality_gate.py` exit contract는 변경하지 않습니다.

`skill_audit.py` 기본 exit:

```text
0 PASS 또는 WARN-only
1 FAIL
```

명시적 `--warn-exit-code` 사용 시 WARN-only는 exit 2입니다.

### 7. Protected Regression

추가:

```text
evaluation/self-managing/protected-routing.json
```

필수 보호 ID:

```text
jwt-exact-3
max-selected-3
llm-unavailable-control-plane
```

`policy.json`의 required ID를 fixture에서 제거하면 promotion/audit가 FAIL하도록 구현했습니다.

특히 LLM unavailable 계약은 test에서 실제로 다음을 확인합니다.

```text
semantic analysis required
+ llm unavailable
-> waiting_for_analysis
-> ACTIVE bytes unchanged
-> governance continues
```

### 8. Runtime State Isolation

`.gitignore`에 추가:

```text
.playbook-state/
```

실사용 Evidence/Queue/Lock은 Repository Source of Truth와 분리된 로컬 runtime state입니다.

## 변경 파일

```text
.gitignore
capability-library/governance/lifecycle.json
capability-library/governance/policy.json
evaluation/self-managing/protected-routing.json
harness/skills/lifecycle.py
harness/skills/proposal.py
harness/skills/locking.py
harness/skills/promotion.py
harness/skills/events.py
harness/skills/queue.py
harness/skills/test_governance.py
harness/skills/test_events.py
harness/skills/test_queue.py
harness/quality/skill_audit.py
harness/quality/test_skill_audit.py
MANIFEST.txt
tasks/V8_2-SKILL-002.md
```

Global `.codex/AGENTS.md`, existing Router scoring, permission model은 변경하지 않았습니다.

## Windows Verification Evidence

실제 Windows repository에서 확인한 Evidence:

```text
Governance focused tests       12/12 PASS
Event Store tests               6/6 PASS
Proposal Queue tests            7/7 PASS
Skill Audit tests               6/6 PASS
Real skill_audit.py             RESULT WARN / exit 0
Capability Router regression   28/28 PASS
Capability Manager             12/12 PASS
Skill Materializer             10/10 PASS
Discovery Bridge               10/10 PASS
Playbook Launcher              12/12 PASS
Installed Launcher              2/2 PASS
Harness Audit                  PASS / warnings 0
STRICT Quality Gate            PASS / ERRORLEVEL 0
Global AGENTS.md               4579 bytes
Working tree                   clean
```

`skill_audit.py`의 WARN은 실패가 아니라 관리 Evidence입니다. 실제 WARN은 기존 trigger overlap / broad-trigger review 후보였고 ACTIVE Skill을 자동 수정하지 않았습니다.

SKILL-002에서 Router/Registry/Optional Skill 파일은 변경하지 않았으므로 SKILL-001에서 이미 확인한 다음 Evidence도 계속 유효합니다.

```text
Registry tests                  6/6 PASS
Optional Skill integrity        6/6 PASS
```

## Acceptance Criteria

1. Lifecycle valid transitions deterministic test PASS
2. Invalid lifecycle transition rejected
3. Proposal schema validation PASS
4. base hash mismatch promotion rejected
5. same-skill concurrent lock collision rejected
6. stale lock handling tested
7. failed candidate validation leaves ACTIVE content unchanged
8. `skill_audit.py` PASS/WARN/FAIL classification works
9. source/license/path/frontmatter audit works
10. broken relative link detected
11. trigger overlap reported without auto merge
12. permission delta detected
13. protected regression cannot be silently removed
14. existing V8.1/V8.2 router tests PASS
15. existing activation/materializer/discovery/launcher tests PASS
16. Harness Audit PASS
17. STRICT Quality Gate PASS
18. Global `.codex/AGENTS.md` size not increased by this feature
19. final working tree clean
20. Event store works without any LLM/Codex dependency
21. Proposal Queue accepts `waiting_for_analysis` while LLM is unavailable
22. repeated Evidence can be grouped by deterministic pattern key without LLM
23. LLM unavailable does not modify ACTIVE Skill and does not fail governance solely for that reason
24. queue state transitions reject invalid transitions
25. no concrete LLM provider is required by governance tests
26. protected regression covers the LLM-unavailable Control Plane contract

모든 Acceptance Criteria를 실제 Windows Evidence로 충족했습니다.

## 완료

**V8_2-SKILL-002 = COMPLETE - VERIFIED**

다음 Task: `V8_2-SKILL-003 - Skill Creator`.
