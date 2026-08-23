---
name: dependency-upgrade
description: npm/pip/cargo/Go/Maven 등 dependency 또는 framework version을 안전하게 올리고 breaking change와 rollback을 관리할 때 사용합니다.
---

# Dependency Upgrade

Dependency upgrade는 버전 숫자만 바꾸는 작업이 아니라 **baseline → release note/migration impact → 작은 upgrade → verification → rollback 가능 상태**를 유지하는 작업입니다.

## 언제 사용

- outdated package 업데이트
- major/minor framework migration
- Dependabot/Renovate 변경 검토
- CVE fix를 위한 package bump
- lockfile과 package manifest 업데이트

## 기본 흐름

1. working tree와 현재 baseline test 상태를 확인합니다.
2. package manager와 manifest/lockfile을 식별합니다.
3. direct/transitive dependency와 version jump를 분류합니다.
4. major/framework/build-tool 변경은 공식 release note와 migration guide를 먼저 확인합니다.
5. 가능하면 한 번에 하나의 high-risk upgrade만 적용합니다.
6. manifest와 lockfile을 같은 변경 단위로 유지합니다.
7. 관련 테스트/build/smoke verification을 실행합니다.
8. 실패 원인이 불명확하면 계속 누적하지 않고 해당 upgrade를 되돌릴 수 있는 상태를 유지합니다.
9. 마지막에 전체 관련 verification을 다시 실행합니다.

## 위험 판단

```text
patch < 일반 minor < breaking/deprecation minor < major/framework/build tool
```

`0.x` package처럼 semver 안정성이 낮은 경우 작은 version jump도 breaking change처럼 검토할 수 있습니다.

## 원칙

- 공식 changelog/migration guide가 일반 기억보다 우선
- 여러 major upgrade를 한꺼번에 섞지 않음
- lockfile의 대규모 churn 원인을 확인
- security advisory는 해결 version과 영향을 확인한 뒤 적용
- Repository verification command를 임의로 대체하지 않음
- commit/push/PR은 별도의 `github-ops` Gate를 따름

## 하지 말 것

- 모든 dependency를 무차별 latest로 올림
- test baseline이 이미 깨진 상태를 upgrade 실패로 오인
- migration guide 확인 없이 major bump
- upgrade 실패 후 broken tree를 누적
- package upgrade를 이유로 unrelated refactor까지 섞음

## Evidence

최소 기록:

```text
old -> new version
참고한 release/migration 정보
변경된 compatibility code/config
실행한 test/build command와 exit code
남은 blocker/deferred dependency
rollback 기준점
```

## Stop / Handoff

- official release 정보 확인에 network가 필요하면 Network Review 정책을 따릅니다.
- credential/private registry 접근은 자동 승인하지 않습니다.
- security advisory가 핵심이면 `security-review`를 함께 고려합니다.
- external commit/push/PR은 `github-ops` Human Gate 대상입니다.

## Source

MIT 라이선스 `JayRHa/AgentSkills`의 `dependency-upgrader`에서 baseline, changelog-first, isolated major upgrade, verification과 rollback 패턴을 참고했습니다. Claude 전용 attribution과 자동 commit 가정을 제거하고 V8.1 Gate/Repository 우선 정책에 맞게 재작성했습니다.
