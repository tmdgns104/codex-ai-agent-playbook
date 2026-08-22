# V8.2-SKILL-003 - Skill Creator

상태: **IMPLEMENTED - WINDOWS VERIFICATION PENDING**

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

먼저 SKILL-003 focused test:

```cmd
python harness\skills\test_creator.py
```

그 다음 Candidate Audit regression과 Control Plane regression:

```cmd
python harness\quality\test_skill_audit.py
python harness\skills\test_governance.py
python harness\skills\test_events.py
python harness\skills\test_queue.py
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

1. Router miss가 즉시 Skill 생성으로 이어지지 않음
2. Gap Event가 privacy-safe 형태로 기록됨
3. trivial task에서 Creator NO_ACTION
4. repository-specific one-off task에서 NO_ACTION
5. existing Skill sufficient case에서 new Skill 생성 안 함
6. reusable domain gap에서 Candidate 생성
7. Candidate는 ACTIVE Library 밖에 존재
8. Candidate에 proposal/provenance/permission 포함
9. positive 2+ / negative 1+ routing fixture 포함
10. `skill_audit.py` candidate audit 실행 가능
11. high-risk permission candidate는 Human Gate 표시
12. source/license 불명 candidate 생성/promotion 경로 차단
13. existing protected routing regressions PASS
14. V8.1/V8.2 activation regression PASS
15. Harness Audit PASS
16. STRICT Quality Gate PASS
17. final working tree clean
18. 동일 task fingerprint를 복제해 반복 Gap으로 가장할 수 없음
19. Creator는 `.playbook-state` 외부 Candidate write를 거부
20. Global `.codex/AGENTS.md` 증가 없음

## 완료 조건

구현은 완료했습니다. 실제 Windows Evidence 확인 전 `COMPLETE - VERIFIED`로 표시하지 않습니다.
