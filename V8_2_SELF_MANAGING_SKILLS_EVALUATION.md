# V8.2 Self-Managing Skill Library - Evaluation Plan

상태: **DESIGN APPROVED - IMPLEMENTATION NOT STARTED**

## 1. 평가 목적

Self-Managing 기능이 단순히 Skill 수만 늘리는 것이 아니라 실제로 다음을 개선하는지 검증합니다.

- 적절한 Skill 선택
- 불필요한 Skill 활성화 감소
- 실제 작업 성공/검증률
- Skill 개선 전후 품질
- Skill Library 구조 유지비용
- Context 비용 억제
- 안전한 permission/lifecycle 관리

## 2. 핵심 평가축

### A. Routing Quality

측정 후보:

- Top-1 match
- selected set precision
- selected set recall
- false positive
- false negative
- zero-capability correctness
- average selected count

V8.2에서는 임의의 절대 PASS 임계값을 먼저 고정하지 않고 baseline을 수집합니다.

### B. Utility

Skill 적용 전/후 같은 task fixture에서 다음을 비교할 수 있습니다.

- acceptance criteria pass
- verification exit code
- retry count
- user correction 필요 여부
- known failure 재발 여부

### C. Context / Cost

직접 token 수가 신뢰성 있게 제공되는 경우에만 token을 기록합니다.

그 외에는 다음 proxy를 사용합니다.

- selected Skill count
- selected SKILL.md total bytes
- loaded support file bytes
- permanent global context bytes
- router metadata bytes

중요 목표:

```text
Library size increases
while permanent global context stays effectively flat
```

### D. Maintainability

- Skill count
- candidate count
- rejected proposal count
- split/merge/archive proposal count
- overlap warning count
- broken reference count
- average SKILL.md size
- largest Skill size

### E. Safety

- permission expansion blocked
- malicious/external instruction blocked
- undeclared network/external write detected
- secret/personal path detected
- protected regression tamper detected
- stale base-hash promotion rejected

## 3. Fixture 구조

권장:

```text
capability-library/skills/optional/<skill>/tests/routing.json

evaluation/self-managing/
  protected-routing.json
  creator-cases.json
  evolver-cases.json
  curator-cases.json
  security-cases.json
```

Skill별 routing fixture 예:

```json
{
  "positive": [
    "EXPLAIN ANALYZE 결과로 느린 SQL 쿼리를 최적화"
  ],
  "negative": [
    "SQL 파일의 오타 한 줄 수정"
  ]
}
```

## 4. Protected V8.1 Regression

최소 다음 계약을 유지합니다.

```text
README 오타 한 줄 수정
-> zero capability allowed

JWT 인증 오류를 수정하고 regression test를 실행
-> security-review + testing + root-cause-debugging
-> exact 3
-> STRICT

GitHub push/PR external write
-> Human Gate

max selected
-> <= 3
```

## 5. Governance Foundation Tests

SKILL-002에서 검증:

- lifecycle valid transition
- invalid transition rejected
- proposal schema
- base hash mismatch rejected
- lock collision rejected
- stale lock handling
- candidate never overwrites active on failed validation
- skill audit PASS/WARN/FAIL contract
- malicious metadata rejection
- broken relative link detection
- trigger overlap warning
- permission delta detection

## 6. Creator Tests

### Positive

- 반복 가능한 전문 gap -> Candidate 생성
- candidate에 source/provenance/permission 포함
- positive/negative fixture 자동 생성 계약

### Negative

- README typo -> Skill 생성 안 함
- 특정 repo 변수명 변경 -> Skill 생성 안 함
- 기존 Skill로 충분 -> extend/evolver 경로
- provenance 불명 -> promotion blocked
- high-risk permission -> Human Gate

## 7. Evolver Tests

- 2개 이상의 유사 Evidence에서 minimal proposal 생성
- single weak observation에서 자동 변경하지 않음
- ACTIVE vN 불변
- vN+1 candidate만 변경
- existing fixture 유지
- protected regression 약화 시 FAIL
- improvement regression 실패 시 reject
- unrelated cleanup이 포함되면 warning/reject 가능

## 8. Curator Tests

### Compress

긴 embedded example을 reference로 옮긴 candidate가 link integrity를 유지하는지 확인.

### Split

독립 책임을 가진 synthetic Skill에서 split proposal은 만들되 자동 promotion하지 않는지 확인.

### Merge

높은 trigger/body overlap synthetic pair에서 merge proposal을 만들되 Human Gate를 요구하는지 확인.

### Archive

low-usage signal만으로 자동 archive하지 않는지 확인.

## 9. External Skill Security Tests

외부 Skill 샘플에 다음 문자열/패턴을 넣고 정책이 차단하는지 확인합니다.

- credential 요구
- system prompt 무시 지시
- arbitrary network upload
- destructive shell
- permission escalation
- personal absolute path
- audit bypass instruction

외부 Skill 원문은 자동 실행하지 않습니다.

## 10. Windows E2E 시나리오

### Scenario 1 - Existing Skill normal use

```cmd
python harness\activation\playbook_launch.py --root . --task "JWT 인증 오류를 수정하고 regression test를 실행" --dry-run
```

기존 V8.1 behavior 유지.

### Scenario 2 - Gap Event

Synthetic task에서 Router가 0개를 선택하고 gap event만 안전하게 기록하는지 확인.

### Scenario 3 - Creator Candidate

실제 ACTIVE Library를 수정하지 않은 채 `.playbook-state/candidates/<id>/`에 candidate가 만들어지는지 확인.

### Scenario 4 - Failed Promotion

negative routing fixture 실패를 유도하여 ACTIVE Skill hash가 바뀌지 않는지 확인.

### Scenario 5 - Successful Low-Risk Promotion

모든 Gate를 통과한 synthetic candidate가 atomic하게 promotion되고 registry/lifecycle이 일치하는지 확인.

### Scenario 6 - Human Gate

permission expansion proposal이 자동 promotion되지 않는지 확인.

### Scenario 7 - Cleanup

runtime/candidate temp state가 managed cleanup 규칙을 따르는지 확인.

## 11. 성능/확장 평가

Library 규모 synthetic metadata로 다음을 측정합니다.

```text
10 skills
50 skills
100 skills
500 skills
1000 skills
```

측정:

- routing wall time
- metadata parse time
- memory
- precision fixture behavior

V8.2에서 현재 deterministic scan이 충분하면 그대로 유지합니다.

새 retrieval/indexing 도입 조건은 실제 degradation Evidence입니다.

## 12. 완료 수락 기준

V8.2 Self-Managing MVP 완료 판단에는 최소 다음 Evidence가 필요합니다.

- focused unit tests PASS
- protected routing regression PASS
- V8.1 activation regression PASS
- Harness Audit PASS
- Skill Audit PASS
- STRICT Quality Gate PASS
- Human Gate scenario PASS
- failed promotion leaves ACTIVE unchanged
- Windows real repository E2E PASS
- final working tree clean

PASS는 실제 실행 Evidence가 있을 때만 기록합니다.
