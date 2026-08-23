---
name: api-client-integration
description: 외부 REST/HTTP API client의 auth, timeout, pagination, response schema drift와 test boundary를 구현할 때 사용합니다.
---

# API Client Integration

서버 API를 새로 설계하는 대신 이미 존재하는 외부 API를 애플리케이션에 안전하게 연결하는 client boundary에 집중합니다.

## When to use

- `httpx`/`requests` 같은 HTTP client integration
- auth header/token injection 경계
- timeout, pagination, rate/response 오류 처리
- 응답 schema drift와 mock/fake 기반 검증

## Workflow

1. 공식 계약과 실제 호출 boundary를 분리합니다.
2. auth/config를 call site에 흩뿌리지 않고 client boundary에 모읍니다.
3. timeout을 명시하고 retry가 필요하면 `resilient-error-handling` 계약을 따릅니다.
4. pagination과 response parsing을 재현 가능한 단위로 분리합니다.
5. network가 없어도 검증 가능한 fake/mock과 최소 통합 Evidence를 준비합니다.

## Boundaries

- 새 endpoint/public contract 설계는 `api-design` 영역입니다.
- 최신 공식 문서 조회 자체는 `documentation-lookup` 영역입니다.
- 무제한 retry나 credential 하드코딩을 추가하지 않습니다.

## Evidence

요청/응답 계약, timeout/pagination 조건, mock 또는 실제 통합 test 결과와 실패 경계를 기록합니다.

## Stop / Handoff

실제 credential 사용, production 호출, 외부 write 또는 비가역 API가 필요하면 명시적 Gate를 요구합니다.

## Source / Provenance

- source_id: `v8.3-internal`
- license: `repository`
- provenance: V8.3 Candidate Review 경계를 바탕으로 새로 작성한 internal-original Skill입니다.
