# V8.2-SKILL-005 - Skill Curator

상태: **COMPLETE - VERIFIED**

선행 조건:

- V8_2-SKILL-004 — COMPLETE - VERIFIED

## 목적

Skill Library가 커질수록 발생하는 비대화, 책임 혼합, 중복, routing 충돌, 저가치 Skill 문제를 관리합니다.

Curator는 Library 전체 본문을 normal-task context에 적재하지 않습니다.

```text
Deterministic metadata report
-> WARN candidates only
-> selected semantic analysis
-> Proposal / runtime Candidate
-> Governance / Human Gate
```

## 구현 내용

### 1. Metadata-first Curator Report

추가:

```text
harness/skills/curator.py
```

`build_curator_report()`는 전체 Skill의 본문 대신 다음 metadata만 반환합니다.

- Skill id/path
- SKILL.md bytes
- support file count
- body signature hash
- duplicate-line ratio
- trigger count/overlap
- permission/source/license
- verified usage/success/failure
- routing false positive/negative
- correction count / last used
- pinned/specialist/external-reference/recently-restored protection
- deterministic warning codes

report contract:

```text
body_included = false
```

WARN 없는 Skill은 semantic Curator 후보에서 제외할 수 있습니다.

### 2. Compress Candidate

`compress`는 ACTIVE를 직접 수정하지 않습니다.

```text
ACTIVE package
-> .playbook-state/candidates/<proposal-id>/ copy
-> selected exact block compression
-> routing regression
```

operation은 exact old block이 한 번만 일치해야 하며 결과가 실제로 짧아져야 합니다. ACTIVE와 기존 assets/tests/resources는 그대로 유지됩니다.

### 3. Extract Reference Candidate

`extract-reference`는 선택된 긴 block을 Candidate의:

```text
references/*.md
```

로 이동하고 SKILL.md에는 relative Markdown link를 남깁니다. Candidate 밖으로 escape하는 path는 거부합니다.

### 4. Split / Merge

`split`, `merge`는 Proposal을 만들 수 있지만:

```text
requires_human_gate = true
auto_promote_allowed = false
```

입니다. Curator가 자동으로 ACTIVE 구조를 변경하지 않습니다.

### 5. Trigger Maintenance

`trigger-narrow`:

- 기존 trigger만 제거 가능
- positive 1+ / negative 1+ regression 필요
- scope expansion이 아니므로 별도 expansion Human Gate를 강제하지 않음

`trigger-expand`:

- 새 trigger만 추가 가능
- positive 1+ / negative 1+ regression 필요
- Human Gate 필수
- auto promotion 금지

### 6. Archive Protection

low usage/time만으로 archive하지 않습니다.

`archive_review()`는 다음 강한 signal 또는 복합 Evidence에서만 REVIEW를 냅니다.

- replacement exists
- deprecated technology
- persistent router confusion
- low usage + no verified success + verified failure

다음 protection이 있으면 archive review를 차단합니다.

- pinned
- specialist
- externally referenced
- recently restored

Archive proposal은 Human Gate 필수이며 protected Skill은 proposal 생성 자체를 거부합니다.

### 7. Delete Policy

V8.2 Curator 지원 action:

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

`delete`는 지원하지 않습니다. 기존 `delete_automation_allowed=false` 정책을 유지합니다.

## 변경 파일

```text
harness/skills/curator.py
harness/skills/test_curator.py
MANIFEST.txt
tasks/V8_2-SKILL-005.md
```

Global `.codex/AGENTS.md`, ACTIVE registry, Router scoring, Optional Skill content는 변경하지 않았습니다.

## Windows Verification Evidence

실제 Windows Repository에서 다음 Evidence를 확인했습니다.

```text
Skill Curator focused tests      12/12 PASS
Skill Evolver regression         13/13 PASS
Skill Creator regression         13/13 PASS
Governance focused tests         12/12 PASS
Event Store tests                 6/6 PASS
Proposal Queue tests              7/7 PASS
Skill Audit unit tests            6/6 PASS
Real skill_audit.py              WARN-only / no FAIL
Capability Router                28/28 PASS
Capability Manager               12/12 PASS
Skill Materializer               10/10 PASS
Discovery Bridge                 10/10 PASS
Playbook Launcher                12/12 PASS
Installed Launcher                2/2 PASS
Harness Audit                    PASS / warnings 0
STRICT Quality Gate              PASS / ERRORLEVEL 0
Quality Gate changed/untracked    0
Global AGENTS.md                  4579 bytes unchanged
working tree                     clean
```

Real Skill Audit WARN은 기존 deterministic review signal이며 FAIL이 아닙니다.

```text
trigger-overlap: '재현' -> root-cause-debugging, testing
broad-trigger: testing -> test
broad-trigger: documentation-lookup -> api, latest, version
broad-trigger: github-ops -> git, pr
broad-trigger: root-cause-debugging -> bug, error
broad-trigger: code-review -> quality
```

이 WARN들은 Curator가 review candidate로 사용할 수 있으나 자동 merge/narrow/archive 근거로 단독 사용하지 않습니다.

## Acceptance Criteria

1. Curator receives metadata/audit candidates, not whole library bodies by default — VERIFIED
2. compress proposal/Candidate works on synthetic oversized Skill — VERIFIED
3. reference extraction preserves valid relative link — VERIFIED
4. split proposal exists but cannot auto-promote — VERIFIED
5. merge proposal exists but cannot auto-promote — VERIFIED
6. trigger narrowing requires positive/negative regression — VERIFIED
7. trigger expansion requires Human Gate — VERIFIED
8. low usage alone does not auto archive — VERIFIED
9. archive requires Human Gate — VERIFIED
10. pinned/specialist protection represented and enforced — VERIFIED
11. delete is not automatic/supported V8.2 action — VERIFIED
12. package resources remain intact during proposed restructure — VERIFIED
13. protected routing regression PASS — VERIFIED
14. V8.1/V8.2 activation regression PASS — VERIFIED
15. Skill Audit PASS/WARN-only with no FAIL — VERIFIED
16. Harness Audit PASS — VERIFIED
17. STRICT Quality Gate PASS — VERIFIED
18. final working tree clean — VERIFIED
19. Curator report does not expose raw Skill body text — VERIFIED
20. Candidate writes remain under `.playbook-state` — VERIFIED

## 완료 조건

**COMPLETE - VERIFIED**

실제 Windows Evidence와 Git clean 상태까지 확인했습니다.
