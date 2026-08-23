---
name: ci-cd-workflow
description: GitHub Actions 등 CI/CD workflow의 build/test graph, cache, artifact, secret masking, branch/deploy gate를 설계할 때 사용합니다.
---

# CI/CD Workflow

CI graph를 작게 유지하면서 build/test/artifact와 배포 Gate를 명확히 분리합니다. Git 조작 자체보다 workflow 계약에 집중합니다.

## When to use

- GitHub Actions 또는 CI pipeline 작성·수정
- cache key와 artifact 전달 경로 정리
- branch/PR 조건과 least-privilege permission 정리
- secret masking과 deploy gate 추가

## Workflow

1. trigger와 job dependency graph를 먼저 확인합니다.
2. build/test를 가장 이른 실패 지점에 배치합니다.
3. cache는 재현성을 깨지 않는 key와 invalidation 조건을 둡니다.
4. artifact와 secret의 생성·소비 범위를 최소화합니다.
5. deploy/release는 명시적 branch/environment/Human Gate 뒤에 둡니다.

## Boundaries

- local test 선택은 `testing` 영역입니다.
- commit/push/PR 조작은 `github-ops` 영역입니다.
- package publication/release 자동화는 이번 Batch 범위 밖입니다.

## Evidence

workflow validation, 관련 test/job 결과, permission/secret 범위와 deploy gate를 기록합니다.

## Stop / Handoff

production deploy, external publish, credential 변경처럼 외부 상태를 바꾸는 단계는 명시적 승인을 요구합니다.

## Source / Provenance

- source_id: `v8.3-internal`
- license: `repository`
- provenance: V8.3 Candidate Review에서 정의한 CI/CD 경계를 기반으로 새로 작성한 internal-original Skill입니다.
