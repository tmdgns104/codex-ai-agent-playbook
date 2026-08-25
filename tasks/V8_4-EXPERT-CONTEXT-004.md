# V8.4-EXPERT-CONTEXT-004 - Pinned Snapshot Offline Compiler

상태: **COMPLETE**

## Problem

V8.4-001/002/003은 raw external Skill snapshot을 runtime authority로 사용하지 않고, 승인된 Adapted Capability Definition만 향후 별도 transport에서 사용할 수 있도록 경계를 확정했다. 현재는 pinned snapshot을 실행하지 않는 데이터로 읽어 deterministic knowledge units, provenance, permission delta, removal record, cache metadata를 가진 reviewable draft로 만드는 offline compiler가 없다.

## Requirements

1. Compiler 입력은 candidate ID, pinned snapshot path/revision/SHA-256/license, adaptation policy version, extractor version을 명시한다.
2. Source는 UTF-8 untrusted data로만 parsing하며 source instruction, install command, bundled/referenced script를 실행하지 않는다.
3. 초기 compile 대상은 현 `ADAPT_CANDIDATE`인 `kd-sympy`, `kd-citation-management` 두 개로 고정한다.
4. Deterministic transform rule은 source claim exact occurrence와 line locator를 검증하고 V8.4-003 knowledge-unit schema의 모든 field를 생성한다.
5. Correctness-critical procedure, prerequisite, verification, safety constraint, known failure mode는 required knowledge rule로 보존한다.
6. Provider governance, install/script, network/credential, destructive guidance, reference inventory, repeated examples, unrelated explanation은 runtime unit content에서 제거하고 provenance/removal Evidence에는 locator/hash/reason을 기록한다.
7. Permission은 source metadata/text에서 보수적으로 도출하고 retained/removed partition과 strongest source gate를 검증한다.
8. Definition은 frozen V8.4-003 schema를 변경하지 않고 `DRAFT`로 생성한다. Human review state는 별도 Evidence의 `APPROVAL_PENDING`으로 기록하며 자동 `APPROVED` 전환을 금지한다.
9. Schema, source/content/unit/cache hash, provenance, permission, forbidden instruction, required knowledge, safety classification, budget, deterministic rebuild를 fail closed로 검증한다.
10. Runtime adaptation, LLM/Ollama, benchmark, external access와 기존 runtime/Registry/Router/AGENTS 변경은 없다.

## Architecture impact

- `evaluation/external-skills/context-compiler/`에만 offline compiler, versioned policy/rules, tests를 추가한다.
- Compile output과 review Evidence는 기존 `adapted-contexts.json`과 분리된 `evaluation/external-skills/adapted-contexts/<candidate>/`에 기록한다.
- V8.4-003 schema/validator는 import하여 재사용하지만 수정하지 않는다.
- Compiler output은 DRAFT이므로 V8.4-003 runtime validator의 APPROVED hard gate를 통과할 수 없고 runtime authority가 아니다.
- ACTIVE registry, Router, activation, launcher, Materializer, Bridge와 context transport에는 연결하지 않는다.
- 새 dependency 없이 Python 표준 라이브러리와 `unittest`만 사용한다.

## Deterministic design

```text
explicit compiler input
  -> manifest/path/revision/license/SHA verification
  -> UTF-8 Markdown structure parsing as untrusted data
  -> deterministic source category inspection
  -> exact-source-claim transform rules
  -> canonical knowledge-unit IDs/content/hashes
  -> provenance/removal/permission/budget verification
  -> schema validation and identical second build
  -> DRAFT definition + APPROVAL_PENDING Evidence
```

- Unit ordering is an explicit strictly increasing priority contract. Duplicate or unstable rules fail instead of being silently reordered.
- Unit IDs are derived from candidate, rule ID, exact source claim hash, policy version, and extractor version.
- Definition `created_at_utc` is a fixed policy value, not wall-clock time.
- Cache key uses the frozen V8.4-003 function and therefore includes source hash, schema version, policy version, extractor version, validator version, permission policy version, unit hashes, draft status, verification Evidence, and tokenizer metadata.
- Actual compiler run timing is Evidence metadata only and is not part of deterministic definition/provenance content.

## Planned files

```text
evaluation/external-skills/context-compiler/
  compiler.py
  generate_outputs.py
  policy/offline-adaptation-policy-v1.json
  policy/transform-rules-v1.json
  tests/test_compiler.py
  tests/test_protected_artifacts.py
evaluation/external-skills/adapted-contexts/
  kd-sympy/{definition.json,provenance.json,compile-evidence.json}
  kd-citation-management/{definition.json,provenance.json,compile-evidence.json}
evaluation/external-skills/reports/v8.4-compiler-summary.json
tasks/V8_4-EXPERT-CONTEXT-004.md
```

## Protected baseline before implementation

- V8.4-001/002/003 task SHA-256: `bea3db0a...`, `fb4b1d47...`, `5d3cde64...`.
- V8.4 design/transport/schema-validator summary SHA-256: `6d29f8ae...`, `4fceb162...`, `1ee46ace...`.
- Frozen 14-file `context-contract/` aggregate: `98fc03d723cddfab69811e075bb98377eed3abcad11eeb961d64550b0fa62f4f`.
- V8.3 Stage-B Evidence 40-file aggregate: `001ed39bc3d95c8506b8ca98ec9d9aa792389a5e1361622fa4a81c6ca07f06ab`.
- Snapshot manifest SHA-256: `265a2ad0ed15d847eac43a46d6477389cba18ffd9044f983bb33c0d88c049135`.
- SymPy/Citation source SHA-256: `5445c2f5...`, `e52459a2...`, matching the pinned manifest.
- Existing benchmark/adoption/V8.3 adapted prototype and protected runtime/Registry/AGENTS hashes are frozen in the new protection regression test.

## Acceptance matrix

| Acceptance | Status |
|---|---|
| deterministic rebuild | PASS |
| schema validation | PASS |
| provenance completeness | PASS |
| permission consistency | PASS |
| forbidden instruction exclusion | PASS |
| required knowledge preservation | PASS |
| source hash verification | PASS |
| cache invalidation | PASS (`INVALIDATED`) |
| malformed input fail-closed | PASS |

## Verification plan

- New compiler unit/failure tests A-L.
- Frozen V8.4-003 context-contract tests.
- Existing external-skill validation tests.
- Existing activation/normal-path regression.
- Generated JSON parse and definition schema validation.
- Deterministic regeneration byte comparison.
- Protected hash regression, change allowlist, `git diff --check`, final clean status.
- Actual Codex backend, LLM, Ollama, benchmark, network/API/credential, hardware/cloud execution count remains zero.

## Result

The standard-library-only compiler was implemented as an isolated offline evaluation component. It accepts only the two explicitly allowlisted pinned snapshots, verifies manifest/path/revision/license/hash binding, parses the Markdown without executing it, maps exact unique claims through reviewed transform rules, and compiles twice before returning an artifact. Every successful Definition remains `DRAFT`; human review remains `APPROVAL_PENDING` in separate provenance Evidence.

### Compiled candidates

| Candidate | Units | Required | Definition bytes | Source permissions | Retained | Strongest gate | Cache key |
|---|---:|---:|---:|---|---|---|---|
| `kd-sympy` | 5 | 4 | 1,155 | local read/write, process, network | local read | `NETWORK_REVIEW` | `097a1c6fec7c0de6456f6b3260b8982ecbb7d4b5a2ccaf27cd5bb03af88049e3` |
| `kd-citation-management` | 5 | 4 | 1,192 | local read/write, process, network, credential | local read | `HUMAN_GATE_REQUIRED` | `a15c4c2c7d34747c7fe2c90922e6d5b95d37177dfc5ff44bed644ca0185f7ed3` |

The conservative source permission union is retained in Evidence even though operational permissions are removed from adapted unit content. This prevents a removed instruction from silently lowering the review gate.

### Verification result

- New compiler/fail-closed/protected tests: 20 PASS, 0 FAIL.
- Frozen V8.4-003 context-contract tests: 21 PASS, 0 FAIL.
- Existing external-skill validation tests: 68 PASS, 0 FAIL.
- Existing activation normal-path tests: 46 PASS, 0 FAIL.
- Existing Router/Registry tests: 40 PASS, 0 FAIL.
- Total final test evidence: 195 PASS, 0 FAIL.
- Both generated artifacts report 10/10 compile checks PASS and deterministic rebuild PASS.
- JSON parse/schema validation, protected hashes, change allowlist, `git diff --check`, commit/push, and final clean-tree Evidence are recorded in `v8.4-compiler-summary.json` after the final repository checks.
- One focused-test iteration initially exposed an incomplete `curl`/plain `API key` exclusion pattern and incorrectly transcribed protection-test paths/hashes. The policy/test fixture was corrected; no protected artifact changed.
- Actual Codex backend, runtime transport, LLM, Ollama, benchmark, external network/API/credential, hardware, cloud write, dependency install, and source script execution count: zero.
