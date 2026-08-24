# 트러블슈팅 기록

> 성공한 결과만 남기면 같은 실수를 반복합니다. 이 문서는 실제로 발생한 실패와 그 해결 과정을 **증상 → 원인 → 조치 → 검증 → 재발 방지** 형태로 보존합니다.

---

## TS-001 — 전역 AGENTS가 커지며 고정 Context 비용 증가

**증상**  
Playbook 기능이 늘수록 모든 세션에서 반복해서 읽는 Global `AGENTS.md`가 커졌습니다.

**원인**  
상황별 workflow와 프로젝트 세부 규칙까지 전역 규칙에 넣으려 했습니다.

**조치**

```text
항상 필요한 원칙    → Global AGENTS.md
상황별 상세 절차    → Skill
프로젝트별 사실     → Repository
결정론적 검사       → Harness
```

**재발 방지**  
거의 모든 작업에서 항상 필요한 내용이 아니면 Global Context에 넣지 않습니다.

---

## TS-002 — Skill backup이 중복 Skill로 발견될 위험

**증상**  
Skill 검색 경로 아래 backup에도 `SKILL.md`가 남아 discovery 대상이 될 수 있었습니다.

**조치**

```text
이전  ~/.agents/skills/<skill>.backup-<timestamp>
변경  ~/.codex/playbook-backups/<timestamp>/
```

**재발 방지**  
Skill discovery path에는 관리 대상 Skill 외의 `SKILL.md` 복사본을 두지 않습니다.

---

## TS-003 — 동일 버전 재설치 때 불필요한 backup 누적

**증상**  
실제 변경이 없어도 reinstall 때 backup/복사가 생길 수 있었습니다.

**조치**  
내용/fingerprint가 동일하면 no-op으로 끝나도록 installer를 멱등화했습니다.

**검증**  
fresh install / update / identical reinstall을 분리해 확인했습니다.

---

## TS-004 — STRICT가 실제 실행 Evidence 없이 PASS할 위험

**문제**  
정적 검사만 통과한 상태를 중요 변경의 완료처럼 볼 수 있었습니다.

**조치**

```text
0 = PASS
1 = FAIL
2 = UNVERIFIED
```

STRICT에서 실행 Evidence가 필요한데 `--verify`가 없으면 PASS를 만들지 않습니다.

**재발 방지**  
Harness는 Repository test를 대체하지 않고 보완합니다.

---

## TS-005 — Skill을 모두 ACTIVE로 만들면 Routing이 병목

**증상**  
Skill 수가 늘수록 trigger overlap과 오선택 가능성이 커집니다.

**조치**

```text
DISCOVERED / Catalog
→ INSPECTED / BENCHMARK_READY
→ ADOPT / ADAPT Candidate
→ ACTIVE
```

Runtime에서는 필요한 Skill만 0~3개 materialize합니다.

---

## TS-006 — External Candidate path를 실제 존재로 오인

**대표 사례**

```text
ar-api-documentation
ar-code-documentation
ecc-aws
ecc-azure-bicep
ecc-api-security
ecc-arm-cortex-m
```

**원인**  
Discovery 단계의 candidate path를 pinned revision의 실제 파일 존재와 동일시했습니다.

**조치**

```text
path 없음
→ REJECTED
→ safety_findings = upstream-path-missing-at-pinned-revision
```

**재발 방지**  
Candidate 발견 후 revision resolve → path existence → license 확인을 preflight로 둡니다.

---

## TS-007 — 공개 저장소의 Proprietary Skill을 READY 처리할 위험

**사례**

```text
kd-pdf
→ Proprietary
→ REFERENCE_ONLY

nv-rtvi-cv-scaffold-vss-service
→ NVIDIA Proprietary
→ REFERENCE_ONLY
```

**조치**

```text
per-skill explicit license
> source policy
> repository root license
```

Proprietary/불명확 license는 `BENCHMARK_READY`로 올리지 않습니다.

---

## TS-008 — External scripts를 inspection 중 실행할 위험

외부 Skill에는 setup, SSH, Docker, GPU, network, helper script가 포함될 수 있습니다.

**조치**  
BENCH 단계는 정적 inspection으로 제한했습니다.

```text
external_scripts_executed = false
```

bundled script가 있어도 존재와 역할만 기록하고 실행하지 않습니다.

---

## TS-009 — NVIDIA Batch A tuple index 버그

**증상**

```text
IndexError: tuple index out of range
```

**원인**  
9개 필드 tuple에서 `v[9]`를 잘못 참조했습니다.

**조치**  
ad-hoc tuple 대신 named dictionary를 사용했습니다.

```python
v['license']
v['burden']
v['scripts']
```

**검증**

```text
ADDED NVIDIA BATCH A 5
Ran 8 tests
OK
```

---

## TS-010 — Windows CMD 긴 one-liner 관리 위험

**문제**  
대량 JSON record를 Python `-c` 하나로 넣으면 CMD 길이/복붙 안정성이 떨어집니다.

**조치**

```text
작은 Batch
→ focused test
→ count assertion
→ 다음 Batch
```

5~10 record 단위로 나누고 각 Batch 뒤 검증합니다.

---

## TS-011 — 다른 Repository에서 Playbook 명령 실행

**증상**

```text
FileNotFoundError:
evaluation\external-skills\candidates.json
```

**원인**  
현재 CMD가 Playbook Repository가 아닌 다른 Repository에 있었습니다.

**조치**

```cmd
cd /d D:\Codex_Playbook\codex_ai_agent_playbook_kit_v5
```

**재발 방지**  
Repository-relative 명령 전 `git rev-parse --show-toplevel` 또는 현재 경로를 확인합니다.

---

## TS-012 — ECC 404를 보안 비공개 처리로 오해할 가능성

**증상**

```text
skills/aws
skills/azure-bicep
skills/api-security
skills/arm-cortex-m
```

가 pinned ECC revision에서 404였습니다.

**조사 결과**  
ECC 저장소와 다수 Skill은 정상 공개되어 있어 보안 비공개보다 candidate path drift로 판단했습니다.

**조치**

```text
REJECTED
upstream-path-missing-at-pinned-revision
```

실제 ECC 트리에서는 다음 유력 후보를 별도로 확인했습니다.

```text
ecc-api-design
ecc-backend-patterns
ecc-coding-standards
ecc-agent-introspection-debugging
ecc-security-review
ecc-deployment-patterns
ecc-react-testing
ecc-verification-loop
```

---

## TS-013 — 이름만 보고 Skill 의미를 잘못 분류할 위험

**사례**  
ECC `benchmark-methodology`는 이름만 보면 소프트웨어 benchmark/test Skill처럼 보였지만 실제 내용은 경쟁사/브랜드 비교와 positioning 방법론이었습니다.

**조치**  
testing-qa에 억지로 매핑하지 않았습니다.

**재발 방지**

```text
frontmatter description
activation 조건
핵심 workflow
dependencies/permissions
bundled files
```

을 확인하고 domain을 지정합니다.

---

## TS-014 — Invalid/stale pinned revision

**문제**  
기존 기록의 SHA가 GitHub commit/tree API에서 유효한 commit으로 resolve되지 않는 경우가 있었습니다.

**조치**  
기존 값을 맹목적으로 재사용하지 않고 새 Wave마다 revision을 다시 resolve합니다.

```text
source revision resolve
→ commit fetch 성공
→ target path fetch 성공
```

---

## TS-015 — 좋은 새 후보를 발견했지만 현재 Task에 바로 넣지 않음

ECC 재탐색에서 유용한 실존 Skill 8개를 발견했습니다.

하지만 BENCH-003A 계약은 **기존 100 Candidate를 추가 inspection하여 50+ READY를 만드는 것**이었습니다.

**결정**

```text
BENCH-003A 먼저 완료
→ 별도 catalog-correction Task
→ ECC 신규 후보 등록/검증
```

좋은 발견도 현재 Task 범위를 깨면서 즉시 흡수하지 않습니다.

---

## TS-016 — `anth-claude-api` 추가 후 focused test 실패

**증상**

```text
test_uninspected_cluster_member_rejected
AssertionError: ExternalCatalogError not raised
```

**상황**  
`anth-claude-api`를 실제 inspection에 추가해 domain coverage가 20이 된 직후 발생했습니다.

**원인**  
테스트 fixture가 다음 candidate를 영구적인 “미검사 후보”처럼 하드코딩했습니다.

```text
anth-claude-api
```

이제 실제로 검사된 candidate이므로 fixture의 가정이 낡았습니다.

Validator 자체는 여전히 정상적으로:

```text
cluster member가 inspections에 없으면 ExternalCatalogError
```

를 발생시키고 있었습니다.

**조치**  
검증 로직을 약화하지 않고 fixture만 일반화했습니다.

```text
실제 duplicate cluster 멤버 하나 선택
→ temp inspections에서 해당 멤버 제거
→ validate_repository(root)
→ ExternalCatalogError 확인
```

**검증**

```text
Inspection Wave 8/8 PASS
```

**재발 방지**  
변하는 Catalog 데이터에서 특정 candidate ID를 “항상 미검사”라고 가정하는 fixture를 피합니다.

---

## TS-017 — LF → CRLF 경고가 STRICT Gate에서 conflict처럼 잡힘

**증상**

STRICT Quality Gate 첫 실행:

```text
FAIL unresolved Git conflicts:
warning: in the working copy of
'evaluation/external-skills/tools/test_inspection_wave.py',
LF will be replaced by CRLF the next time Git touches it
```

**원인**  
`test_inspection_wave.py`가 LF로 저장됐고 Windows Git이 CRLF 변환 경고를 stderr/stdout에 출력했습니다. Quality Gate의 conflict 검사에서 이 경고 텍스트가 conflict path처럼 취급됐습니다.

실제 Git conflict는 없었습니다.

**조치**  
Quality Gate나 테스트를 약화하지 않고 파일 줄바꿈만 CRLF로 복구했습니다.

**재검증**

```text
Inspection Wave          8/8 PASS
STRICT Quality Gate      PASS
git diff --check         PASS
```

**재발 방지**

- Windows에서 Repository의 줄바꿈 정책을 유지
- warning과 실제 path를 분리해 해석
- Gate 실패 시 검증을 우회하지 않고 root cause 확인

---

# BENCH-003A 최종 Evidence

```text
INSPECTED                  62
BENCHMARK_READY            52
INSPECTION_DOMAINS         20
ACTIVE_IMPORTS              0
EXTERNAL_SCRIPTS_EXECUTED   0
External Catalog          12/12 PASS
Effective Coverage         5/5 PASS
Candidate Wave             5/5 PASS
Inspection Wave            8/8 PASS
V8.2 normal regression    72/72 PASS
Harness Audit             PASS / warnings 0
STRICT Quality Gate       PASS
git diff --check          PASS
```

완료 commit:

```text
4e1d92531cebb32a995562e922db50b35e0bcb5f
```

---

# 반복되는 공통 패턴

프로젝트에서 반복된 문제는 대체로 다음입니다.

```text
1. Source of Truth 혼동
2. Discovery 결과를 Verification 결과로 오인
3. 자동화 명령 자체의 작은 구현 버그
4. Task 범위를 좋은 아이디어 때문에 확장하려는 유혹
5. Windows/Git 환경 차이를 실제 코드 실패로 오인
6. fixture가 변하는 실제 데이터 상태를 하드코딩
```

현재 기본 방어선:

```text
Repository root 확인
→ pinned revision 확인
→ path/content/license 정적 검사
→ 작은 batch
→ focused test
→ count/invariant assertion
→ full regression
→ Harness Audit
→ STRICT Gate
→ diff check
→ clean working tree
→ commit/push
```

이 순서를 생략하지 않는 것이 가장 큰 재발 방지책입니다.