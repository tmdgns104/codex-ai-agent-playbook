# V8.2-SKILL-003 - Skill Creator

상태: **COMPLETE - VERIFIED**

선행 조건:

- V8_2-SKILL-002 — COMPLETE - VERIFIED

## 목적

적절한 Skill이 없는 반복 가능한 전문 작업을 감지했을 때, ACTIVE Library를 직접 수정하지 않고 안전한 runtime Skill Candidate를 생성합니다.

핵심 원칙:

```text
no skill != create skill
one router miss != create skill
Candidate != ACTIVE
```

## 구현 내용

### 1. Privacy-safe Gap Event

추가:

```text
harness/skills/gap_detector.py
```

Gap Event는 다음만 보존합니다.

- task fingerprint
- 160자 이하 redacted summary
- router result
- nearby skill ids
- domain hypothesis
- issue code / timestamp

raw task text, prompt, credential은 Event Store에 저장하지 않습니다.

### 2. Creator Eligibility

`harness/skills/creator.py`가 Candidate 생성 전 deterministic gate를 적용합니다.

생성하지 않는 경우:

- 기존 Router가 Skill/capability를 이미 선택
- nearby Skill이 있어 먼저 minimal extension 검토가 필요한 경우
- repository-specific one-off
- 재사용 가능한 workflow가 아님
- 서로 다른 task fingerprint 기반 matching Gap Event가 2건 미만
- positive routing case 2개 미만
- negative routing case 1개 미만

따라서 Router miss 한 번만으로 Skill을 생성할 수 없습니다.

### 3. Runtime Candidate Package

Candidate는 반드시 다음 경로 아래에만 생성합니다.

```text
.playbook-state/candidates/<proposal-id>/
```

생성 파일:

```text
SKILL.md
proposal.json
routing.json
```

`state_root` 자체도 `.playbook-state` 디렉터리여야 합니다. ACTIVE `capability-library/`와 `.agents/skills/`는 Creator가 수정하지 않습니다.

### 4. Candidate Content Contract

생성 SKILL.md 최소 구성:

- frontmatter name / description
- Purpose / Scope
- When to use
- When not to use
- Workflow
- Evidence
- Permissions
- Stop / Handoff
- Source / Provenance

Candidate status는 문서에도 ACTIVE가 아닌 runtime Candidate로 명시합니다.

### 5. Proposal / Human Gate

기존 SKILL-002 `proposal.py` contract를 그대로 사용합니다.

Create proposal:

```text
change_type = create
base_version = 0
proposed_version = 1
status = candidate
```

새 trigger는 trigger expansion이므로 Human Gate가 필요합니다. high-risk permission이 포함된 경우에도 Human Gate가 유지됩니다.

source/license/provenance는 Candidate 생성 전 명시되어야 하며 `unknown`, `unverified`, `unspecified` 값은 거부합니다.

### 6. Routing Fixture

각 Candidate는 함께 생성합니다.

```text
routing.json
  positive: 2+
  negative: 1+
```

대표 fixture는 ROS2 QoS + CAN-MQTT integration의 반복 workflow이고, README 오타 같은 단순 작업은 negative case입니다.

### 7. Candidate Skill Audit

기존 `harness/quality/skill_audit.py`를 확장했습니다.

```cmd
python harness\quality\skill_audit.py --candidate <candidate-directory>
```

Candidate audit 검사:

- SKILL.md / proposal.json / routing.json 존재
- proposal schema
- create change type
- source/license/provenance
- frontmatter
- Evidence / Stop-Handoff / Source-Provenance section
- positive 2+ / negative 1+
- relative links / personal path / obvious secret
- executable resource permission + Human Gate

기존 ACTIVE Library audit와 exit contract는 변경하지 않았습니다.

## 변경 파일

```text
harness/skills/gap_detector.py
harness/skills/creator.py
harness/skills/test_creator.py
harness/quality/skill_audit.py
MANIFEST.txt
tasks/V8_2-SKILL-003.md
```

Global `.codex/AGENTS.md`, ACTIVE registry, Router scoring, Optional Skill content는 변경하지 않았습니다.

## Windows Verification

실제 Windows Evidence:

```text
Skill Creator focused tests     13/13 PASS
Governance focused tests        12/12 PASS
Event Store tests                6/6 PASS
Proposal Queue tests             7/7 PASS
Skill Audit unit tests           6/6 PASS
Real skill_audit.py              WARN-only / no FAIL
Capability Router               28/28 PASS
Capability Manager              12/12 PASS
Skill Materializer              10/10 PASS
Discovery Bridge                10/10 PASS
Playbook Launcher               12/12 PASS
Installed Launcher               2/2 PASS
Harness Audit                   PASS / warnings 0
STRICT Quality Gate             PASS / ERRORLEVEL 0
Global AGENTS.md                 4579 bytes unchanged
working tree                    clean
```

`skill_audit.py --root .`의 WARN은 기존 trigger overlap / broad-trigger review 항목이며 FAIL은 없었습니다. 이 경고는 자동 수정/병합하지 않고 이후 Curator의 Evidence로 유지합니다.

## Acceptance Criteria

1. Router miss가 즉시 Skill 생성으로 이어지지 않음 — PASS
2. Gap Event가 privacy-safe 형태로 기록됨 — PASS
3. trivial task에서 Creator NO_ACTION — PASS
4. repository-specific one-off task에서 NO_ACTION — PASS
5. existing Skill sufficient case에서 new Skill 생성 안 함 — PASS
6. reusable domain gap에서 Candidate 생성 — PASS
7. Candidate는 ACTIVE Library 밖에 존재 — PASS
8. Candidate에 proposal/provenance/permission 포함 — PASS
9. positive 2+ / negative 1+ routing fixture 포함 — PASS
10. `skill_audit.py` candidate audit 실행 가능 — PASS
11. high-risk permission candidate는 Human Gate 표시 — PASS
12. source/license 불명 candidate 생성/promotion 경로 차단 — PASS
13. existing protected routing regressions PASS — PASS
14. V8.1/V8.2 activation regression PASS — PASS
15. Harness Audit PASS — PASS
16. STRICT Quality Gate PASS — PASS
17. final working tree clean — PASS
18. 동일 task fingerprint를 복제해 반복 Gap으로 가장할 수 없음 — PASS
19. Creator는 `.playbook-state` 외부 Candidate write를 거부 — PASS
20. Global `.codex/AGENTS.md` 증가 없음 — PASS

## 완료 조건

실제 Windows Evidence와 clean working tree가 확인되었습니다. `COMPLETE - VERIFIED`.
