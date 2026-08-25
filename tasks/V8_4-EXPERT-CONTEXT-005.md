# V8.4-EXPERT-CONTEXT-005 - Deterministic Selector and Budget Planner

상태: **COMPLETE**

## Problem

V8.4-001~004는 adapted context의 architecture boundary, transport contract, schema/validator, pinned-snapshot offline compiler를 확정했다. 현재 `kd-sympy`와 `kd-citation-management`의 compiler output은 안전하게 검증된 `DRAFT/APPROVAL_PENDING`이지만, task별로 승인·freshness·applicability·overlap·permission·quality·budget·cardinality를 순서대로 평가하고 whole knowledge unit만 선택하는 shadow-mode control plane은 없다.

## Requirements

1. Selector 입력은 exact task text, 기존 Router result, current activation plan, 별도 adapted catalog, candidate metadata, permission state, frozen budget policy다.
2. 기존 Router와 activation result는 읽기 전용이며 hash와 selected/profile/gate Evidence를 기록하고 어떤 field도 변경하지 않는다.
3. 후보 gate는 `approval`, `freshness`, `task_applicability`, `exclusion`, `overlap`, `permission`, `quality_evidence`, `budget`, `cardinality` 순서를 반드시 유지한다.
4. Candidate는 `kd-sympy`, `kd-citation-management` 두 개만 허용한다. Checked-in compiler output은 DRAFT이므로 실제 repository shadow selection에서는 자동 승인하거나 선택하지 않는다.
5. Domain, exact phrase trigger, prerequisite evidence, exclusion phrase만 deterministic match한다. Semantic/fuzzy/LLM matching은 금지한다.
6. Ranking은 specificity, lower planned context bytes, lower risk, stable ID의 lexicographic order다.
7. Required unit은 전부 whole-unit로 유지한다. Optional unit은 task tag exact match 때만 고려하고 budget 초과 시 stable reverse-priority order로 whole-unit 제외한다.
8. Required-only per-capability 또는 total byte budget 초과는 `BUDGET_BLOCKED`다. Raw snapshot fallback, unit truncate, summarization, token 추정은 금지한다.
9. Current/source/retained permission union과 기존 required gate 중 strongest gate를 계산한다. Unknown, missing, downgrade, 필요한 approval 부재는 PASS가 아니다.
10. 기본 cardinality는 1이다. 2개 선택은 explicit multi-domain phrase와 exact approved composition Evidence가 함께 있을 때만 허용한다.
11. Output은 task/input/output hash, Router reference, ordered gate Evidence, ranking breakdown, selected/excluded candidate와 unit, budget, permission, final decision을 가진다.
12. 동일 canonical input은 동일 output bytes/hash를 생성하며 runtime/backend/transport에는 연결하지 않는다.

## Architecture impact

- 새 코드는 `evaluation/external-skills/context-selector/` 아래의 isolated shadow-mode selector/budget planner와 tests뿐이다.
- V8.4-003 canonical serialization, definition schema, strongest permission gate를 import하여 재사용한다.
- V8.4-004 compiler output은 immutable input으로만 읽는다. Test-only approved copies는 메모리에서 만들며 runtime catalog나 compiler output으로 저장하지 않는다.
- ACTIVE registry, Router/scoring, activation, Skill Materializer, launcher/transport, AGENTS/global policy는 변경하지 않는다.
- Python 표준 라이브러리만 사용하며 LLM/Ollama/backend/benchmark/network/API/credential/hardware/cloud 실행이 없다.

## Deterministic data flow

```text
exact task + immutable Router/activation result
  + adapted catalog + candidate metadata + permission state + budget policy
  -> structural input validation
  -> ordered candidate gates 1..8
  -> deterministic rank
  -> cardinality gate 9
  -> combined whole-unit budget revalidation
  -> CURRENT_ONLY | NO_ACTION | HUMAN_GATE_REQUIRED |
     BUDGET_BLOCKED | ADAPTED_SELECTED
  -> canonical Evidence + self hash
```

Gate 실패 후 후속 gate는 `NOT_EVALUATED`로 남기며 PASS로 보간하지 않는다. Duplicate candidate, missing approval/quality/freshness data, invalid compiler definition은 fail closed다.

## Planned files

```text
evaluation/external-skills/context-selector/
  selector.py
  budget_planner.py
  policy/selector-budget-policy-v1.json
  tests/fixture_factory.py
  tests/test_selector.py
  tests/test_protected_artifacts.py
evaluation/external-skills/reports/v8.4-selector-budget-summary.json
tasks/V8_4-EXPERT-CONTEXT-005.md
```

## Protected baseline

- V8.4-001/002/003/004 task and report hashes are frozen before implementation.
- `context-contract/` 14-file aggregate: `98fc03d723cddfab69811e075bb98377eed3abcad11eeb961d64550b0fa62f4f`.
- `context-compiler/` 6-file aggregate: `5f20cd02868ea8c9fcf9e3ae8b54e4e8b04ede55213c586e87ea6183749f72a2`.
- `adapted-contexts/` 6-file aggregate: `b08b81615e246f4f5c5a3209596867d21b6a34dd6445efd6a331f3b31fb2282d`.
- V8.3 Evidence 40-file aggregate: `001ed39bc3d95c8506b8ca98ec9d9aa792389a5e1361622fa4a81c6ca07f06ab`.
- Existing Router, activation, Registry, benchmark/adoption, V8.3 prototype, and AGENTS hashes are frozen in the new protected-artifact test.

## Acceptance matrix

| Acceptance | Status |
|---|---|
| gate ordering deterministic | PASS |
| candidate ranking deterministic | PASS |
| unauthorized candidate never selected | PASS |
| Router result preserved | PASS |
| required units preserved | PASS |
| optional pruning deterministic | PASS |
| required overflow blocked | PASS |
| strongest permission enforced | PASS |
| tie-break deterministic | PASS |
| identical input/output deterministic | PASS |
| unknown/missing Evidence never passes | PASS |

## Verification plan

- New selector/budget A~P tests and protected hash tests.
- Frozen V8.4-003 context-contract tests.
- Frozen V8.4-004 compiler tests.
- Existing external-skill validation, activation normal path, Router/Registry regressions.
- New JSON validity, deterministic output hashes, `git diff --check`, change allowlist, final clean tree.

## Result

The selector and budget planner were implemented as isolated standard-library shadow-mode components. The main candidate flow deliberately remains linear so the required nine-gate order is visible in code and Evidence. The readability audit reported long sequential gate/planning functions; they were retained because splitting each gate across dispatcher abstractions would make the security order harder to audit. Names, early exits, immutable input hashes, and gate-local Evidence keep the flow explicit.

### Candidate selection Evidence

| Scenario | Authority | Decision | Selected | Units | UTF-8 bytes | Strongest gate |
|---|---|---|---|---:|---:|---|
| Repository 004 compiler outputs | actual DRAFT | `NO_ACTION` | none | 0 | 0 | `NONE` |
| SymPy exact solving | test-only APPROVED fixture | `ADAPTED_SELECTED` | `kd-sympy` | 4 required | 1,202 | `NETWORK_REVIEW` |
| Local citation normalization/consistency | test-only APPROVED fixture | `ADAPTED_SELECTED` | `kd-citation-management` | 4 required + 1 relevant optional | 1,670 | `HUMAN_GATE_REQUIRED` |
| Explicit approved two-domain composition | test-only APPROVED fixture | `ADAPTED_SELECTED` | both | 8 required | 2,562 | `HUMAN_GATE_REQUIRED` |

The checked-in DRAFTs were never rewritten or automatically approved. Test-only approval records are constructed in memory, bind the complete approved Definition hash, require fixture/holdout Evidence, and are not runtime authority.

### Budget and failure behavior

- Frozen hard limits are 4,096 total UTF-8 bytes and 2,048 bytes per capability.
- Exact assembled canonical bytes are always measured. Token count and tokenizer remain `null` with a non-empty reason; no estimate is recorded.
- Required units are selected before task-relevant optional units and never truncated or summarized.
- Optional units are pruned whole by highest numeric priority followed by stable capability/unit ID, with an explicit pruning sequence.
- Per-capability or total required-only overflow returns `BUDGET_BLOCKED` and selects no units.
- Raw snapshot fallback remains disabled.

### Verification

- New selector/budget/protection tests: 24 PASS, 0 FAIL.
- V8.4-003 context-contract tests: 21 PASS, 0 FAIL.
- V8.4-004 compiler tests: 20 PASS, 0 FAIL.
- Existing external-skill validation: 68 PASS, 0 FAIL.
- Existing activation normal path: 46 PASS, 0 FAIL.
- Existing Router/Registry: 40 PASS, 0 FAIL.
- Total final regression: 219 PASS, 0 FAIL.
- One initial focused run found two issues: a fixture expected a non-source trigger phrase, and malformed compiler output incorrectly degraded to `NO_ACTION`. The fixture was corrected and malformed input now returns `HUMAN_GATE_REQUIRED`.
- Compiler/selector processing performed zero runtime/backend/LLM/Ollama/benchmark/network/API/credential/hardware/cloud actions and installed no dependency. The explicitly requested final Git push is a separate control-plane completion action.
