# V8.2-SKILL-006 - Self-Managing Lifecycle Integration

상태: **APPROVED - NOT STARTED**

선행 조건:

- V8_2-SKILL-005 COMPLETE - VERIFIED

## 목적

Governance, Creator, Evolver, Curator를 기존 V8.1 Router/Activation/Launcher와 연결해 Self-Managing Skill Lifecycle을 실제 Windows workflow에서 검증합니다.

## 최종 흐름

```text
User Task
  |
  v
V8.1 Metadata Router
  |
  +--> Skill found --> Gate --> Activation --> Codex --> Verification --> Event
  |
  +--> No suitable Skill --> Gap Event --> Creator Candidate

Observed Events
  |
  +--> Evolver Proposal
  +--> Curator Proposal
           |
           v
      Skill Audit
           |
           v
      Regression
           |
           v
   Promotion/Human Gate
           |
           v
   Capability Library
```

## 통합 요구사항

### 1. Normal Task Cost

Self-Managing subsystem 때문에 정상 작업마다 Creator/Evolver/Curator LLM 작업을 실행하면 안 됩니다.

Normal path는 기존 V8.1과 동일하게 lightweight해야 합니다.

### 2. Event Recording

Task 종료 후 최소 event를 기록할 수 있습니다.

- selected Skill ids
- verification outcome
- task fingerprint
- correction marker if explicitly available

기록 실패가 정상 Codex task를 깨뜨리면 안 됩니다.

### 3. Maintenance Entry Point

권장 CLI 예:

```text
python harness/skills/manage.py audit
python harness/skills/manage.py gaps
python harness/skills/manage.py proposals
python harness/skills/manage.py validate <proposal-id>
python harness/skills/manage.py promote <proposal-id>
python harness/skills/manage.py curate
```

실제 CLI 이름은 구현 시 기존 naming과 정합성을 맞춥니다.

### 4. Human Gate

CLI는 Human Gate가 필요한 proposal을 자동 적용하지 않습니다.

상태 예:

```text
READY
VALIDATION_FAILED
HUMAN_GATE_REQUIRED
STALE_BASE
PROMOTED
REJECTED
```

### 5. Installer

필요한 governance code/data가 global installed harness에 포함되어야 한다면 `install.ps1`, `verify-install.ps1`, uninstall parity를 유지합니다.

Optional Skill은 여전히 global discovery path에 대량 설치하지 않습니다.

## Windows E2E

최소 실제 검증:

### E2E-1 Existing behavior

JWT regression task에서 기존 exact-3/STRICT behavior 유지.

### E2E-2 Gap

Known gap task -> no Skill auto-creation, Gap Event only.

### E2E-3 Creator

Gap -> Candidate package 생성 -> ACTIVE unchanged.

### E2E-4 Failed validation

negative fixture failure -> promotion blocked -> ACTIVE hash unchanged.

### E2E-5 Successful low-risk promotion

Synthetic low-risk candidate -> all checks PASS -> atomic promotion.

### E2E-6 Human Gate

permission expansion/split/merge/archive -> HUMAN_GATE_REQUIRED.

### E2E-7 Curator

oversized synthetic Skill -> compress/reference proposal, no silent ACTIVE mutation.

### E2E-8 Install/Reinstall

install -> verify -> same-version reinstall idempotent.

## Scaling Check

Synthetic registry metadata로 10/50/100/500/1000 Skill routing runtime을 측정합니다.

V8.2에서는 결과를 기록만 하고 Evidence 없이 semantic router를 추가하지 않습니다.

## Acceptance Criteria

1. Existing V8.1 normal task flow remains backward-compatible
2. Global AGENTS does not meaningfully grow for self-management
3. Normal path does not invoke Creator/Evolver/Curator automatically on every task
4. Gap Event integration works
5. Creator Candidate integration works
6. Evolver Proposal integration works
7. Curator Proposal integration works
8. Failed validation preserves ACTIVE hash/content
9. Low-risk validated promotion atomic PASS
10. Human Gate scenarios block auto promotion
11. protected routing regressions PASS
12. all V8.1 router tests PASS
13. all V8.1 activation/materializer/discovery/launcher tests PASS
14. new governance/creator/evolver/curator tests PASS
15. Skill Audit PASS
16. Harness Audit PASS
17. STRICT Quality Gate PASS
18. install/verify/reinstall Windows PASS
19. arbitrary target Git repository behavior PASS
20. final working tree clean

## V8.2 완료 후

이 Task까지 COMPLETE - VERIFIED가 된 뒤 Optional Skill Batch 2 이상의 대량 확장을 진행합니다.

V8.3+ 후보:

- semantic/embedding candidate retrieval
- background maintenance scheduling
- automated external source ingestion
- richer utility/cost dashboard
- multi-agent evolution experiments

## 완료 조건

실제 Windows Evidence 전 `COMPLETE - VERIFIED` 금지.
