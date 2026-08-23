# 트러블슈팅 기록

> 성공한 결과만 남기면 같은 실수를 반복합니다. 이 문서는 실제로 발생한 실패와 그 해결 과정을 **증상 → 원인 → 조치 → 재발 방지** 형태로 보존합니다.

## 읽는 법

각 항목은 다음 형식을 사용합니다.

```text
증상
원인
조치
검증
재발 방지
```

---

## TS-001 — 전역 AGENTS가 커지면서 고정 Context 비용 증가

### 증상

Playbook 기능이 늘수록 모든 세션에서 반복해서 읽는 Global `AGENTS.md`가 커졌습니다.

### 원인

상황별 workflow와 프로젝트별 세부 규칙까지 전역 규칙에 넣으려 했기 때문입니다.

### 조치

V7에서 책임을 분리했습니다.

```text
항상 필요한 원칙    → Global AGENTS.md
상황별 상세 절차    → Skill
프로젝트별 사실     → Repository
결정론적 검사       → Harness
```

### 검증

V7 Windows 설치/재설치 및 `verify-install.ps1`을 통해 전역 적용본 drift와 멱등성을 확인했습니다.

### 재발 방지

새 규칙을 추가할 때 먼저 묻습니다.

> 이 내용이 거의 모든 작업에서 항상 필요한가?

아니면 Global Context에 넣지 않습니다.

---

## TS-002 — Skill backup이 중복 Skill로 발견될 위험

### 증상

Skill 폴더 안에 backup을 만들면 backup 안의 `SKILL.md`도 discovery 대상이 될 수 있습니다.

### 원인

이전 backup 위치:

```text
~/.agents/skills/<skill>.backup-<timestamp>
```

### 조치

backup을 discovery path 밖으로 이동했습니다.

```text
~/.codex/playbook-backups/<timestamp>/
```

legacy `*.backup-*`도 설치 시 이동하도록 했습니다.

### 검증

V7 Windows 실환경에서 legacy backup migration과 재설치 no-op을 확인했습니다.

### 재발 방지

Skill search path에는 **활성/관리 Skill 외의 `SKILL.md` 복사본을 두지 않습니다.**

---

## TS-003 — 동일 버전 재설치 때 불필요한 backup 누적

### 증상

설치를 반복할 때 실제 변경이 없어도 backup과 복사가 계속 생길 수 있었습니다.

### 원인

설치 전 fingerprint/내용 동일 여부를 충분히 비교하지 않았기 때문입니다.

### 조치

변경이 있을 때만 backup/replace하고 동일하면 `OK`로 끝내도록 설치 스크립트를 멱등화했습니다.

### 검증

V6 → V7 업데이트 직후 동일 버전을 다시 설치했을 때 새 backup/installation이 생기지 않았습니다.

### 재발 방지

installer 변경 시 반드시:

1. fresh install
2. update
3. identical reinstall

세 경로를 분리 검증합니다.

---

## TS-004 — STRICT 검증이 실제 실행 Evidence 없이 PASS할 위험

### 증상

보안/배포/중요 변경에서도 정적 검사만 통과하면 완료처럼 보일 수 있습니다.

### 원인

Quality Gate와 Repository 실제 test/build Evidence의 책임이 섞일 수 있기 때문입니다.

### 조치

계약을 명확히 했습니다.

```text
0 = PASS
1 = FAIL
2 = UNVERIFIED
```

STRICT에서 실제 실행 Evidence가 필요한데 `--verify`가 없으면 PASS를 만들지 않습니다.

### 재발 방지

Harness의 역할은 Repository test를 대체하는 것이 아니라 보완하는 것입니다.

---

## TS-005 — 모든 Skill을 ACTIVE로 만들면 Routing 정확도가 병목

### 증상

Skill을 많이 모을수록 Trigger overlap과 오선택 가능성이 커집니다.

### 원인

Library 규모와 Runtime Active 규모를 같은 것으로 생각했기 때문입니다.

### 조치

계층을 분리했습니다.

```text
DISCOVERED / Catalog
→ INSPECTED / BENCHMARK_READY
→ ADOPT / ADAPT Candidate
→ ACTIVE
```

Runtime에서는 필요한 Skill만 0~3개 materialize합니다.

### 재발 방지

Skill 수를 늘릴 때 Context 크기보다 **trigger overlap / routing precision / permission boundary**를 먼저 봅니다.

---

## TS-006 — External Candidate path를 실제 존재로 오인

### 증상

BENCH-002에 등록된 외부 Candidate 중 일부 path가 BENCH-003/003A 실제 inspection에서 존재하지 않았습니다.

대표 사례:

```text
ar-api-documentation
ar-code-documentation

ecc-aws
ecc-azure-bicep
ecc-api-security
ecc-arm-cortex-m
```

### 원인

BENCH-002는 discovery 단계였고, candidate 이름/path 후보를 실제 pinned revision 파일 존재 여부와 동일시하면 안 됐습니다.

### 조치

pinned revision의 실제 path를 직접 조회하고 존재하지 않으면:

```text
REJECTED
safety_findings = upstream-path-missing-at-pinned-revision
```

으로 기록했습니다.

비슷한 다른 Skill로 조용히 대체하지 않았습니다.

### 재발 방지

Discovery pipeline에 다음 preflight를 추가하는 방향을 채택합니다.

```text
Candidate 발견
→ source revision resolve
→ path existence 확인
→ license 확인 가능 여부
→ DISCOVERED 등록
```

경로가 불확실하면 verified candidate가 아니라 discovery lead로 취급합니다.

---

## TS-007 — Proprietary Skill을 Open Source Source라는 이유로 READY 처리할 위험

### 증상

공개 GitHub 저장소 안의 Skill이라도 개별 Skill license가 Proprietary일 수 있습니다.

사례:

```text
kd-pdf
→ Proprietary
→ REFERENCE_ONLY

nv-rtvi-cv-scaffold-vss-service
→ NVIDIA Proprietary
→ REFERENCE_ONLY
```

### 원인

root repository license만 보고 per-skill license를 생략하면 잘못 채택할 수 있습니다.

### 조치

license 우선순위:

```text
per-skill explicit license
> source policy
> repository root license
```

Proprietary/불명확 license는 BENCHMARK_READY로 올리지 않습니다.

### 재발 방지

Inspection record에 항상 `license_status`를 필수로 기록합니다.

---

## TS-008 — External scripts를 검증 목적으로 실행할 위험

### 증상

외부 Skill에는 helper script, setup, remote SSH, Docker, GPU, network 작업이 포함될 수 있습니다.

### 위험 사례

- NVIDIA HSB setup/test: SSH, Docker, hardware, network configuration
- DeepStream: GPU runtime, generated pipeline
- AI-Q: HTTP backend
- K-Dense scientific tools: bundled Python scripts

### 조치

BENCH 단계에서는 **정적 inspection만 수행**했습니다.

```text
external_scripts_executed = false
```

bundled script가 있어도 존재/역할만 기록하고 실행하지 않았습니다.

### 재발 방지

외부 코드 실행은 별도 sandbox/task/explicit approval 없이는 inspection에 포함하지 않습니다.

---

## TS-009 — NVIDIA Batch A 삽입 명령 tuple index 버그

### 증상

NVIDIA inspection record 삽입용 Python one-liner가 `IndexError: tuple index out of range`로 실패했습니다.

### 원인

Tuple은 9개 필드(`0..8`)였는데 다음처럼 잘못 참조했습니다.

```python
'bundled_scripts': v[9]
```

실제 index는 `v[8]`이었습니다.

### 안전성 확인

오류가 `p.write_bytes(...)` 이전에 발생했기 때문에 부분 쓰기가 없을 것으로 예상됐지만 추측하지 않고 확인했습니다.

실제 Evidence:

```text
INSPECTED 39
NVIDIA_BATCH_A_FOUND []
EXTERNAL_SCRIPTS_EXECUTED False
```

### 조치

Tuple index 방식 자체를 버리고 named dictionary를 사용했습니다.

```python
v['license']
v['burden']
v['scripts']
```

### 검증

수정 후:

```text
ADDED NVIDIA BATCH A 5
Ran 8 tests
OK
```

### 재발 방지

여러 의미 필드를 가진 ad-hoc tuple 대신 dict/dataclass를 사용합니다.

---

## TS-010 — Windows CMD 긴 one-liner 관리 위험

### 증상

대량 JSON record를 한 번에 넣는 Python `-c` 명령이 매우 길어졌습니다.

### 원인

Windows CMD 길이 제한과 복붙 안정성을 고려하지 않고 하나의 명령으로 과도하게 묶을 수 있었습니다.

### 조치

Wave를 Batch A/B로 나누고 중간마다 focused test를 실행했습니다.

예:

```text
NVIDIA Batch A 5개
→ focused test 8/8
→ Batch B 5개
→ focused test 8/8
→ count verification
```

### 재발 방지

- 5~10 record 단위 batch
- batch마다 duplicate/count assertion
- batch마다 focused verification
- 긴 shell chain보다 독립 명령 선호

---

## TS-011 — 다른 Repository에서 Playbook 명령 실행

### 증상

다음 오류 발생:

```text
FileNotFoundError:
evaluation\external-skills\candidates.json
```

### 원인

현재 CMD가 Playbook Repository가 아니라:

```text
D:\qwen-harness-test
```

에 있었습니다.

정상 위치:

```text
D:\Codex_Playbook\codex_ai_agent_playbook_kit_v5
```

### 조치

```cmd
cd /d D:\Codex_Playbook\codex_ai_agent_playbook_kit_v5
```

후 동일 명령 재실행.

### 검증

```text
CURRENT_INSPECTED 49
ALREADY_INSPECTED []
```

### 재발 방지

Repository-relative 명령 전 `cd` 또는 `git rev-parse --show-toplevel`로 root를 확인합니다.

---

## TS-012 — ECC 후보 4개가 404: 보안 처리로 오해할 가능성

### 증상

```text
skills/aws
skills/azure-bicep
skills/api-security
skills/arm-cortex-m
```

가 ECC pinned revision에서 404였습니다.

### 처음 의심

특정 Skill을 보안상 숨겼거나 private 처리했을 가능성.

### 조사 결과

ECC 저장소 자체와 다수 Skill은 정상 공개되어 있었고, 실제 `skills/` 및 `.agents/skills/` 구조도 존재했습니다.

따라서 보안 비공개 처리보다 **candidate path drift / discovery 부정확성**으로 판단했습니다.

### 조치

4개 모두:

```text
REJECTED
upstream-path-missing-at-pinned-revision
```

### 추가 발견

실제 ECC에는 다음 실존 Skill이 있었습니다.

```text
.agents/skills/api-design
.agents/skills/backend-patterns
.agents/skills/coding-standards
.agents/skills/agent-introspection-debugging
.agents/skills/security-review
skills/deployment-patterns
skills/react-testing
.agents/skills/verification-loop
```

### 재발 방지

추측 이름을 candidate path로 만들지 않고 recursive tree/contents API의 실제 path에서 후보를 생성합니다.

---

## TS-013 — 이름만 보고 Skill 의미를 잘못 분류할 위험

### 증상

ECC `benchmark-methodology`라는 이름은 소프트웨어 benchmark/test Skill처럼 보였습니다.

### 실제 내용

본문은 경쟁사/브랜드 비교와 positioning score 방법론이었습니다.

### 조치

testing-qa domain에 억지로 매핑하지 않고 현재 003A 대상에서 제외했습니다.

### 재발 방지

Skill 분류는 최소한 다음을 봅니다.

1. frontmatter description
2. activation 조건
3. 핵심 workflow
4. dependencies/permissions
5. 실제 bundled files

이름만 보고 domain을 지정하지 않습니다.

---

## TS-014 — Invalid/stale pinned revision 발견

### 증상

기존 alirezarezvani inspection에 사용된 것으로 기록된 SHA를 GitHub commit/tree API에서 확인했을 때 유효한 commit으로 해석되지 않았습니다.

### 위험

존재하지 않는 revision을 Evidence처럼 계속 재사용하면 재현성이 깨집니다.

### 조치

새 inspection에서 기존 값을 맹목적으로 재사용하지 않고, 실제 GitHub에서 resolve되는 current commit을 다시 확인하는 원칙을 적용했습니다.

확인된 최신 commit 예:

```text
98180dafc4f0bc9d629bd479fc6107674cfb3cf8
```

### 재발 방지

새 Wave 시작 전에 항상:

```text
source revision resolve
→ commit fetch 성공
→ target path fetch 성공
```

을 preflight로 확인합니다.

---

## TS-015 — 새 ECC 후보를 발견했지만 현재 Task에 바로 추가하지 않음

### 상황

ECC 재탐색에서 실존하고 유용한 Skill 8개를 발견했습니다.

### 문제

현재 BENCH-003A의 계약은 **기존 100 Candidate를 추가 inspection하여 50+ READY를 만드는 것**입니다.

새 ECC 후보를 지금 `candidates.json`에 추가하면 Task 범위를 확장하게 됩니다.

### 결정

```text
BENCH-003A 먼저 완료
→ 별도 catalog-correction Task
→ ECC 신규 후보 등록/검증
```

### 교훈

좋은 발견이 나와도 현재 Task 계약을 깨면서 즉시 흡수하지 않습니다.

---

# 반복되는 공통 패턴

이번 프로젝트의 트러블 대부분은 다음 네 종류였습니다.

```text
1. Source of Truth 혼동
2. Discovery 결과를 Verification 결과로 오인
3. 자동화 명령 자체의 작은 구현 버그
4. Task 범위를 좋은 아이디어 때문에 확장하려는 유혹
```

따라서 현재 기본 방어선은 다음과 같습니다.

```text
Repository root 확인
→ pinned revision 확인
→ path/content/license 정적 검사
→ 작은 batch
→ focused test
→ count/invariant assertion
→ diff check
→ full regression
→ commit
```

이 순서를 생략하지 않는 것이 가장 큰 재발 방지책입니다.
