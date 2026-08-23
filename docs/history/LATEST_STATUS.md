# 최신 진행상황 — 2026-08-24

> 이 문서는 현재 V8.3 외부 Expert Skill Catalog 작업의 최신 체크포인트를 요약합니다. 완료 판정은 항상 Git/Test/Artifact Evidence를 기준으로 하며, 원격에 아직 반영되지 않은 로컬 결과는 별도로 표시합니다.

## 1. 안정 버전

현재 안정 버전은 `main`의 **V8.2 COMPLETE - VERIFIED**입니다.

V8.3은 Skill Library 확장을 위한 실험·검증 단계이며 두 트랙으로 분리되어 있습니다.

```text
Track A
v8.3-skill-library-expansion
→ 내부 Candidate 확장 및 promotion 전 검증

Track B
v8.3-expert-skill-catalog
→ 외부 Expert Skill catalog / inspection / benchmark
```

## 2. Track A 체크포인트

브랜치:

```text
v8.3-skill-library-expansion
```

체크포인트:

```text
e5a83cdf78a091f68978f46138f402e866bce278
V8.3: register Batch 2A candidate files in manifest
```

Batch 2A 후보 8개는 Candidate 등록과 회귀 검증을 통과했지만 아직 ACTIVE로 promotion하지 않았습니다.

확인된 Evidence:

```text
Candidate          8/8
activation         72/72
Skill Audit         9/9
skills             79/79
Harness Audit      PASS
STRICT Gate        PASS / exit 0
```

## 3. Track B 원격 체크포인트

브랜치:

```text
v8.3-expert-skill-catalog
```

BENCH-003 완료 commit:

```text
8c5fc7d8818bf9bdc0b972386d640ded04e9d1e9
V8.3: complete expert skill inspection verification
```

BENCH-003A Task baseline:

```text
d8e801f2b668027baafb51f3fbf73507e9e659fe
V8.3: define 50+ expert skill inspection expansion
```

BENCH-003A의 목표는 다음과 같습니다.

```text
INSPECTED >= 60
BENCHMARK_READY >= 50
inspected domain packs >= 20
external scripts executed = false
ACTIVE import = 0
```

## 4. 현재 로컬 Evidence

2026-08-24 현재 실제 로컬 baseline은 다음과 같습니다.

```text
FILE_EXISTS               True
INSPECTED                  53
BENCHMARK_READY            43
EXTERNAL_SCRIPTS_EXECUTED  False
```

현재 working tree에는 다음 파일의 미커밋 변경이 있습니다.

```text
evaluation/external-skills/inspections.json
```

따라서 이 숫자는 아직 Track B 원격 HEAD의 완료 상태가 아닙니다.

## 5. ECC path drift 조사 결과

초기 catalog에 등록됐던 다음 4개 후보는 고정 revision에서 실제 경로가 존재하지 않았습니다.

```text
ecc-aws          -> skills/aws
ecc-azure-bicep  -> skills/azure-bicep
ecc-api-security -> skills/api-security
ecc-arm-cortex-m -> skills/arm-cortex-m
```

처리 결과:

```text
ecc-aws          REJECTED
ecc-azure-bicep  REJECTED
ecc-api-security REJECTED
ecc-arm-cortex-m REJECTED
```

공통 안전 기록:

```text
upstream-path-missing-at-pinned-revision
```

비슷한 이름의 다른 Skill로 조용히 대체하지 않았습니다.

### ECC 재탐색에서 실제 존재가 확인된 유력 후보

다음 Skill은 실제 ECC 트리에서 별도 후보로 검토할 가치가 있음을 확인했습니다.

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

이 후보들은 기존 잘못된 후보를 덮어쓰지 않고 별도 catalog correction Task에서 새 Candidate로 등록하는 방향이 적절합니다.

## 6. K-Dense 저장소 이름 변경 확인

기존 조사 과정에서 사용하던 K-Dense 저장소는 현재 다음 정식 이름으로 확인됐습니다.

```text
K-Dense-AI/scientific-agent-skills
```

기존 pinned revision은 새 정식 저장소에서도 유효합니다.

```text
390f5146bf3c1877cf15636a3dd7b775e4f0f185
```

따라서 이전 조회 실패의 원인은 pinned SHA 손상이 아니라 저장소 이름 변경에 따른 경로 문제였습니다.

## 7. K-Dense 추가 8개 정적검사 결과

다음 8개는 pinned revision의 실제 `SKILL.md`, 디렉터리 구조, 라이선스, dependency, network/credential 요구, bundled script 여부를 정적으로 검사했습니다.

```text
kd-statsmodels
kd-matplotlib
kd-seaborn
kd-vaex
kd-zarr-python
kd-peer-review
kd-scientific-schematics
kd-infographics
```

현재 판정:

```text
8/8 BENCHMARK_READY 판정 가능
```

단, 이 8개는 **아직 로컬 `inspections.json`에 반영되지 않았습니다.** 따라서 현재 공식 로컬 수치는 계속 `INSPECTED 53 / BENCHMARK_READY 43`입니다.

### 주요 안전 메모

#### `kd-statsmodels`

- BSD-3-Clause
- 통계 추론 결과는 사람의 검증 필요
- bundled script 없음

#### `kd-matplotlib`

- upstream license 확인
- bundled `scripts/` 존재
- script 실행하지 않음
- 파일 출력 및 GUI 사용 가능성 기록 필요

#### `kd-seaborn`

- BSD-3-Clause
- `sns.load_dataset()`은 캐시가 없을 때 public example data를 네트워크로 받을 수 있음
- private/offline 작업은 local file 사용 권고

#### `kd-vaex`

- MIT
- 대용량 파일 read/write 가능
- S3/GCS/Azure 계열 optional cloud I/O는 사용자 credential이 필요할 수 있음
- 실제 cloud 접근은 수행하지 않음

#### `kd-zarr-python`

- MIT
- S3/GCS 등 remote store는 optional dependency와 credential이 필요할 수 있음
- 실제 network 접근은 수행하지 않음

#### `kd-peer-review`

- MIT
- confidential manuscript는 authorization과 venue policy 확인이 선행되어야 함
- local-only deterministic CLI가 bundled되어 있음
- bundled script 실행하지 않음

#### `kd-scientific-schematics`

- MIT
- OpenRouter API key를 사용할 수 있음
- prompt와 생성 이미지가 외부 서비스로 전송될 수 있음
- external API, script 모두 실행하지 않음

#### `kd-infographics`

- Skill frontmatter에는 개별 license가 없었음
- pinned repository의 `LICENSE.md`가 MIT임을 별도 확인
- OpenRouter/Perplexity 계열 외부 API 사용 가능
- external API, script 모두 실행하지 않음

## 8. README 및 한국어 문서 최신화

`docs-history-v8.3` 문서 브랜치에서 GitHub 첫 화면과 상세 가이드를 현재 상태에 맞춰 갱신했습니다.

```text
README.md
README_KO.md
docs/DOCUMENTATION_POLICY.md
docs/history/README.md
docs/history/LATEST_STATUS.md
docs/history/DEVELOPMENT_JOURNAL.md
docs/history/TROUBLESHOOTING_LOG.md
docs/history/RESEARCH_LOG.md
```

두 README는 이제 다음을 동시에 보여줍니다.

```text
안정판  V8.2 COMPLETE / VERIFIED
개발판  V8.3 Skill Library Expansion
```

설치·일반 사용 명령은 검증된 `main` 기준으로 유지하고, V8.3 Track A/Track B의 개발 현황과 BENCH-003A 수치는 별도 개발 상태로 표시합니다.

설명 문장은 한국어를 기본으로 하며 코드, 명령어, 파일 경로, Skill ID, 상태 enum, commit SHA 등 실제 계약 식별자만 원문을 유지합니다.

## 9. 다음 실행 단계

BENCH-003A 범위를 유지하기 위해 새 ECC 후보를 현재 Task에 억지로 추가하지 않습니다.

다음 순서는 다음과 같습니다.

```text
1. K-Dense Batch A 4개를 inspections.json에 반영
2. focused inspection test
3. 수치 확인: INSPECTED 57 / READY 47 목표
4. K-Dense Batch B 4개 반영
5. 수치 확인: INSPECTED 61 / READY 51 목표
6. external catalog / coverage / candidate / inspection tests
7. 기존 shortlist >= 15 확인
8. normal path regression
9. Harness Audit
10. STRICT Gate
11. git diff --check
12. working tree 검증
13. 완료 Evidence가 모두 PASS일 때만 commit/push
```
