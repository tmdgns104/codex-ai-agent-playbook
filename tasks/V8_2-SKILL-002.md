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

## 목적

Creator/Evolver/Curator보다 먼저 Skill 자기관리의 안전 경계를 구현합니다.

이 Task에서는 LLM 기반 Skill 생성/수정을 구현하지 않습니다.

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

## 금지 범위

- Skill Creator 구현
- Skill Evolver 구현
- Skill Curator LLM 구현
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
harness/skills/proposal.py
harness/skills/locking.py
harness/skills/promotion.py
harness/quality/skill_audit.py
harness/quality/test_skill_audit.py
harness/skills/test_governance.py
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

## 완료 조건

실제 Windows Evidence 확인 전 `COMPLETE - VERIFIED`로 표시하지 않습니다.
