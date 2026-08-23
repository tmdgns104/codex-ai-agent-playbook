---
name: refactoring
description: 기능 범위를 늘리지 않고 behavior-preserving change를 작은 단계로 rename, extract, move, simplify할 때 사용합니다.
---

# Refactoring

동작을 보존한다는 계약을 먼저 세우고 작은 변경과 focused regression을 반복해 구조를 개선합니다.

## When to use

- 큰 함수/모듈을 extract/move/simplify할 때
- rename과 dependency boundary 정리가 필요할 때
- 기능 추가 없이 유지보수성을 개선할 때
- before/after behavior를 비교할 Evidence가 있을 때

## Workflow

1. 현재 동작을 characterization test 또는 기존 regression으로 고정합니다.
2. 한 단계에서 하나의 구조 변화만 선택합니다.
3. rename/extract/move 후 가장 가까운 test를 즉시 실행합니다.
4. 중간 단계에서 feature scope를 섞지 않습니다.
5. 최종 diff가 같은 외부 behavior를 유지하는지 확인합니다.

## Boundaries

- 문제를 찾아 보고만 하는 작업은 `code-review` 영역입니다.
- 새 기능/요구사항 추가를 refactoring으로 숨기지 않습니다.
- test를 제거하거나 약화해 동작 보존을 주장하지 않습니다.

## Evidence

변경 전 보장, 각 단계의 focused test, 최종 regression과 의도적으로 바뀌지 않은 behavior를 기록합니다.

## Stop / Handoff

동작 보존을 증명할 수 없거나 요구사항 변경이 필요해지면 refactor를 멈추고 별도 feature/task로 분리합니다.

## Source / Provenance

- source_id: `v8.3-internal`
- license: `repository`
- provenance: V8.3 Candidate Review의 behavior-preserving 경계를 기반으로 새로 작성한 internal-original Skill입니다.
