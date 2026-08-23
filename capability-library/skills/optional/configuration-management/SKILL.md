---
name: configuration-management
description: environment variable, config file, default/override precedence와 dev/test/prod 설정 경계를 정리할 때 사용합니다.
---

# Configuration Management

설정값이 어디에서 오고 어떤 순서로 override되는지 명시해 환경별 동작 차이와 secret 노출을 줄입니다.

## When to use

- environment variable와 config file 우선순위 정리
- default → file → environment → explicit override 규칙 정의
- dev/test/prod 설정 차이 정리
- secret 값이 문서·로그·샘플에 섞이는 문제 예방

## Workflow

1. 현재 config source와 override 순서를 목록화합니다.
2. 필수값, 안전한 default, 환경별 override를 분리합니다.
3. secret은 값이 아니라 이름/주입 경로만 코드와 문서에 남깁니다.
4. startup 시 잘못된 설정을 빠르게 검출하도록 합니다.
5. 최소 두 환경에서 같은 precedence contract를 확인합니다.

## Boundaries

- secret rotation, IAM, 인증 권한 검토는 `security-review` 영역입니다.
- 특정 Python package layout 문제를 이 Skill로 확장하지 않습니다.
- production secret 값을 Repository나 로그에 기록하지 않습니다.

## Evidence

설정 source, precedence, 필수/기본값 규칙, 환경별 확인 결과와 secret 비노출 여부를 기록합니다.

## Stop / Handoff

credential 접근, production secret 변경, 외부 secret store write가 필요하면 Human/Permission Gate로 넘깁니다.

## Source / Provenance

- source_id: `v8.3-internal`
- license: `repository`
- provenance: V8.3 Candidate Review 경계를 바탕으로 새로 작성한 cross-runtime internal-original Skill입니다.
