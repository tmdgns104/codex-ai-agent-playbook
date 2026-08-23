# V8.2 Self-Managing Skill Library - Requirements

상태: **DESIGN APPROVED - IMPLEMENTATION NOT STARTED**

## 1. 목적

V8.1의 Dynamic Capability Library를 확장해 Skill을 많이 보유하면서도 다음을 동시에 달성합니다.

- 필요한 Skill이 없으면 재사용 가치가 있는 경우 새 Candidate를 만든다.
- 실제 작업 Evidence를 바탕으로 기존 Skill을 점진적으로 개선한다.
- Skill이 커지거나 책임이 섞이면 축소, reference 추출, split을 제안한다.
- 유사 Skill은 merge 후보로 관리하고 저가치 Skill은 archive 후보로 관리한다.
- Library가 수십~수백 개로 커져도 Global Context는 증가시키지 않는다.
- 자동 성장은 항상 Audit, Regression, Permission/Human Gate 아래에서만 일어난다.

핵심 원칙:

```text
Library는 성장할 수 있다.
Active Skill은 검증 없이 자가수정하지 않는다.
Global Context는 성장시키지 않는다.
판정 가능한 것은 deterministic code가 담당한다.
의미 해석이 필요한 것만 LLM이 제안한다.
```

## 2. 기존 V8.1 계약

다음 계약은 유지해야 합니다.

- Core Skill은 `.agents/skills/`에 유지한다.
- Optional Skill은 `capability-library/skills/optional/`에 저장한다.
- Router는 metadata-first deterministic routing을 기본으로 한다.
- 기본 선택 수는 0~3개다.
- Optional Skill 본문은 선택 전에는 로드하지 않는다.
- Permission/Risk Gate를 우회하지 않는다.
- Task-scoped materialization/discovery/cleanup을 유지한다.
- `.codex/AGENTS.md`를 Self-Managing 기능 때문에 비대화하지 않는다.

## 3. 기능 요구사항

### R-001 Governance Foundation First

Creator/Evolver/Curator보다 먼저 공통 Governance 기반을 구현해야 합니다.

포함:

- Skill lifecycle state
- version/proposal/evidence 모델
- deterministic `skill_audit.py`
- safe promotion/rollback 규칙
- concurrency/lock 규칙
- Human Gate 분류

### R-002 Gap Event

Router가 적절한 Skill을 찾지 못했다고 즉시 새 Skill을 만들면 안 됩니다.

먼저 `gap event`를 기록합니다.

Gap Event에는 최소 다음을 저장합니다.

- task fingerprint 또는 redacted task summary
- router result
- selected capabilities
- missing capability hypothesis
- timestamp
- project-local context 여부

민감정보, credential, 전체 사용자 입력을 장기 저장하지 않습니다.

### R-003 Skill Creator

새 Skill은 다음 조건을 만족할 때만 Candidate로 생성할 수 있습니다.

1. 기존 Skill 확장만으로 해결하기 어렵다.
2. 특정 Repository에만 종속되지 않는 반복 가능한 Workflow가 있다.
3. 최소 2개 이상의 representative positive case를 만들 수 있다.
4. 최소 1개 이상의 negative case를 만들 수 있다.
5. 기존 Skill과 역할 중복이 허용 범위 내다.
6. source/provenance/license를 기록할 수 있다.

새 Candidate는 바로 ACTIVE가 되면 안 됩니다.

### R-004 Skill Evolver

ACTIVE Skill은 직접 수정하지 않습니다.

```text
ACTIVE vN
  -> observed evidence
  -> proposal
  -> CANDIDATE vN+1
  -> audit/regression
  -> promote or reject
```

Evolver는 다음 Evidence를 입력으로 사용할 수 있습니다.

- task success/failure
- verification result
- user correction
- repeated workaround
- false positive / false negative routing
- missing step pattern

한 번의 단발성 실패만으로 Skill을 수정하지 않는 것을 기본으로 합니다.

### R-005 Skill Curator

Curator는 Library 전체를 관리하며 다음 제안 타입을 지원합니다.

- `compress`
- `extract-reference`
- `split`
- `merge`
- `trigger-narrow`
- `trigger-expand`
- `archive`
- `restore`

`delete`는 V8.2 자동 동작 범위에서 제외합니다.

### R-006 Skill Structure Hygiene

SKILL.md는 핵심 판단과 실행 절차만 유지합니다.

세부 예제/긴 표/도메인별 명령어/템플릿/반복 스크립트는 필요 시 다음으로 이동할 수 있습니다.

```text
references/
scripts/
templates/
assets/
```

Curator는 package 단위 무결성을 유지해야 하며 SKILL.md만 떼어내 support file 링크를 깨뜨리면 안 됩니다.

### R-007 Deterministic Audit

`harness/quality/skill_audit.py`는 LLM 없이 최소 다음을 검사해야 합니다.

- schema/frontmatter/path consistency
- duplicate id
- source/license/provenance
- permission declaration
- Optional Skill discovery isolation
- SKILL.md byte/line budget
- broken relative references
- trigger exact overlap
- suspicious broad trigger
- obvious secret/personal path
- executable/script presence and declaration
- lifecycle/version consistency
- positive/negative routing fixture presence

출력 계약:

```text
PASS
WARN
FAIL
```

FAIL은 promotion을 막습니다.

### R-008 Human Gate

다음 변경은 자동 promotion 금지입니다.

- permission 확대
- network/credential/external-write/database-write/destructive/production 추가
- trigger 범위 확대
- Skill split/merge
- archive
- Core Skill 승격/강등
- 외부 실행 script 추가
- lifecycle 정책 자체 변경

### R-009 Provenance

외부 Skill은 신뢰하지 않는 입력으로 취급합니다.

외부 Skill 흡수 기본 절차:

```text
source inspect
-> license inspect
-> untrusted content scan
-> useful pattern extraction
-> Codex Playbook용 재작성
-> candidate
-> audit/regression
-> promotion
```

원문 wholesale copy를 기본 동작으로 하지 않습니다.

### R-010 Metrics

다음 지표를 수집할 수 있어야 합니다.

- routing selected count
- true/false activation evidence
- Skill usage count
- successful verified usage count
- failure count
- last used
- proposal count
- promotion/rejection count
- SKILL.md bytes/lines
- support file count
- trigger overlap
- context cost class
- selected Skill body bytes

실제 token 수가 플랫폼에서 신뢰성 있게 노출되지 않으면 추정치를 PASS/FAIL 근거로 사용하지 않습니다.

### R-011 Threshold Policy

초기 숫자는 hard policy가 아니라 soft warning baseline으로 둡니다.

예:

- SKILL.md soft size warning
- trigger overlap warning
- low-usage review candidate
- repeated failure review candidate

실사용 데이터가 쌓이기 전 `30일 미사용=archive`, `Precision 80%=PASS` 같은 값을 고정 정책으로 만들지 않습니다.

### R-012 Lifecycle

V8.2 lifecycle:

```text
CANDIDATE
  -> VALIDATING
      -> REJECTED
      -> ACTIVE

ACTIVE
  -> REVIEW_REQUIRED
  -> ACTIVE (new version promoted)
  -> STALE
  -> ARCHIVED

ARCHIVED
  -> CANDIDATE (restore proposal)
  -> ACTIVE (validated restore)
```

`EVOLVING`을 ACTIVE Skill의 mutable state로 사용하지 않습니다. 개선 중에도 현재 ACTIVE version은 불변입니다.

### R-013 Versioning / Rollback

Skill 변경은 proposal 단위로 추적합니다.

최소 정보:

- proposal_id
- skill_id
- base_version/base_hash
- proposed_version
- reason
- evidence refs
- change type
- permission delta
- trigger delta
- audit result
- regression result
- promotion status

Promotion 실패 시 ACTIVE version은 바뀌지 않습니다.

### R-014 Concurrency

동일 Skill에 동시에 여러 proposal이 적용되면 안 됩니다.

V8.2 MVP는 file lock 또는 atomic lock record를 사용하고 다음을 보장합니다.

- one writer per skill
- stale lock recovery
- base hash mismatch rejection
- atomic registry update

### R-015 Scale

V8.2에서는 현재 deterministic metadata Router를 유지합니다.

확장 전략은 Evidence가 있을 때만 단계적으로 적용합니다.

```text
small/medium library
-> current metadata router

routing degradation observed
-> domain prefilter / inverted metadata index

larger library with measured recall problem
-> two-stage retrieval

semantic retrieval
-> only after deterministic approach becomes insufficient
```

Embedding/Vector DB는 V8.2 MVP 필수사항이 아닙니다.

## 4. 비기능 요구사항

### NFR-001 Context

Self-Managing 기능 때문에 Global `.codex/AGENTS.md` 크기를 의미 있게 증가시키면 안 됩니다.

### NFR-002 Determinism

가능한 검증/상태전이는 Python 기반 deterministic code를 우선합니다.

### NFR-003 Safety

Skill이 자신의 검증 규칙, permission, audit 결과를 스스로 수정해 승격할 수 없어야 합니다.

### NFR-004 Auditability

모든 promotion/split/merge/archive 제안은 Git diff와 Evidence로 추적 가능해야 합니다.

### NFR-005 Windows First

현재 실제 운영 환경인 Windows CMD/PowerShell에서 검증 가능한 CLI를 제공해야 합니다.

### NFR-006 Backward Compatibility

기존 V8.1 launcher/router/materializer/discovery/install/uninstall 동작을 깨뜨리지 않아야 합니다.

## 5. V8.2 MVP 범위

V8.2에서 구현:

1. Governance Foundation
2. `skill_audit.py`
3. lifecycle/proposal/evidence storage
4. Gap Event
5. Skill Creator Candidate generation contract
6. Skill Evolver proposal contract
7. Skill Curator proposal contract
8. deterministic promotion gate
9. Windows regression

V8.3+로 보류:

- 완전 자동 background evolution
- embedding/vector search
- autonomous external web ingestion
- automatic split/merge promotion
- automatic archive without human approval
- multi-agent parallel evolutionary search
- large telemetry dashboard

## 6. 참고 패턴

설계 원칙을 추출한 주요 공개 참고:

- OpenSkill - open-world skill generation/evolution
- SkillEvolver - artifact-level adaptation and independent auditor
- Hermes Agent Curator - usage-aware stale/archive/consolidation pattern
- SkillAudit - utility/efficiency/safety 중심 skill evaluation
- ECC context-budget - context cost visibility and bloat detection

이 Repository에서는 해당 프로젝트를 그대로 복제하지 않고 V8.1의 deterministic-first, minimal-context, Human Gate 규칙에 맞게 재설계합니다.
