# V8.2-SKILL-004 - Skill Evolver

상태: **APPROVED - NOT STARTED**

선행 조건:

- V8_2-SKILL-003 COMPLETE - VERIFIED

## 목적

실제 작업 Evidence를 바탕으로 기존 ACTIVE Skill의 문제를 분석하고, ACTIVE version을 직접 수정하지 않은 채 개선 Candidate를 생성합니다.

## 핵심 계약

```text
ACTIVE vN stays immutable
Evidence -> Proposal -> Candidate vN+1 -> Audit -> Regression -> Promotion
```

## 입력 Evidence

최소 지원:

- verified success
- verified failure
- user correction marker
- repeated workaround
- routing false positive
- routing false negative
- missing workflow step

## Pattern Rule

일반 품질 문제는 유사 Evidence가 반복될 때 proposal을 만드는 것을 기본으로 합니다.

안전/정확성에 심각한 문제는 단일 Evidence도 review signal이 될 수 있습니다.

특정 Repository의 literal/path/variable을 일반 Skill 규칙으로 복사하지 않습니다.

## Minimal Change

한 evolution proposal은 핵심 문제 1~2개만 해결합니다.

금지:

- 전체 SKILL.md 무관한 재작성
- unrelated style cleanup
- permission 확대를 개선의 부수 효과로 포함
- protected fixture 삭제
- audit rule 변경으로 자기 candidate를 통과시킴

## Candidate Diff

Proposal은 최소 다음을 설명합니다.

```text
Observed pattern
Evidence refs
Root cause in Skill
Proposed minimal change
Expected behavior
Positive regression
Negative regression
Permission delta
Trigger delta
```

## Clean Validation

Evolver의 private analysis에 의존하지 않고 candidate package와 fixture만으로 audit/regression이 가능해야 합니다.

## Promotion

Promotion은 V8_2-SKILL-002 Governance Gate를 그대로 사용합니다.

Evolver 자체가 promotion을 결정하지 않습니다.

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
16. V8.1 regressions PASS
17. Harness Audit PASS
18. STRICT Quality Gate PASS
19. final working tree clean

## 완료 조건

실제 Windows Evidence 전 `COMPLETE - VERIFIED` 금지.
