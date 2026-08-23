---
name: api-design
description: REST/GraphQL endpoint, resource, versioning, pagination, error contract처럼 API surface 자체를 설계하거나 검토할 때 사용합니다.
---

# API Design

API 구현 전에 **공개 계약을 먼저 명확히 하고 breaking change를 줄이는** 절차입니다. 단순히 기존 외부 API를 호출하는 작업에는 사용하지 않습니다.

## 언제 사용

- 새 REST/GraphQL endpoint 또는 resource 설계
- OpenAPI/GraphQL schema 작성·검토
- pagination/versioning/idempotency/error contract 결정
- 공개 API 변경의 backward compatibility 검토
- endpoint naming과 HTTP semantics 정리

## 기본 흐름

1. Repository의 기존 API convention과 public contract를 먼저 확인합니다.
2. 사용자/consumer가 필요로 하는 resource와 operation을 정의합니다.
3. REST라면 method/status code/idempotency 의미를 맞춥니다.
4. list API는 pagination/filter/sort의 안정된 계약을 정합니다.
5. 오류 응답은 일관된 machine-readable shape를 사용합니다.
6. 인증/권한이 관련되면 `security-review`와 분리해 검토합니다.
7. 기존 contract를 깨는 변경이면 migration/versioning/deprecation 영향부터 보고합니다.
8. 가능하면 OpenAPI/SDL 또는 Repository가 사용하는 contract artifact로 남깁니다.
9. contract test 또는 기존 API verification을 실제 실행합니다.

## 설계 기준

- URL보다 resource와 consumer contract를 먼저 정의
- REST path는 일관된 noun 중심으로 유지
- 무제한 list response 금지
- public API breaking change는 명시적 근거 없이 진행하지 않음
- retry 가능한 write에는 idempotency 의미를 검토
- DB 내부 구조를 그대로 외부 contract로 노출하지 않음
- Repository 기존 naming/error/versioning 규칙이 일반론보다 우선

## 하지 말 것

- framework default를 API 설계 근거로 간주
- 기존 consumer 영향 확인 없이 field 삭제/rename/type 변경
- 모든 API에 임의로 `/v1`을 강제
- 단순 내부 함수 변경을 public API redesign으로 확대
- 인증/권한 설계를 이 Skill 하나로 PASS 처리

## Evidence

완료 시 최소한 다음을 남깁니다.

```text
검토한 existing contract/convention
변경된 API guarantee
breaking / non-breaking 판단
실행한 contract/test command와 exit code
남은 consumer/migration risk
```

## Stop / Handoff

- 공개 계약 변경이 요구사항/Architecture 범위를 넓히면 Human Gate로 넘깁니다.
- auth/authz boundary가 포함되면 `security-review`를 함께 고려합니다.
- 실제 외부 서비스 write가 필요하면 Capability Permission Gate를 우회하지 않습니다.

## Source

MIT 라이선스 `JayRHa/AgentSkills`의 `api-designer`에서 resource-first 설계, HTTP semantics, pagination, versioning, idempotency, contract-first 패턴을 참고했습니다. 원문 도구/템플릿 의존성을 제거하고 V8.1 Repository-first·Evidence 정책에 맞게 재작성했습니다.
