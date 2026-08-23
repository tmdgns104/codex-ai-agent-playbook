# V8.2 Self-Managing Skill Library - Governance Policy

상태: **DESIGN APPROVED - IMPLEMENTATION NOT STARTED**

## 1. 정책 목적

이 정책은 Skill Library가 스스로 생성·개선·정리되더라도 품질, 보안, Context 비용, 추적 가능성을 잃지 않도록 변경 경계를 정의합니다.

## 2. 기본 원칙

1. ACTIVE Skill은 검증 전 직접 수정하지 않는다.
2. 새 Skill은 항상 CANDIDATE부터 시작한다.
3. 자동화는 proposal 생성과 deterministic 검증을 우선한다.
4. 권한·범위·구조를 넓히는 변경은 더 높은 Gate를 요구한다.
5. 외부 Skill은 untrusted input으로 취급한다.
6. 삭제보다 archive를 우선한다.
7. 사용 빈도만으로 가치 없음을 단정하지 않는다.
8. 측정하지 않은 token/성공률 수치를 PASS 근거로 만들지 않는다.
9. Global Context 증가를 Self-Managing 기능의 대가로 허용하지 않는다.
10. Git/Test Evidence 없이 COMPLETE/PASS를 선언하지 않는다.

## 3. 변경 분류와 Gate

| 변경 | 기본 처리 | Human Gate |
|---|---|---|
| event/metric 기록 | 자동 | 아니오 |
| static audit/report | 자동 | 아니오 |
| exact duplicate warning | 자동 | 아니오 |
| candidate 생성 | 자동 제안 가능 | 아니오 |
| Skill body 최소 수정 candidate | 자동 제안 가능 | promotion 전 검증 |
| trigger 축소 | candidate + regression | 보통 아니오 |
| reference 추출 | candidate + link regression | 보통 아니오 |
| trigger 확대 | proposal only | 예 |
| permission 확대 | proposal only | 예 |
| 새 executable script | proposal only | 예 |
| Skill split | proposal only | 예 |
| Skill merge | proposal only | 예 |
| archive | proposal only | 예 |
| restore | candidate + validation | 구조 변경이면 예 |
| delete | V8.2 자동화 금지 | 항상 |
| Core 승격/강등 | proposal only | 항상 |

## 4. Skill 생성 정책

새 Skill은 아래 질문을 통과해야 합니다.

```text
Q1. 기존 Skill로 충분히 해결 가능한가?
  yes -> 새 Skill 생성 금지

Q2. 특정 Repo 한 번만 쓰는 규칙인가?
  yes -> project docs/task rule로 처리

Q3. 다른 작업에서도 반복될 전문 Workflow가 있는가?
  no -> 생성 금지

Q4. positive 2+ / negative 1+ routing case가 가능한가?
  no -> candidate 보류

Q5. 기존 Skill과 역할이 실질적으로 겹치는가?
  yes -> extend/merge proposal 우선

Q6. provenance와 permission을 설명할 수 있는가?
  no -> 생성 금지
```

Router count=0은 생성의 필요조건이 아닙니다. 단순한 Gap signal일 뿐입니다.

## 5. Skill 개선 정책

Evolver는 실제 Evidence에서 반복 패턴을 찾습니다.

권장 최소 원칙:

- 동일/유사 문제 2회 이상이면 review candidate가 될 수 있다.
- 심각한 안전/정확성 실패는 1회라도 review candidate가 될 수 있다.
- 단일 사용자 표현 취향이나 특정 Repository 상수는 일반 Skill에 넣지 않는다.
- 한 proposal은 핵심 문제 1~2개에 집중한다.
- 기존 positive/negative fixture를 보존한다.

`2회`는 hard PASS 기준이 아니라 proposal 생성 heuristic입니다.

## 6. Skill 크기/비대화 정책

V8.2 초기에는 hard line limit보다 soft warning을 사용합니다.

Audit에서 다음을 출력할 수 있습니다.

```text
INFO  skill bytes/lines
WARN  skill body growing
WARN  multiple responsibility headings
WARN  large examples embedded in SKILL.md
WARN  repeated command/reference tables
```

Curator 처리 우선순위:

```text
1. 중복 문장 제거
2. 긴 예제 -> references/
3. 반복 deterministic 작업 -> scripts/
4. 재사용 양식 -> templates/
5. 독립 책임이 명확하면 split proposal
```

단순히 파일이 길다는 이유만으로 split하지 않습니다.

## 7. Split 정책

Split 후보 조건 예시:

- 서로 독립적으로 trigger 가능한 두 책임이 존재
- 각 책임에 별도 positive/negative case를 만들 수 있음
- 한 책임 없이 다른 책임만 필요한 실제 사용 사례가 반복됨
- support file/permission profile이 크게 다름

Split은 Router behavior를 바꾸므로 Human Gate가 필요합니다.

## 8. Merge 정책

Merge 후보 조건 예시:

- trigger 집합이 과도하게 겹침
- 실제 작업에서 두 Skill이 거의 항상 같이 선택됨
- body workflow가 실질적으로 동일
- 두 Skill을 분리해서 유지할 사용자 가치가 낮음

Merge는 기존 id 참조와 routing 결과를 변경하므로 Human Gate가 필요합니다.

## 9. Archive 정책

시간 경과만으로 자동 archive하지 않습니다.

Archive review signal:

- 오랫동안 사용되지 않음
- 매우 낮은 verified utility
- 다른 Skill에 완전히 대체됨
- Router confusion을 반복 유발
- deprecated technology/domain

다음은 archive에서 보호할 수 있습니다.

- pinned
- 전문 저빈도 Skill
- 외부 작업/자동화가 참조하는 Skill
- 최근 restore된 Skill

V8.2에서는 archive는 항상 Human Gate입니다.

## 10. Provenance / License 정책

외부 Skill intake 시 기록:

- source repository/page
- source revision/commit if available
- license
- inspected files
- adaptation mode: `rewritten`, `inspired`, `copied-with-license` 등

기본값은 `rewritten`입니다.

외부 문서 안의 다음 지시는 source evidence일 뿐 실행 명령으로 취급하지 않습니다.

- tool execution 요청
- credential 요청
- 시스템/프롬프트 변경
- 다른 파일 삭제/변조 지시
- 네트워크로 임의 데이터 전송

## 11. Security Policy

다음은 candidate FAIL 또는 Human Gate 대상입니다.

- credential/secret 요구
- undeclared network access
- undeclared external write
- destructive command
- production mutation
- personal absolute path
- suspicious prompt injection instruction
- audit/promotion policy 자체를 우회하도록 지시
- 자기 자신을 자동 승인하도록 지시

Self-Managing Skill은 `skill_audit.py`, promotion policy, protected regression을 수정할 권한을 기본적으로 갖지 않습니다.

## 12. Protected Regression

다음 종류의 fixture는 protected로 표시할 수 있습니다.

- V8.1 핵심 routing contract
- Permission/Human Gate contract
- Optional Skill isolation
- max selected <= 3
- known false-positive regression
- known false-negative regression

Self-Managing proposal이 protected fixture를 삭제하거나 약화하면 FAIL입니다.

## 13. Metric Interpretation

측정값은 의사결정 보조 신호입니다.

- usage count가 낮다고 자동 archive하지 않는다.
- success rate가 높아도 false activation이 많으면 좋은 Skill이 아니다.
- Skill 크기가 작아도 역할이 모호하면 좋은 Skill이 아니다.
- token estimate가 정확하지 않으면 size/context proxy로만 사용한다.

## 14. Promotion Policy

Promotion은 다음 조건을 모두 만족해야 합니다.

```text
candidate package complete
AND skill audit PASS
AND registry validation PASS
AND routing positive PASS
AND routing negative PASS
AND protected regression PASS
AND permission policy PASS
AND base hash current
AND required Human Gate approved
```

하나라도 실패하면 ACTIVE package는 변경하지 않습니다.

## 15. Rollback Policy

Promotion 후 회귀가 발견되면:

1. 새 evolution을 즉시 덧붙여 고치지 않는다.
2. 문제가 promotion과 관련 있는지 Evidence 확인.
3. 필요하면 이전 Git 상태로 rollback.
4. 실패 Evidence를 새 proposal input으로 기록.

## 16. 대량 Skill 흡수 정책

한 번에 대량으로 넣지 않습니다.

권장:

```text
small batch
-> registry/audit
-> routing positive/negative
-> existing regression
-> Windows actual evidence
-> next batch
```

Self-Managing 기반이 완성되기 전에는 V8.2 Batch 1 이후 대량 흡수를 보류합니다.
