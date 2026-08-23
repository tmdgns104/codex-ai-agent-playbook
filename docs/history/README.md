# Codex AI Agent Playbook — 프로젝트 기록

> 개발 과정에서 **무엇을 만들었는지**뿐 아니라 **왜 그렇게 바꿨는지, 어디서 실패했는지, 무엇을 검증했는지**를 남기는 기록입니다.

이 디렉터리는 사용자 가이드(`docs/QUICKSTART.md`, `docs/HOW_IT_WORKS.md`)와 목적이 다릅니다.  
사용자 가이드는 현재 사용법을 설명하고, 이 기록은 프로젝트가 현재 구조에 도달한 **과정과 Evidence**를 보존합니다.

## 문서 작성 언어

이 저장소에서 새로 추가하거나 갱신하는 설명 문서는 **한국어를 기본 언어**로 사용합니다.

코드, 명령어, 경로, Skill ID, 상태 enum, commit SHA처럼 실제 동작 계약에 사용되는 식별자는 정확성을 위해 원문을 유지합니다.

자세한 기준은 [`docs/DOCUMENTATION_POLICY.md`](../DOCUMENTATION_POLICY.md)를 참고합니다.

## 기록 문서

| 문서 | 내용 |
|---|---|
| [LATEST_STATUS.md](LATEST_STATUS.md) | **2026-08-24 기준 최신 진행상황, 현재 재개 지점, 다음 검증 단계** |
| [DEVELOPMENT_JOURNAL.md](DEVELOPMENT_JOURNAL.md) | V4 → V8.3 개발 흐름, 설계 변화, 주요 체크포인트 |
| [TROUBLESHOOTING_LOG.md](TROUBLESHOOTING_LOG.md) | 실제 장애/실수/실패의 증상 → 원인 → 조치 → 재발 방지 |
| [RESEARCH_LOG.md](RESEARCH_LOG.md) | Skill Library 확장 연구, 외부 소스 조사, BENCH 실험 기록 |

## 현재 기준점 — 2026-08-24

안정 버전은 `main`의 **V8.2 COMPLETE - VERIFIED**입니다.  
V8.3은 Skill Library를 대규모로 확장하기 위한 실험/검증 단계입니다.

```text
main
└─ V8.2 COMPLETE - VERIFIED

v8.3-skill-library-expansion
└─ Track A: 내부 Candidate 확장 / promotion 전 검증

v8.3-expert-skill-catalog
└─ Track B: 외부 Expert Skill catalog / inspection / benchmark
```

### V8.3 Track B 원격 체크포인트

```text
8c5fc7d8818bf9bdc0b972386d640ded04e9d1e9
V8.3: complete expert skill inspection verification

↓

d8e801f2b668027baafb51f3fbf73507e9e659fe
V8.3: define 50+ expert skill inspection expansion
```

### 2026-08-24 로컬 작업 체크포인트

아래 값은 현재 실제 로컬 실행 Evidence이며 아직 `v8.3-expert-skill-catalog` 원격 HEAD에는 커밋되지 않은 상태입니다.

```text
FILE_EXISTS                True
INSPECTED                   53
BENCHMARK_READY             43
ECC path-drift REJECTED      4
EXTERNAL_SCRIPTS_EXECUTED  False
focused inspection tests    8/8 PASS
git diff --check            PASS
working tree                evaluation/external-skills/inspections.json modified
```

추가로 K-Dense 후보 8개에 대한 pinned upstream 정적검사는 완료됐고 **8/8 BENCHMARK_READY 판정 가능** 상태지만, 아직 `inspections.json`에는 반영하지 않았습니다.

따라서 현재 공식 로컬 수치는 계속 다음과 같습니다.

```text
INSPECTED        53
BENCHMARK_READY  43
```

현재 재개 지점은 **K-Dense Batch A 반영 직전**입니다.

상세 내용은 [LATEST_STATUS.md](LATEST_STATUS.md)에 기록했습니다.

## 최근 조사에서 확인된 중요 사항

### ECC

초기 catalog의 다음 4개 후보는 pinned revision에서 실제 경로가 없어 `REJECTED` 처리했습니다.

```text
ecc-aws
ecc-azure-bicep
ecc-api-security
ecc-arm-cortex-m
```

비슷한 Skill로 조용히 대체하지 않았습니다.

실제 ECC 트리 재탐색에서는 다음 후보가 별도 신규 Candidate로 검토할 가치가 있음을 확인했습니다.

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

### K-Dense

현재 정식 저장소 이름은 다음과 같이 확인됐습니다.

```text
K-Dense-AI/scientific-agent-skills
```

기존 pinned revision은 새 정식 저장소에서도 유효합니다.

```text
390f5146bf3c1877cf15636a3dd7b775e4f0f185
```

따라서 이전 404의 원인은 pinned SHA 손상이 아니라 저장소 이름 변경에 따른 경로 문제였습니다.

## 기록 원칙

이 프로젝트의 개발 기록은 다음 원칙을 따릅니다.

1. **자기보고 PASS를 Evidence로 사용하지 않는다.**
2. Git 상태, 테스트 결과, Quality Gate, Audit, 실제 파일 내용을 우선한다.
3. 실패를 삭제하지 않고 원인과 재발 방지까지 기록한다.
4. 외부 Skill은 이름이나 README만 믿지 않고 pinned revision의 실제 path/content/license를 확인한다.
5. 외부 script/install은 inspection 중 실행하지 않는다.
6. 라이선스 불명확/Proprietary는 자동 채택하지 않는다.
7. Task 범위를 넓혀서 테스트를 통과시키지 않는다.
8. 토큰 절감은 중요하지만 정확성/검증 강도보다 우선하지 않는다.
9. 문서는 한국어를 기본으로 작성하되 실제 코드 계약 식별자는 원문을 유지한다.
10. 원격 완료 상태와 로컬 미커밋 Evidence를 섞지 않는다.

## 전체 흐름

```mermaid
flowchart LR
    V4[V4\nPlaybook + PPT] --> V5[V5\n사람이 읽기 쉬운 개발]
    V5 --> V6[V6\n장기 작업 + Task Router]
    V6 --> V7[V7\nContext 절감]
    V7 --> V8[V8\n결정론적 Harness]
    V8 --> V82[V8.2\nSelf-Managing Skill Library]
    V82 --> V83A[V8.3 Track A\nCandidate 확장]
    V82 --> V83B[V8.3 Track B\n외부 Expert Catalog]
```

## 관련 Source of Truth

- `README.md`, `README_KO.md`
- `docs/DOCUMENTATION_POLICY.md`
- `docs/DEVELOPMENT.md`
- `V4_CHANGES_KO.md` ~ `V7_CHANGES_KO.md`
- `V8_1_ARCHITECTURE.md`
- `tasks/`
- `evaluation/external-skills/`
- `harness/`
- `.codex/AGENTS.md`
- `.agents/skills/`

이 기록은 위 파일들을 대체하지 않습니다. **현재 동작과 계약은 Repository Source of Truth가 우선**이며, 이 디렉터리는 그 결정이 만들어진 배경을 설명합니다.
