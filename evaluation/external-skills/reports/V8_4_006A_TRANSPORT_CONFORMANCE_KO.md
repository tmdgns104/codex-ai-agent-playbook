# V8.4-006A Transport Conformance Summary

- Contract: `C_VERSIONED_OPT_IN_LAUNCHER_CONTRACT`
- Mode: `SEPARATE_VERIFIED_CONTEXT_V1`
- Execution type: deterministic, non-inference simulation
- Unit tests: **5/5 PASS**
- Current Codex CLI: **unsupported**
- Complete positive control: **compatible**
- Incomplete positive control: **partial**
- Real transport promotion gate: **still false**
- Model/API/network/production integration: **0**

핵심 판정은 단순하다. 현재 Repository는 exact user task를 positional argument로
보존하는 Evidence는 있지만, adapted context를 별도 verified channel로 실제 모델 입력에
전달한다는 Codex CLI/backend Evidence가 없다. 따라서 006A 시뮬레이션 성공을
`transport_conformance=true`로 바꾸지 않는다.

다음 단계는 V8.4-007 controlled benchmark의 **정책/holdout fixture를 먼저 freeze**할 수
있지만, adapted-on-demand 실제 비교 실행은 real transport가 승인되기 전까지 BLOCKED로
유지해야 한다.
