---
name: testing
description: 버그 재현, 신규 핵심 로직 검증, regression 확인처럼 focused test가 필요한 작업에서 사용합니다.
---

# Testing

테스트는 작업의 위험과 Repository 계약에 맞는 최소 충분 수준으로 선택합니다. 모든 작업에 TDD나 임의 coverage 목표를 강제하지 않습니다.

## 언제 사용

- 버그를 수정할 때
- 핵심 동작을 새로 추가할 때
- 회귀 가능성이 있는 리팩터링을 할 때
- acceptance criteria를 실행 Evidence로 증명해야 할 때

## 기본 흐름

### Bug

1. 가능하면 실패를 재현합니다.
2. 기존 테스트가 있으면 가장 좁은 관련 테스트부터 사용합니다.
3. 재현 테스트가 없고 비용이 합리적이면 focused reproducer를 추가합니다.
4. 수정 후 같은 경로가 GREEN인지 확인합니다.
5. 관련 회귀 범위를 필요한 만큼만 넓혀 확인합니다.

### New behavior

1. 요구사항에서 검증 가능한 guarantee를 뽑습니다.
2. 가장 싼 test level부터 선택합니다.
   - unit
   - integration
   - E2E
3. Repository가 가진 runner와 convention을 우선 사용합니다.
4. 실제 실행 결과만 PASS Evidence로 기록합니다.

## Coverage 정책

- Repository가 coverage threshold를 정의했다면 그 기준을 따릅니다.
- 별도 기준이 없다면 임의로 `80%` 같은 전역 숫자를 강제하지 않습니다.
- 숫자보다 변경된 핵심 동작과 실패 경로가 검증되는지를 우선합니다.

## 하지 말 것

- 테스트를 실행하지 않고 PASS라고 보고
- unrelated suite 전체를 무조건 실행
- 기존 실패를 현재 변경의 성공으로 오인
- mock이 실제 계약을 대체하도록 과도하게 사용
- 테스트를 통과시키기 위해 production behavior를 왜곡

## Evidence

최소 기록:

```text
command
exit code
관련 test 결과
검증된 guarantee
남은 gap
```

## Stop / Handoff

- 테스트 명령이 destructive/network/credential 작업을 포함하면 Policy Gate로 넘깁니다.
- 테스트 환경 자체가 깨져 재현 신뢰성이 없으면 root-cause-debugging과 함께 원인을 분리합니다.

## Source

ECC의 `tdd-workflow`에서 RED/GREEN/evidence 개념을 참고했지만, 모든 작업 TDD·80% coverage·Git checkpoint 강제를 제거하고 Repository 우선의 경량 testing Skill로 재작성했습니다.
