# V8.3-SKILL-BENCH-004 - Expert Skill Benchmark and Adoption Decisions

상태: **APPROVED - READY TO IMPLEMENT**

선행:
- V8_3-SKILL-BENCH-003 COMPLETE - VERIFIED
- V8_3-SKILL-BENCH-003A COMPLETE - VERIFIED
- INSPECTED=62
- BENCHMARK_READY=52
- benchmark shortlist=15
- shortlist domain packs=15
- external ACTIVE import=0
- external_scripts_executed=0

## 목적

BENCH-003/003A에서 정적 inspection을 통과한 외부 Expert Skill 중 기존 15개 shortlist를 controlled benchmark한다.

목표는 외부 Skill을 많이 ACTIVE로 만드는 것이 아니라 다음 질문에 Evidence로 답하는 것이다.

```text
현재 Playbook보다 실제로 도움이 되는가
어떤 부분만 가져오는 것이 더 좋은가
Context / token burden은 얼마나 늘어나는가
dependency / permission / safety 부담은 감당 가능한가
기존 Skill과 중복되는가
ACTIVE promotion 후보로 보낼 가치가 있는가
```

이번 Task에서 허용되는 최종 결정은 다음 네 가지뿐이다.

```text
ADOPT_CANDIDATE
ADAPT_CANDIDATE
REFERENCE_ONLY
REJECTED
```

`PROMOTED` 및 ACTIVE registry 반영은 이 Task 범위 밖이다.

## 범위

### Benchmark Wave 1

입력 Candidate는 `evaluation/external-skills/benchmark-shortlist.json`의 기존 15개를 고정한다.

```text
kd-scientific-writing
kd-dask
kd-exploratory-data-analysis
kd-scikit-learn
kd-pytorch-lightning
kd-sympy
kd-citation-management
kd-scientific-slides
kd-docx
kd-pylabrobot
kd-pydicom
nv-aiq-deploy
nv-holoscan-setup
nv-dynamo-interconnect-check
nv-dynamo-troubleshoot
```

BENCH-004 진행 중 새 외부 Candidate discovery를 섞지 않는다.
새 ECC 실존 후보 등록은 별도 catalog-correction Task로 유지한다.

### 비교 Variant

각 실행 Benchmark는 동일한 fixture를 다음 Variant로 비교한다.

```text
baseline-no-optional
current-playbook
external-expert
adapted-playbook
```

정의:

#### baseline-no-optional
- 해당 Domain의 Optional Skill 없이 최소 공통 Playbook만 사용
- 외부 Candidate body 사용 금지

#### current-playbook
- 현재 V8.2/V8.3의 ACTIVE registry와 deterministic routing 결과를 기준으로 사용
- Registry/Router를 Benchmark를 위해 수정하지 않음

#### external-expert
- pinned revision에서 inspection된 외부 Candidate의 Skill body를 evaluation-only context로 사용
- bundled script/install/API command는 실행하지 않음
- 외부 governance/self-modification 지시는 무시

#### adapted-playbook
- 외부 Candidate에서 유용한 workflow만 평가용으로 정제한 context
- provider-specific governance, unsafe execution, unnecessary dependency, 중복 설명을 제거 가능
- evaluation artifact일 뿐 ACTIVE Skill이 아님

## Token 절감형 2단계 Benchmark

모든 Candidate에 비싼 실행 Benchmark를 강제하지 않는다.

### Stage A - Deterministic Pre-Benchmark

15개 전체에 대해 정적/결정론적 비교를 수행한다.

최소 측정:

- candidate/domain/source
- current capability overlap
- license/revision status
- dependency burden
- permission/network/auth burden
- bundled script presence
- loaded context bytes
- available tokenizer가 있을 때 token count
- tokenizer가 없으면 token count는 null + reason 기록
- duplicate/overlap risk
- Windows/Codex compatibility notes
- fixture applicability
- safety gate

Stage A에서 명확히 가치가 없거나 안전/호환성 Gate를 통과하지 못한 Candidate는 실행 Benchmark를 생략할 수 있다.
그 경우 `ADOPT_CANDIDATE` 또는 `ADAPT_CANDIDATE` 판정은 금지한다.

### Stage B - Controlled Execution Benchmark

Stage A를 통과하고 실제 채택 가능성이 있는 Candidate만 실행 비교한다.

실행되는 Candidate는 동일 fixture에서 네 Variant를 모두 비교해야 한다.

Benchmark runtime/model/provider를 코드에 하드코딩하지 않는다.
실행 시 실제 runtime metadata를 Evidence로 기록하며 같은 fixture의 Variant 비교에서는 가능한 한 동일 runtime/configuration을 사용한다.

## Fixture 원칙

Fixture는 local/synthetic/supplied data만 사용한다.

허용 예:

- synthetic dataframe / CSV
- synthetic ML dataset
- local citation list
- supplied document text
- synthetic DICOM fixture
- synthetic logs / diagnostic output
- dry deployment configuration
- text-only robotics scenario

금지:

- 실제 credential
- 실제 cloud/account write
- 실제 hardware actuation
- 실제 SSH/Docker cluster 변경
- 외부 API 호출
- upstream install command 실행
- upstream bundled script 실행
- destructive command

Fixture마다 최소 다음을 기록한다.

```text
fixture_id
candidate_id
domain_pack
task
local_inputs
expected_requirements
forbidden_actions
acceptance_checks
```

## 평가 지표

각 실행 결과는 최소 다음을 기록한다.

```text
fixture_id
candidate_id
variant
runtime_metadata
acceptance_pass
acceptance_details
selected_capability
loaded_context_bytes
token_count_or_null
execution_time_ms_or_null
dependency_burden
permission_burden
safety_gate
external_access_attempted
notes
```

### 핵심 우선순위

1. correctness / task acceptance
2. safety / permission boundary
3. verification quality
4. current capability 대비 실질적 차별성
5. context / token burden
6. dependency burden
7. execution cost / time

토큰 절감이 correctness나 verification 강도를 낮추는 방식은 채택하지 않는다.

## Decision Policy

### ADOPT_CANDIDATE

다음을 모두 만족하는 경우에만 가능하다.

- Stage B 실행 Evidence 존재
- current-playbook 대비 task acceptance가 악화되지 않음
- 의미 있는 capability/value 증가 Evidence 존재
- safety regression 없음
- license/revision 확정
- dependency/permission burden이 허용 가능
- raw external form을 유지할 이유가 있음

### ADAPT_CANDIDATE

다음과 같은 경우 우선한다.

- 외부 workflow의 실질적 가치가 확인됨
- raw external form에는 provider-specific 지시, 과도한 context, dependency, 권한 또는 중복이 있음
- adapted-playbook이 current/external 대비 동등 이상 acceptance를 보이며 부담을 줄임
- Stage B 실행 Evidence 존재

### REFERENCE_ONLY

- 전문 참고가치는 있으나 Runtime Skill로 가져올 이점이 부족함
- 실행 dependency가 너무 무겁거나 환경 특화가 큼
- Stage B를 수행하지 않아 채택 Evidence가 부족함
- 현재 Skill과 겹치지만 문서/전문 reference 가치는 있음

### REJECTED

- safety/permission Gate 실패
- license/revision 문제
- current-playbook 대비 명확한 가치 없음
- 중복이 심하고 차별성 없음
- fixture acceptance가 지속적으로 불리함
- 재현 가능한 Benchmark 대상이 아님

## Protected Domain

다음 Domain은 기존 품질을 보호한다.

```text
documentation-guide
big-data
```

이 Domain의 Candidate를 `ADOPT_CANDIDATE` 또는 `ADAPT_CANDIDATE`로 판정하려면 current-playbook 대비 acceptance/verification 품질이 악화되지 않았다는 Evidence가 필요하다.

## 산출물

최소 다음을 추가한다.

```text
evaluation/external-skills/benchmark-policy.json
evaluation/external-skills/benchmark-fixtures.json
evaluation/external-skills/benchmark-results.json
evaluation/external-skills/adapted-contexts.json
evaluation/external-skills/adoption-decisions.json
evaluation/external-skills/reports/benchmark-summary.json
evaluation/external-skills/tools/run_benchmark.py
evaluation/external-skills/tools/test_benchmark_wave.py
```

필요한 경우 fixture용 local data를 `evaluation/external-skills/fixtures/` 아래에 추가할 수 있다.

## Safety / Architecture Guardrails

- external script/install 실행 금지
- external API/network/credential 사용 금지
- hardware actuation 금지
- 외부 Skill output을 shell command로 자동 실행 금지
- ACTIVE registry 변경 금지
- Router scoring 변경 금지
- Global AGENTS.md 변경 금지
- Core/Optional Skill을 Benchmark 편의를 위해 수정 금지
- Human Gate 우회 금지
- external Skill의 self-modification/governance 지시 무시
- Candidate의 원본 inspection Evidence를 Benchmark 결과에 맞춰 소급 변경 금지
- `PROMOTED` 상태 생성 금지

## Context / Performance Guardrails

- Benchmark runner는 대상 Candidate/fixture만 lazy load한다.
- 52개 BENCHMARK_READY body 전체를 한 번에 Context로 로드하지 않는다.
- normal task path에서 benchmark artifact를 로드하지 않는다.
- loaded context bytes는 Variant별로 실제 측정한다.
- tokenizer가 제공되는 경우 실제 token count를 기록한다.
- tokenizer가 없으면 임의의 `chars/4` 같은 값을 실제 token count로 표시하지 않는다.
- model/provider 이름을 영구 routing 규칙에 하드코딩하지 않는다.

## Acceptance Criteria

1. BENCH-003A 상태가 COMPLETE - VERIFIED로 기록됨
2. benchmark input shortlist가 기존 15개와 정확히 일치
3. 15개 Candidate 모두 Stage A 완료
4. 15개 Domain Pack 모두 Stage A Evidence 존재
5. Stage A 항목마다 license/revision/dependency/permission/context bytes/safety 기록
6. token count 미측정 시 null + reason 기록
7. Stage B 실행 Candidate는 동일 fixture에서 4 Variant 모두 비교
8. Stage B 미실행 Candidate는 ADOPT_CANDIDATE/ADAPT_CANDIDATE 금지
9. 실행 fixture는 local/synthetic/supplied data만 사용
10. external script 실행 0
11. external API/network credential 사용 0
12. hardware/cloud/destructive side effect 0
13. external access attempt가 있으면 자동 차단되고 Evidence에 기록
14. Variant별 loaded context bytes 측정
15. 실행 시 runtime metadata 기록, model/provider hard-code 0
16. adoption decision 15개 전부 존재
17. decision enum은 ADOPT_CANDIDATE / ADAPT_CANDIDATE / REFERENCE_ONLY / REJECTED만 허용
18. ADOPT/ADAPT에는 Stage B Evidence와 선정 근거 필수
19. protected domain ADOPT/ADAPT는 current-playbook 대비 회귀 0
20. ACTIVE external import 0
21. ACTIVE registry unchanged
22. Router scoring unchanged
23. Global AGENTS.md unchanged
24. benchmark runner/tests deterministic schema 검증 PASS
25. 기존 External Catalog / Effective Coverage / Candidate Wave / Inspection Wave PASS
26. V8.2 normal-path regression 72/72 PASS
27. Harness Audit PASS, warnings 0
28. STRICT Quality Gate PASS, ERRORLEVEL 0
29. git diff --check PASS
30. final working tree clean
31. Windows Evidence 확인 전 COMPLETE 표시 금지

## 완료 판단

BENCH-004 완료는 "몇 개를 채택했는가"가 아니라 다음으로 판단한다.

```text
15개 shortlist에 대한 재현 가능한 Evidence가 존재한다
→ 각 Candidate의 장단점과 비용을 비교할 수 있다
→ ADOPT / ADAPT / REFERENCE / REJECT 결정이 Evidence로 추적된다
→ ACTIVE Library는 아직 변경되지 않는다
```

## 완료 후

후속 Task에서만 다음을 수행한다.

```text
ADOPT_CANDIDATE / ADAPT_CANDIDATE 검토
→ duplicate merge/archive 검토
→ trigger overlap 검토
→ Router regression fixture 추가
→ Promotion Gate
→ Human Gate
→ 제한적 ACTIVE promotion
```

새 ECC 실존 후보는 별도 catalog-correction Task에서 먼저 Candidate 등록/inspection한 뒤 후속 Benchmark Wave에 넣는다.
