# V8.2-SKILL-001 - High-Value Optional Skill Expansion Batch 1

상태: **COMPLETE - VERIFIED**

선행 조건:

- V8.1 CAP-001 ~ CAP-008 — COMPLETE - VERIFIED
- V8.1 installed launcher / arbitrary repository integration — COMPLETE - VERIFIED

## 목적

V8.1의 Dynamic Capability Library 구조를 유지하면서, 실제 소프트웨어 개발에서 반복적으로 가치가 큰 Optional Skill을 추가합니다.

핵심 원칙:

```text
Library는 확장
Global Context는 유지
Router는 metadata-first
Task마다 선택되는 Skill은 최소화
```

이번 Task는 전역 Core Skill을 늘리지 않습니다. 새 Skill은 모두 `capability-library/skills/optional/`에만 저장하며 현재 Task에서 Router가 선택했을 때만 session-scoped discovery bridge에 노출합니다.

## Batch 1 구현

추가된 Optional Skill:

1. `api-design` — REST/GraphQL/API contract 설계 및 review
2. `sql-optimization` — execution plan 기반 SQL 성능 진단
3. `docker-container` — Dockerfile/container build의 보안·재현성·크기·cache 검토
4. `dependency-upgrade` — package/framework upgrade의 breaking change와 rollback 관리
5. `performance-profiling` — measure/profile/before-after 기반 성능 개선
6. `resilient-error-handling` — timeout/retry/idempotency/failure classification 설계

V8.1 기존 Optional 4개와 합쳐 Skill registry 기준 Optional Skill은 10개입니다.

## Source / Adaptation

주요 외부 참고:

- `JayRHa/AgentSkills`
- License: MIT
- 참고 Skill: `api-designer`, `sql-optimizer`, `dockerfile-pro`, `dependency-upgrader`, `performance-profiler`, `error-handling-patterns`

적용 정책:

- 원문 wholesale copy 없음
- Claude 전용 command / attribution / hook 제거
- V8.1 Repository-first / Evidence / Human Gate 정책에 맞게 재작성
- source/license를 `sources.json`과 registry에 기록
- 원본의 bundled scripts/templates를 무조건 가져오지 않고 Skill 핵심 절차만 경량화

## Router Precision

새 Skill의 trigger를 좁게 설정했습니다.

- `api-design`: `api design`, `openapi`, `endpoint design` 등 설계 신호
- `sql-optimization`: `EXPLAIN ANALYZE`, `slow query`, `실행 계획` 등 query tuning 신호
- `docker-container`: `Dockerfile`, `multi-stage`, `build cache` 등 container build 신호
- `dependency-upgrade`: `Dependabot`, `major version`, `의존성 업그레이드` 등 package migration 신호
- `performance-profiling`: `p95`, `latency`, `benchmark`, `성능 프로파일링` 등 측정 신호
- `resilient-error-handling`: `retry`, `backoff`, `idempotency`, `timeout policy` 등 resilience 신호

일반 `error`/`오류`, 일반 `api`, 일반 `version`, 일반 `performance` 한 단어만으로 새 Skill이 과도 활성화되지 않도록 negative tests를 추가했습니다.

기존 핵심 regression도 유지하도록 test contract에 포함했습니다.

```text
JWT 인증 오류 + regression test
-> security-review + testing + root-cause-debugging
-> exact 3
-> STRICT
```

## Windows Verification Evidence

2026-08-22 실제 Windows Repository에서 다음을 확인했습니다.

```text
registry                  6/6 PASS
optional skill integrity   6/6 PASS
capability router         28/28 PASS
capability manager        12/12 PASS
skill materializer        10/10 PASS
discovery bridge          10/10 PASS
playbook launcher         12/12 PASS
installed launcher         2/2 PASS
Harness Audit             PASS / warnings 0
STRICT Quality Gate       PASS / ERRORLEVEL 0
git status --short        clean
```

Harness Audit에서 다음 기준도 확인했습니다.

```text
global AGENTS.md size: 4579 bytes
Core skill metadata: 7
Optional skill integrity: 10
capability sources: PASS
capability registry: PASS
MANIFEST coverage: PASS
```

검증 중 발견한 기존 Optional Skill 공통 계약 불일치 2건은 최소 수정 후 재검증했습니다.

- `root-cause-debugging`: `Stop / Handoff` 공통 섹션 형식으로 정규화
- `code-review`: `Stop / Handoff` 규칙 추가

## Acceptance Criteria

1. Optional Skill 6개 추가 — PASS
2. Registry / sources provenance valid — PASS
3. Optional Skill total 10개 — PASS
4. Core Skill 7개 변경 없음 — PASS
5. Global `.codex/AGENTS.md` 변경 없음 — PASS
6. 각 새 Skill에 Evidence / Stop-Handoff 규칙 포함 — PASS
7. Router positive cases — PASS
8. Router negative cases — PASS
9. 기존 JWT exact-3 regression — PASS
10. total selection <= 3 — PASS
11. Registry tests — PASS
12. Router tests — PASS
13. Optional Skill integrity tests — PASS
14. Activation/materializer/discovery/launcher regressions — PASS
15. Harness Audit — PASS
16. STRICT Quality Gate — PASS
17. final working tree clean — PASS

## 완료 후 순서

Batch 1은 **COMPLETE - VERIFIED**입니다. 다음 대량 Skill Batch를 바로 추가하지 않습니다.

```text
V8_2-SKILL-002  Skill Governance Foundation
V8_2-SKILL-003  Skill Creator
V8_2-SKILL-004  Skill Evolver
V8_2-SKILL-005  Skill Curator
V8_2-SKILL-006  Self-Managing Lifecycle Integration
```

이 관리 체계가 COMPLETE - VERIFIED 된 뒤 다음 대량 Optional Skill 흡수 Batch를 진행합니다.
