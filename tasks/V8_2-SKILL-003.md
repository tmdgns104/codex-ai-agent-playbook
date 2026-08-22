# V8.2-SKILL-003 - Skill Creator

상태: **APPROVED - NOT STARTED**

선행 조건:

- V8_2-SKILL-002 COMPLETE - VERIFIED

## 목적

적절한 Skill이 없는 반복 가능한 전문 작업을 감지했을 때, ACTIVE Library를 직접 수정하지 않고 안전한 Skill Candidate를 생성합니다.

## 핵심 원칙

```text
no skill != create skill
```

Router miss는 먼저 Gap Event가 됩니다. Creator는 Gap을 재사용 가능한 Skill 후보로 만들 가치가 있을 때만 동작합니다.

## 구현 범위

### 1. Gap Event

권장 위치:

```text
harness/skills/events.py
harness/skills/gap_detector.py
```

기록 정보는 최소화합니다.

- task fingerprint
- redacted summary
- router result
- nearby skill ids
- domain hypothesis
- timestamp

credential, full prompt, personal secrets는 저장하지 않습니다.

### 2. Creator Eligibility

Candidate 생성 전 다음을 판정합니다.

- 기존 Skill로 충분한가?
- 기존 Skill minimal extension으로 해결 가능한가?
- 특정 Repository 일회성 규칙인가?
- 반복 가능한 workflow인가?
- positive 2+ / negative 1+ case가 가능한가?
- 기존 Skill과 중복되지 않는가?
- provenance/permission을 설명할 수 있는가?

### 3. Candidate Package

출력은 ACTIVE Library가 아니라 runtime candidate area입니다.

```text
.playbook-state/candidates/<proposal-id>/
  SKILL.md
  proposal.json
  routing.json
```

필요한 경우 references/scripts/templates는 candidate 안에만 생성합니다.

### 4. Candidate Content Contract

최소:

- frontmatter name/description
- purpose/scope
- when to use
- when not to use
- workflow
- Evidence
- Stop/Handoff
- Source/Provenance

### 5. Candidate Tests

Creator는 최소 다음 fixture를 함께 제안해야 합니다.

- positive 2개 이상
- negative 1개 이상

## 자동화 경계

Creator는 다음을 할 수 없습니다.

- ACTIVE registry에 직접 등록
- Core Skill 생성
- Human Gate를 우회
- permission 확대 자동 승인
- 외부 Skill script 자동 실행
- 외부 Skill wholesale copy

## 외부 Source Intake

V8.2 MVP에서는 자동 web crawling을 Creator의 기본 기능으로 넣지 않습니다.

외부 source를 사용할 때는 명시적으로 승인된 source content를 untrusted input으로 읽고 provenance를 기록합니다.

## 대표 테스트

### 생성해야 하는 예

```text
ROS2 publisher/subscriber QoS와 CAN-MQTT integration을 반복적으로 설계/진단
```

기존 Library에 충분한 Skill이 없고 workflow 재사용성이 있다면 candidate 생성 가능.

### 생성하면 안 되는 예

```text
README의 오타 한 줄 수정
foo.py 변수명을 x에서 y로 변경
현재 프로젝트 전용 파일명 규칙 한 번 적용
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
12. source/license 불명 candidate promotion 불가
13. existing protected routing regressions PASS
14. V8.1 activation regression PASS
15. Harness Audit PASS
16. STRICT Quality Gate PASS
17. final working tree clean

## 완료 조건

Windows actual Evidence 전 `COMPLETE - VERIFIED` 금지.
