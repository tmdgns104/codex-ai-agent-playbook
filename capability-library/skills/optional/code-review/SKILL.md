---
name: code-review
description: diff 또는 리팩터링 결과에서 correctness, regression, contract 위반, 검증 누락을 focused review할 때 사용합니다.
---

# Code Review

리뷰는 바뀐 코드와 그 계약에 집중합니다. 단순 style 선호보다 실제 실패 가능성과 검증 누락을 우선합니다.

## Review 순서

1. 변경 목적과 acceptance criteria를 확인합니다.
2. diff를 먼저 읽고 영향 범위를 좁힙니다.
3. correctness와 regression 위험을 확인합니다.
4. public/API/data contract가 바뀌었는지 봅니다.
5. error handling과 boundary condition을 확인합니다.
6. 보안 영향이 있으면 `security-review`로 넘깁니다.
7. 테스트/검증 Evidence가 변경 위험에 충분한지 확인합니다.
8. style/readability는 기능 위험 이후에 다룹니다.

## Finding 우선순위

### High

- 잘못된 결과 또는 crash
- 데이터 손상
- auth/permission 우회
- public contract 깨짐
- 검증 없이 위험한 migration/change

### Medium

- 특정 edge case 실패
- regression 가능성
- resource leak
- error handling 누락
- 중요한 테스트 gap

### Low

- 유지보수성 저하
- 불필요한 복잡도
- 명확한 naming/readability 문제

취향 차이만 있는 style nit은 가능한 한 보고하지 않습니다.

## Finding 형식

```text
severity
파일/위치
문제
왜 실제 문제가 되는지
재현/근거
최소 수정 방향
```

실제 근거가 없는 speculative finding은 확정적으로 쓰지 않습니다.

## Review 범위 규칙

- 현재 diff 밖의 전체 architecture를 임의로 재설계하지 않습니다.
- 관련 없는 오래된 문제를 이번 변경의 blocker로 만들지 않습니다.
- 자동 생성 파일이나 dependency lockfile은 실제 의미 있는 문제가 있을 때만 지적합니다.

## Evidence

리뷰가 PASS라고 말하려면 최소한 diff와 관련 verification 결과를 실제로 확인해야 합니다. 테스트가 실행되지 않았다면 `not verified`라고 구분합니다.

## Source

ECC의 code-review command/rule 패턴을 참고해, always-on reviewer나 Claude 전용 workflow 없이 Codex Playbook의 focused diff review용 Skill로 재작성했습니다.
