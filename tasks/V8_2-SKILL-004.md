# V8.2-SKILL-004 - Skill Evolver

상태: **COMPLETE - VERIFIED**

선행 조건:

- V8_2-SKILL-003 — COMPLETE - VERIFIED

## 목적

실제 작업 Evidence를 바탕으로 기존 ACTIVE Skill의 문제를 분석하고, ACTIVE version을 직접 수정하지 않은 채 개선 Candidate를 생성합니다.

## 핵심 계약

```text
ACTIVE vN stays immutable
Evidence -> Proposal -> Candidate vN+1 -> Audit -> Regression -> Promotion
```

## 구현 요약

`harness/skills/evolver.py`는 동일 Skill/problem bucket에서 서로 다른 task fingerprint 기반 반복 Evidence를 요구합니다. 일반 evolution은 2건 이상이어야 하며, 단일 severe safety/correctness signal은 자동 수정이 아니라 REVIEW만 생성합니다.

전체 SKILL.md 자유 재작성은 금지하고 exact replacement를 최대 2개, 변경 비율 0.35 이하로 제한합니다. Candidate는 `.playbook-state/candidates/<proposal-id>/`에만 생성하며 ACTIVE vN은 Candidate validation/promotion 전까지 immutable입니다.

Candidate proposal은 `change_type=modify`, `base_hash=ACTIVE vN package hash`, `base_version=vN`, `proposed_version=vN+1`, non-empty Evidence refs를 가집니다. source/license는 ACTIVE registry provenance와 일치해야 합니다.

기존 routing fixture는 보존하고 관측 문제용 positive/negative regression을 추가합니다. trigger/permission expansion은 Human Gate이며 registry delta가 있는 Candidate는 package-only promotion을 허용하지 않습니다.

low-risk Candidate promotion은 기존 Governance의 validation, protected regression, base hash, lock, Human Gate를 재사용합니다. 성공한 promotion은 `.playbook-state/history/promotion-history.jsonl`에 기록합니다. Candidate root의 `proposal.json`/`routing.json` governance metadata는 ACTIVE package로 복사하지 않습니다.

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

## Actual Windows Evidence

2026-08-23 실제 Windows Repository에서 확인:

```text
Skill Evolver focused tests     13/13 PASS
Skill Creator regression        13/13 PASS
Skill Audit unit tests           6/6 PASS
Governance focused tests        12/12 PASS
Event Store tests                6/6 PASS
Proposal Queue tests             7/7 PASS
Real skill_audit.py              WARN-only / no FAIL
Capability Router               28/28 PASS
Capability Manager              12/12 PASS
Skill Materializer              10/10 PASS
Discovery Bridge                10/10 PASS
Playbook Launcher               12/12 PASS
Installed Launcher               2/2 PASS
Harness Audit                   PASS / warnings 0
STRICT Quality Gate             PASS / ERRORLEVEL 0
Quality Gate changed/untracked   0
Global AGENTS.md                 4579 bytes unchanged
working tree                    clean
```

`skill_audit.py` WARN은 기존 trigger overlap / broad-trigger review signal이며 SKILL-004 신규 FAIL은 없습니다.

## Acceptance Criteria Result

1. ACTIVE content unchanged during evolution — PASS
2. evidence refs required for modify proposal — PASS
3. weak single observation does not force normal auto evolution — PASS
4. repeated evidence can create minimal proposal — PASS
5. candidate vN+1 base hash points to ACTIVE vN — PASS
6. unrelated rewrite bounded/rejected by policy — PASS
7. existing routing fixture preserved — PASS
8. new regression fixture generated — PASS
9. candidate audit path verified — PASS
10. protected regression preserved — PASS
11. permission expansion forces Human Gate — PASS
12. trigger expansion forces Human Gate — PASS
13. failed validation leaves ACTIVE vN unchanged — PASS
14. low-risk atomic promotion through Governance Gate — PASS
15. promotion history recorded — PASS
16. V8.1/V8.2 regressions — PASS
17. Harness Audit — PASS
18. STRICT Quality Gate — PASS
19. final working tree clean — PASS
20. duplicate fingerprint cannot inflate Evidence — PASS
21. severe single Evidence becomes REVIEW — PASS
22. ACTIVE provenance match required — PASS
23. Candidate governance metadata excluded from ACTIVE package — PASS
24. Global `.codex/AGENTS.md` unchanged — PASS

## 완료

**COMPLETE - VERIFIED**. 다음 Task는 `V8_2-SKILL-005` Skill Curator입니다.
