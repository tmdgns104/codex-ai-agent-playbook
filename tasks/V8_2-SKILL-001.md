# V8.2-SKILL-001 - High-Value Optional Skill Expansion Batch 1

상태: **APPROVED - IMPLEMENTATION IN PROGRESS**

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

## Batch 1

1. `api-design` — REST/GraphQL/API contract 설계 및 review
2. `sql-optimization` — execution plan 기반 SQL 성능 진단
3. `docker-container` — Dockerfile/container build의 보안·재현성·크기·cache 검토
4. `dependency-upgrade` — package/framework upgrade의 breaking change와 rollback 관리
5. `performance-profiling` — measure/profile/before-after 기반 성능 개선
6. `resilient-error-handling` — timeout/retry/idempotency/failure classification 설계

## Source / Adaptation

주요 외부 참고:

- `JayRHa/AgentSkills`
- License: MIT
- 참고 Skill: `api-designer`, `sql-optimizer`, `dockerfile-pro`, `dependency-upgrader`, `performance-profiler`, `error-handling-patterns`

정책:

- 원문 wholesale copy 금지
- Claude 전용 command / attribution / hook 제거
- V8.1 Repository-first / Evidence / Human Gate 정책에 맞게 재작성
- source/license를 `sources.json`과 registry에 기록

## Router Precision 제약

새 Skill은 기존 `security-review`, `testing`, `root-cause-debugging`, `code-review`를 밀어내지 않아야 합니다.

특히 다음 기존 regression은 유지해야 합니다.

```text
JWT 인증 오류 + regression test
-> security-review + testing + root-cause-debugging
-> exact 3
-> STRICT
```

새 Skill의 trigger는 가능한 좁고 domain-specific하게 구성합니다.

예:

- 일반 `error`/`오류`만으로 resilient-error-handling 활성화 금지
- 일반 `api` 한 단어만으로 api-design을 과도 활성화하지 않음
- 일반 `slow`만으로 SQL optimizer가 활성화되지 않음

## Acceptance Criteria

1. Optional Skill 6개 추가
2. Registry / sources provenance valid
3. Optional Skill total 10개
4. Core Skill 7개 변경 없음
5. Global `.codex/AGENTS.md` 변경 없음
6. 각 새 Skill에 Evidence / Stop-Handoff 규칙 포함
7. Router가 각 새 Skill의 명확한 positive case를 선택
8. 각 새 Skill의 대표 negative case에서 false activation 없음
9. 기존 JWT exact-3 regression 유지
10. total selection <= 3 유지
11. Registry tests PASS
12. Router tests PASS
13. Optional Skill integrity tests PASS
14. Activation/materializer/discovery/launcher regression PASS
15. Harness Audit PASS
16. STRICT Quality Gate PASS
17. final working tree clean

## 완료 후

Batch 1 Windows Evidence가 모두 PASS한 뒤 다음 Skill 묶음을 추가합니다. 여러 Batch를 한 번에 섞지 않습니다.
