---
name: root-cause-debugging
description: 오류, 실패, 성능 저하처럼 원인이 불명확한 문제에서 증상과 root cause를 Evidence로 분리할 때 사용합니다.
---

# Root Cause Debugging

증상을 바로 덮는 수정보다 재현 가능한 원인을 먼저 좁힙니다. 단순하고 원인이 명백한 수정에는 이 Skill을 쓰지 않아도 됩니다.

## 기본 흐름

1. **증상 고정**
   - 실제 오류 메시지, 실패 조건, 입력, 환경을 기록합니다.
2. **재현 최소화**
   - 가능한 가장 작은 재현 경로를 만듭니다.
3. **정상 기준 확보**
   - 기대 동작과 실제 동작의 차이를 명확히 합니다.
4. **가설 생성**
   - 동시에 많은 가설을 만들지 말고 Evidence로 판별 가능한 작은 가설부터 둡니다.
5. **한 변수씩 확인**
   - 로그, 테스트, diff, configuration, dependency, environment를 좁혀 봅니다.
6. **원인 수정**
   - 증상만 숨기는 workaround와 root cause fix를 구분합니다.
7. **재검증**
   - 최초 재현 경로가 사라졌는지 확인하고 필요한 regression만 실행합니다.

## Evidence 우선순위

- 실제 failing test / exit code
- stack trace / error message
- 최소 재현
- 최근 diff
- known-good와 failing 상태 비교
- config/environment 차이
- dependency/version 변화

추측만으로 원인을 확정하지 않습니다.

## 흔한 실패 패턴

- 첫 번째 의심 지점을 바로 수정
- 여러 파일을 동시에 바꿔 원인 추적 불가능
- 로그를 추가했지만 실제 failing path는 확인하지 않음
- workaround가 성공했다고 root cause가 해결됐다고 보고
- 환경 문제와 코드 문제를 섞음

## Stop / Handoff

- 재현 후 테스트가 필요하면 `testing`
- 보안 경계 문제면 `security-review`
- 수정 후 diff 독립 검토가 필요하면 `code-review`
- Repository 범위를 넘어 architecture 변경이나 권한 확대가 필요해지면 현재 Task에서 임의로 진행하지 않습니다.
