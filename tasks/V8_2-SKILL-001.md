# V8.2-SKILL-001 - High-Value Optional Skill Expansion Batch 1

상태: **IMPLEMENTED - WINDOWS VERIFICATION PENDING**

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

## 변경 파일

```text
capability-library/registry.json
capability-library/sources.json
capability-library/skills/optional/api-design/SKILL.md
capability-library/skills/optional/sql-optimization/SKILL.md
capability-library/skills/optional/docker-container/SKILL.md
capability-library/skills/optional/dependency-upgrade/SKILL.md
capability-library/skills/optional/performance-profiling/SKILL.md
capability-library/skills/optional/resilient-error-handling/SKILL.md
harness/router/test_capability_router.py
harness/router/test_optional_skills.py
MANIFEST.txt
tasks/V8_2-SKILL-001.md
```

Global `.codex/AGENTS.md`와 Core `.agents/skills/`는 변경하지 않았습니다.

## Windows Verification 필요

먼저 focused tests:

```cmd
python harness\router\test_registry.py
python harness\router\test_optional_skills.py
python harness\router\test_capability_router.py
```

그 다음 V8.1 activation regression:

```cmd
python harness\activation\test_capability_manager.py
python harness\activation\test_skill_materializer.py
python harness\activation\test_discovery_bridge.py
python harness\activation\test_playbook_launch.py
python harness\activation\test_installed_launcher.py
```

마지막:

```cmd
python harness\security\harness_audit.py --root .
python harness\quality\quality_gate.py --repo . --profile strict --verify "python harness\security\harness_audit.py --root ."
echo %ERRORLEVEL%
git status --short
```

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
