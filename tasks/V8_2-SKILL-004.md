# V8.2-SKILL-004 - Skill Evolver

상태: **IMPLEMENTED - WINDOWS VERIFICATION PENDING**

선행 조건:

- V8_2-SKILL-003 — COMPLETE - VERIFIED

## 목적

실제 작업 Evidence를 바탕으로 기존 ACTIVE Skill의 문제를 분석하고, ACTIVE version을 직접 수정하지 않은 채 개선 Candidate를 생성합니다.

## 핵심 계약

```text
ACTIVE vN stays immutable
Evidence -> Proposal -> Candidate vN+1 -> Audit -> Regression -> Promotion
```

## 구현 내용

### 1. Repeated Evidence Gate

추가:

```text
harness/skills/evolver.py
```

일반 evolution은 동일 Skill/problem bucket에서 **서로 다른 task fingerprint 2건 이상**이 있어야 Candidate 생성이 가능합니다.

지원 Evidence:

- verification_failure
- user_correction
- routing_false_positive
- routing_false_negative

repeated workaround / missing workflow step은 위 Evidence의 `issue_code`로 grouping합니다.

단일 safety/correctness 심각 Evidence는 자동 evolution이 아니라 `REVIEW` signal만 생성합니다.

### 2. Bounded Minimal Change

전체 SKILL.md 자유 재작성 대신 exact replacement edit만 허용합니다.

Governance policy:

```text
evolution_min_distinct_evidence = 2
evolution_max_content_edits = 2
evolution_max_changed_fraction = 0.35
```

각 edit는 `old/new/reason`을 가져야 하며 `old`가 ACTIVE content에서 정확히 한 번만 일치해야 합니다.

따라서:

- unrelated whole-file rewrite
- 대규모 style cleanup
- Evidence와 무관한 재작성

을 deterministic하게 차단합니다.

### 3. Candidate vN+1

Candidate는 반드시:

```text
.playbook-state/candidates/<proposal-id>/
```

아래에 생성합니다.

ACTIVE package를 먼저 복사한 뒤 Candidate 안의 `SKILL.md`만 bounded edit로 변경합니다.

Proposal:

```text
change_type = modify
base_hash = ACTIVE vN package hash
base_version = vN
proposed_version = vN+1
evidence_refs = repeated verified evidence
```

source/license는 ACTIVE registry provenance와 일치해야 합니다.

### 4. Routing Regression Preservation

ACTIVE package에 기존 local routing fixture가 있으면 Candidate에 byte-for-byte 보존합니다.

새 관측 문제에 대해서는 Candidate root의 `routing.json`에 최소:

```text
positive 1+
negative 1+
```

regression을 추가합니다.

### 5. Candidate Audit

`harness/quality/skill_audit.py`를 확장했습니다.

Creator Candidate:

```text
change_type=create
positive 2+ / negative 1+
```

Evolver Candidate:

```text
change_type=modify
base_hash matches current ACTIVE
non-empty evidence_refs
observed_pattern / root_cause / expected_behavior required
positive 1+ / negative 1+
```

기존 Library Audit exit contract는 변경하지 않았습니다.

### 6. Human Gate

trigger 또는 permission 추가는 기존 `proposal.py` contract에 따라 `requires_human_gate=true`입니다.

Evolver는 registry delta를 package-only promotion에 몰래 적용하지 않습니다. trigger/permission delta가 있으면 Lifecycle Integration 단계 전까지 promotion을 차단합니다.

### 7. Safe Promotion / History

low-risk Candidate에서 registry delta가 없고 다음 조건이 모두 충족될 때만 기존 `promote_package()`를 사용합니다.

- Candidate audit/validation PASS
- protected regression PASS
- base hash 일치
- required Human Gate 승인
- same-skill writer lock 획득

Candidate root의 governance metadata:

```text
proposal.json
routing.json
```

는 ACTIVE package에 복사하지 않습니다. 단, Skill package 내부의 `tests/routing.json` 같은 기존 fixture는 보존합니다.

성공한 promotion은 local runtime history에 기록합니다.

```text
.playbook-state/history/promotion-history.jsonl
```

기록:

- proposal id
- skill id
- base/new hash
- base/promoted version
- evidence refs
- timestamp
- promoted status

## 변경 파일

```text
capability-library/governance/policy.json
harness/skills/evolver.py
harness/skills/test_evolver.py
harness/quality/skill_audit.py
MANIFEST.txt
tasks/V8_2-SKILL-004.md
```

Global `.codex/AGENTS.md`, ACTIVE registry, Router scoring, Optional Skill content는 변경하지 않았습니다.

## Windows Verification

먼저 SKILL-004 focused test:

```cmd
python harness\skills\test_evolver.py
```

그 다음 Creator/Governance/Audit regression:

```cmd
python harness\skills\test_creator.py
python harness\skills\test_governance.py
python harness\skills\test_events.py
python harness\skills\test_queue.py
python harness\quality\test_skill_audit.py
python harness\quality\skill_audit.py --root .
```

Router/Activation protected regression:

```cmd
python harness\router\test_capability_router.py
python harness\activation\test_capability_manager.py
python harness\activation\test_skill_materializer.py
python harness\activation\test_discovery_bridge.py
python harness\activation\test_playbook_launch.py
python harness\activation\test_installed_launcher.py
```

마지막:

```cmd
python harness\security\harness_audit.py --root .
python harness\quality\quality_gate.py --repo . --profile strict --verify "python harness\security\harness_audit.py --root ."
echo %ERRORLEVEL%
git status --short
```

## Acceptance Criteria

1. ACTIVE content is unchanged during evolution
2. evidence refs required for modify proposal
3. weak single observation does not force normal auto evolution
4. repeated evidence can create minimal proposal
5. candidate vN+1 base hash points to ACTIVE vN
6. unrelated rewrite is rejected/warned by policy
7. existing routing fixture preserved
8. new regression fixture generated for observed problem
9. candidate audit PASS required
10. protected regression PASS required
11. permission expansion forces Human Gate
12. trigger expansion forces Human Gate
13. failed validation leaves ACTIVE vN unchanged
14. successful low-risk candidate can be promoted atomically through Governance Gate
15. promotion history recorded
16. V8.1/V8.2 regressions PASS
17. Harness Audit PASS
18. STRICT Quality Gate PASS
19. final working tree clean
20. duplicate task fingerprint cannot inflate repeated Evidence count
21. severe single Evidence becomes REVIEW, not automatic evolution
22. ACTIVE registry provenance must match Candidate source/license
23. candidate governance metadata is not copied into ACTIVE package
24. Global `.codex/AGENTS.md` remains unchanged

## 완료 조건

구현은 완료했습니다. 실제 Windows Evidence 확인 전 `COMPLETE - VERIFIED`로 표시하지 않습니다.
