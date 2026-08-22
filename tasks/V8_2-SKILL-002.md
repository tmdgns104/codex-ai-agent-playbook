# V8.2-SKILL-002 - Skill Governance Foundation

상태: **APPROVED - NOT STARTED**

선행 조건:

- V8_2-SKILL-001 Windows verification COMPLETE - VERIFIED
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

추가 핵심 계약:

```text
Codex/LLM이 없거나 사용량이 소진되어도
Router / Evidence / Metrics / Queue / Lifecycle / Audit / Gate / Rollback은 계속 동작한다.
```

Semantic 판단이 필요한 작업은 실패 처리하지 않고 Proposal Queue에 `waiting_for_analysis` 상태로 보관합니다.

## 구현 범위

### 1. Lifecycle schema/store

최소 상태:

```text
candidate
validating
active
review_required
rejected
stale
archived
```

ACTIVE version은 immutable snapshot으로 취급합니다.

### 2. Proposal schema

최소 필드:

```text
proposal_id
change_type
skill_id
base_version
base_hash
proposed_version
reason
evidence_refs
trigger_delta
permission_delta
requires_human_gate
status
```

### 3. `skill_audit.py`

권장 위치:

```text
harness/quality/skill_audit.py
```

최소 검사:

- registry/path/frontmatter consistency
- source/license
- Optional isolation
- permission declaration
- SKILL.md size stats + soft warning
- relative link integrity
- exact trigger overlap report
- suspicious broad trigger warning
- personal path / obvious secret
- executable resources declaration
- lifecycle consistency
- routing fixture presence

CLI는 human-readable output과 JSON output을 지원합니다.

Exit contract 제안:

```text
0 PASS
1 FAIL
2 WARN-only (optional; 기존 harness convention과 충돌하면 문서화 후 조정)
```

기존 Quality Gate exit contract를 임의로 변경하지 않습니다.

### 4. Lock / base hash

동일 Skill concurrent write 방지.

- one writer per skill
- base hash mismatch rejection
- stale lock recovery test
- atomic write strategy

### 5. Protected regression marker

기존 routing regression을 proposal이 삭제/약화하지 못하도록 protected fixture 개념을 정의합니다.

특히 다음 Control Plane 계약도 protected regression 대상입니다.

```text
LLM unavailable
-> governance continues
-> semantic work queued
-> ACTIVE Skill unchanged
```

### 6. Append-only Event Store

권장 위치:

```text
harness/skills/events.py
.playbook-state/events/skill-events.jsonl
```

최소 event:

- verified usage
- verification failure
- capability gap
- user correction marker
- routing false-positive/false-negative marker

규칙:

- 전체 task text/credential을 장기 저장하지 않음
- fingerprint/redacted summary/Evidence ref 우선
- append-only
- malformed event rejection
- `.playbook-state/`는 gitignored local runtime state

### 7. Proposal Queue

권장 위치:

```text
harness/skills/queue.py
.playbook-state/queue/pending.jsonl
.playbook-state/queue/processed.jsonl
```

최소 상태:

```text
waiting_for_analysis
analyzing
proposal_created
no_change_needed
blocked
failed
```

Queue item은 LLM availability와 무관하게 생성/조회/상태 검증이 가능해야 합니다.

Codex/LLM이 없다는 이유만으로 `waiting_for_analysis` item을 governance FAIL로 취급하지 않습니다.

### 8. Deterministic Pattern Bucket Contract

MVP에서는 semantic clustering을 구현하지 않습니다.

대신 동일/유사 Evidence를 LLM 호출 전에 줄일 수 있도록 deterministic grouping key contract만 둡니다.

예:

```text
skill_id + event_type + normalized_issue_code
```

목적은 Evidence 한 건마다 LLM을 호출하지 않고 반복 패턴을 batch 분석할 수 있게 하는 것입니다.

### 9. Provider-independent Boundary

SKILL-002에서는 Codex/OpenAI/Ollama 같은 구체 provider adapter를 구현하지 않습니다.

다음 상태만 구분할 수 있으면 됩니다.

```text
semantic_analysis_not_needed
semantic_analysis_required
waiting_for_analysis
```

Creator/Evolver/Curator는 이후 Task에서 이 queue contract 위에 구현합니다.

Local LLM 또는 Codex의 결과는 모두 동일한 Audit/Regression/Promotion Gate를 통과해야 합니다.

## 금지 범위

- Skill Creator 구현
- Skill Evolver 구현
- Skill Curator LLM 구현
- Codex를 governance runtime의 필수 dependency로 만들기
- Local LLM adapter 구현
- automatic provider selection
- semantic/embedding retrieval
- 자동 archive
- automatic merge/split
- global AGENTS 확대
- permission model 변경

## 예상 파일

최소 후보:

```text
capability-library/governance/lifecycle.json
capability-library/governance/policy.json
harness/skills/events.py
harness/skills/queue.py
harness/skills/proposal.py
harness/skills/locking.py
harness/skills/promotion.py
harness/quality/skill_audit.py
harness/quality/test_skill_audit.py
harness/skills/test_governance.py
harness/skills/test_events.py
harness/skills/test_queue.py
evaluation/self-managing/protected-routing.json
```

실제 구현 과정에서 파일을 더 작게 합치는 것은 허용하지만 책임 경계는 유지합니다.

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
14. existing V8.1 router tests PASS
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

## 완료 조건

실제 Windows Evidence 확인 전 `COMPLETE - VERIFIED`로 표시하지 않습니다.
