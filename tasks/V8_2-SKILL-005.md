# V8.2-SKILL-005 - Skill Curator

상태: **APPROVED - NOT STARTED**

선행 조건:

- V8_2-SKILL-004 COMPLETE - VERIFIED

## 목적

Skill Library가 커질수록 발생하는 비대화, 책임 혼합, 중복, routing 충돌, 저가치 Skill 문제를 관리합니다.

Curator는 Library 전체를 무작정 LLM에 로드하지 않습니다.

```text
Deterministic Audit
-> WARN candidates only
-> Curator semantic analysis
-> Proposal
-> Governance/Human Gate
```

## 지원 Proposal Type

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

V8.2에서 `delete` 자동 proposal/promotion은 지원하지 않습니다.

## 1. Compress / Extract Reference

Skill body에 긴 예제, 명령어 표, 도메인별 상세 설명이 누적되면 다음 우선순위로 정리합니다.

```text
remove real duplication
-> move long examples to references/
-> move reusable deterministic work to scripts/
-> move forms to templates/
-> consider split only if responsibilities are independent
```

Support file 링크 무결성을 유지해야 합니다.

## 2. Split

Split proposal 조건 예:

- 독립적으로 trigger 가능한 복수 책임
- 각 책임별 positive/negative fixture 가능
- 실제 사용에서 한 책임만 필요한 사례가 반복됨
- permission/support resource 성격이 다름

Split은 자동 promotion 금지, Human Gate 필수.

## 3. Merge

Merge proposal 조건 예:

- trigger overlap 반복
- 거의 항상 함께 선택
- body workflow 실질 중복
- 별도 Skill 유지 가치 낮음

Merge 역시 Human Gate 필수.

## 4. Trigger Maintenance

### Narrow

false positive evidence에 따라 trigger를 좁히는 candidate 생성 가능.

### Expand

새 trigger 추가는 scope 확장이므로 Human Gate.

## 5. Archive

시간만으로 자동 archive하지 않습니다.

Archive review signal:

- low usage
- low verified utility
- replacement by another Skill
- persistent router confusion
- deprecated technology

다음은 보호할 수 있습니다.

- pinned
- specialist low-frequency skill
- externally referenced skill
- recently restored skill

Archive는 Human Gate 필수.

## 6. Deterministic Inputs

Curator가 사용할 report 예:

```text
skill size
support files
usage count
verified success/failure
last used
trigger overlap
routing false positive/negative
body duplication signature
broken references
proposal history
```

Semantic 판단이 필요 없는 값은 LLM에게 다시 계산시키지 않습니다.

## Acceptance Criteria

1. Curator receives only audit/report candidates, not whole library bodies by default
2. compress proposal works on synthetic oversized Skill
3. reference extraction preserves relative links
4. split candidate can be proposed but not auto-promoted
5. merge candidate can be proposed but not auto-promoted
6. trigger narrowing can be validated with regression
7. trigger expansion requires Human Gate
8. low usage alone does not auto archive
9. archive requires Human Gate
10. pinned/specialist protection represented
11. delete is not automatic V8.2 action
12. package resources remain intact during proposed restructure
13. protected routing regression PASS
14. V8.1 activation regression PASS
15. Skill Audit PASS
16. Harness Audit PASS
17. STRICT Quality Gate PASS
18. final working tree clean

## 완료 조건

Windows actual Evidence 전 `COMPLETE - VERIFIED` 금지.
