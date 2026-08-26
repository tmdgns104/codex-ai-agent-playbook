# V8 변경사항 - Harness Core

상태: **Released / Verified**

현재 안정 브랜치:

```text
main
```

V8 개발 브랜치:

```text
v8-harness-core
```

GitHub `main` 병합 commit:

```text
3d18991 V8: add context-aware routing and deterministic harness gates
```

## 2026-08-25 후속 Experimental / Release Candidate 상태

이 문서의 V8 Harness Core와 `main`의 안정 상태는 그대로 유지됩니다. 후속 연구는
`v8.3-expert-skill-catalog` branch에서만 진행했으며 global rollout은 승인되지 않았습니다.

### V8.3 완료

- pinned external Expert Skill catalog와 Stage B benchmark를 완료했습니다.
- Wave 2에서 adapted-playbook은 5/5 fixture PASS, 전체 비교는 8 PASS/12 FAIL이었습니다.
- 이 결과는 단일 모델, 고정 fixture, validator/output contract 변화가 포함된 실험이므로
  다른 모델이나 실제 작업으로의 일반화를 확정하지 않습니다.
- 별도 DNN 실전 실험은 탐색적 보조 실험이며 V8.3/V8.4 본선 acceptance Evidence가 아닙니다.

### V8.4-001~006 완료

- 001: task-scoped Adapted Capability Context 설계
- 002: versioned opt-in launch contract와 transport 경계 결정
- 003: schema, canonical hash, deterministic validator와 fake backend fixtures
- 004: pinned snapshot offline compiler와 provenance/permission 검증
- 005: approved-only selector와 context budget planner
- 006: session-local materializer, pre-launch coordinator, lifecycle, cleanup/quarantine

V8.4-006 최종 회귀는 245 PASS/0 FAIL이지만 실제 Codex backend나 transport를 실행한
결과가 아닙니다. 현재 `kd-sympy`와 `kd-citation-management` compiler output도 `DRAFT`
상태이며 자동 승인하지 않습니다.

### 미완료와 rollout blocker

- V8.4-006A: 실제 Codex transport 검증 미구현
- V8.4-007: Native Codex vs Current Playbook vs Adapted Context 통제 비교 미수행
- 실제 backend capability와 context separation/injection invariant 미검증
- 반복 실행, 복수 모델, 실제 task에 대한 일반화 Evidence 부족

따라서 V8.4는 **Experimental / Release Candidate**이며 **Global rollout: NOT APPROVED**입니다.
상세 상태와 rollback 방향은
[`docs/V8.4_RELEASE_CANDIDATE_STATUS.md`](docs/V8.4_RELEASE_CANDIDATE_STATUS.md)를 참고하세요.

## 목표

V8은 Everything Claude Code/Claude Code 계열에서 다음 운영 패턴만 선별해 Codex 친화적으로 흡수합니다.

1. 필요할 때만 Skill을 선택하는 Progressive Disclosure
2. 작업 위험도에 따라 검증 강도를 조절하는 Profile
3. LLM 자기보고가 아닌 결정론적 Quality Gate
4. Harness 자체를 검사하는 경량 Audit

V7의 최우선 원칙인 **낮은 고정 컨텍스트 + Evidence 기반 완료**는 유지합니다.

## V8에 포함된 P0

### P0-1. Context-aware Skill Router

```text
.agents/skills/codex-skill-router/SKILL.md
```

라우터는 애매한 비단순 작업에서만 사용합니다.

출력:

- 최소 Skill 집합
- MINIMAL/STANDARD/STRICT Profile
- Long-run 여부
- Capability Router 여부
- Human Gate 여부

명확한 단일 Skill 작업이나 작은 수정에는 호출하지 않습니다.

### P0-2. Verification Profiles

```text
harness/profiles/minimal.json
harness/profiles/standard.json
harness/profiles/strict.json
```

- MINIMAL: 저위험/격리/쉬운 검증
- STANDARD: 일반적인 비단순 개발
- STRICT: 보안, 권한, 마이그레이션, 배포, 중요한 아키텍처/공개 계약, 파괴적 작업 등

### P0-3. Deterministic Quality Gate

```text
harness/quality/quality_gate.py
```

검사:

- unstaged/staged `git diff --check`
- unresolved conflict
- conflict marker
- changed/untracked file count
- STANDARD/STRICT suspicious-secret scan
- 명시적인 Repository verification command

STRICT에서 `--verify`가 없으면 PASS가 아니라 `UNVERIFIED`입니다.

Exit code:

```text
0 PASS
1 FAIL
2 UNVERIFIED
```

### P0-4. Harness Audit

```text
harness/security/harness_audit.py
```

검사:

- Global AGENTS.md size budget
- marker integrity
- permanent global context의 현재 모델명 hardcoding
- Skill frontmatter/name/중복
- Skill discovery path 안의 backup
- 큰 SKILL.md 경고
- Profile JSON 구조
- Harness Python syntax
- MANIFEST coverage/drift
- reusable Skill/AGENTS의 개인 절대 경로 및 명백한 secret material

## 전역 설치 구조

V8부터 Harness 파일도 전역에 설치됩니다.

```text
~/.codex/playbook-harness/
```

Windows와 shell installer 모두:

- 변경이 없으면 no-op
- 실제 변경이 있을 때만 backup
- backup은 Skill discovery path 밖에 저장
- Harness도 fingerprint 비교

Windows `verify-install.ps1`는 다음을 확인합니다.

- Global AGENTS block
- 모든 managed Skill
- playbook-harness
- legacy backup 잔존
- Python 사용 가능 시 Harness Audit

## 의도적으로 제외

V8 Core에는 다음을 넣지 않습니다.

### LangChain / LlamaIndex

이 저장소는 Agent 애플리케이션 runtime이 아니라 Codex 운영 Harness입니다.
Core dependency로 넣으면 책임 계층과 유지보수 비용이 커집니다.

### 상시 Multi-Agent

작은 작업에도 Planner/Coder/Reviewer 등을 항상 실행하는 구조는 토큰 비용이 큽니다.
필요하면 기존 `codex-task-router`의 Parallel 판단을 후속 P1에서 확장합니다.

### 자동 Learning / Instinct 승격

잘못된 패턴이 자동으로 전역 규칙이 되는 위험이 있어 P1 Candidate Learning으로 분리합니다.
Human 승인 없는 자동 Skill 승격은 하지 않습니다.

### Claude-specific Hooks 복제

Codex에 동일한 lifecycle API가 있다고 가정하지 않습니다.
Hook의 목적은 MINIMAL/STANDARD/STRICT 검증 Profile과 결정론적 Gate로 번역합니다.

## 실제 Windows 검증 결과

2026-08-22 대상 Windows PC에서 확인:

- [x] V7 -> V8 update
- [x] 새 `codex-skill-router` 전역 설치
- [x] `~/.codex/playbook-harness` 설치
- [x] `verify-install.ps1` RESULT PASS
- [x] Harness Audit RESULT PASS / warnings 0
- [x] 동일 V8 재설치 no-op
- [x] Quality Gate MINIMAL PASS
- [x] Quality Gate STRICT + verify PASS
- [x] Quality Gate STRICT + no verify -> UNVERIFIED / exit 2
- [x] deliberate conflict/secret fixture -> FAIL / exit 1
- [x] negative fixture 삭제 후 Git working tree clean
- [x] uninstall 후 사용자 소유 AGENTS 영역 보존
- [x] uninstall 후 V8 재설치 및 최종 `verify-install.ps1` RESULT PASS
- [x] 로컬 `main`, `origin/main`, `origin/HEAD`가 V8 merge commit으로 정렬

Negative fixture는 검증 후 삭제했습니다.
Uninstall 검증에서는 사용자 소유 테스트 문구가 남고 managed AGENTS block, 7개 Skill, playbook harness만 제거되는 것을 확인했습니다.
최종 재설치 후 Global AGENTS, 7개 Skill, playbook harness, Harness Audit가 모두 PASS했습니다.

## Context Budget 결과

V8은 기능을 늘리면서 전역 `AGENTS.md`를 다시 비대하게 만들지 않았습니다.

Repository 기준 전역 AGENTS 크기는 V7 수준 이하로 유지했고,
Windows CRLF working copy에서도 Harness Audit size budget을 통과했습니다.

즉 V8의 목표는 다음입니다.

```text
기능 증가
!= 항상 읽는 Context 증가
```

상세 절차는 Skills/Harness로 밀어내고 필요할 때만 사용합니다.

## V8 이후 P1 후보

P0의 실사용 결과를 본 뒤에만 검토합니다.

1. Candidate Learning
   - 반복 성공 패턴을 candidate로만 기록
   - Evidence 누적 후 Human 승인으로 Skill 승격
2. Conditional subagent review
   - 고위험/병렬 가능한 작업에서만 별도 verifier/reviewer 사용
3. Worktree parallel policy
   - 독립 workstream이 명확할 때만 병렬화
4. Routing/Quality eval dataset
   - V7/V8 A-B 비교를 위한 고정 task set

P1 기능을 바로 Core에 추가하지 않습니다.
실제 V8 작업에서 Router/Profile의 오버헤드와 효과를 먼저 확인합니다.

## 성공 기준

V8은 기능 수가 많아졌다는 이유로 성공이 아닙니다.

성공은 다음을 동시에 만족해야 합니다.

- 평소 고정 컨텍스트가 크게 증가하지 않음
- 불필요 Skill 로딩 감소
- 일반 작업에서 과도한 검증 오버헤드 없음
- 고위험 작업의 검증 누락 감소
- 설치/업데이트/rollback 신뢰성 유지
- 기존 V7보다 완료 정확성 또는 Evidence 품질이 좋아짐

이 항목들의 설치/검증 계약은 실제 Windows에서 검증한 뒤 `main`에 병합했습니다.
