# V6 변경사항

v6는 v5의 기존 4개 Skill을 유지하면서 실제 장기 Codex 사용에서 분리된 두 개의 전역 Workflow Skill을 추가하고, GitHub 공개용 문서와 전역 규칙 구조를 정리한 버전입니다.

## 유지되는 기존 Skill

```text
$ai-agent-development-playbook
$human-readable-code
$human-centered-project-builder
$guide-ppt-creator
```

v5 배포본과 실제 전역 사용본을 비교한 결과, 위 4개 Skill의 내용은 동일했습니다. 따라서 v6에서는 기존 동작을 그대로 보존합니다.

## 신규 Skill 1: codex-long-run

긴 Repository 작업을 여러 구현/디버깅/검증 cycle 또는 여러 session에 걸쳐 이어가기 위한 orchestration Skill입니다.

핵심:

- minimum sufficient context
- Repository 기반 durable state
- stale state guard
- one coherent outcome
- focused verification budget
- meaningful checkpoint
- repository-based resume
- pause/stop handoff
- Evidence 기반 completion

작은 isolated edit에는 사용하지 않습니다.

## 신규 Skill 2: codex-task-router

충분히 정의된 software-engineering work unit에 대해 필요한 최소 충분한 Codex capability를 추천하는 Skill입니다.

판단 기준:

- Complexity
- Uncertainty
- Risk
- Project Criticality
- Architecture Impact
- Breadth
- Verification Difficulty
- Parallelizability
- Routing Confidence
- Cost Sensitivity

논리적 route:

```text
LIGHT
STANDARD
DEEP
CRITICAL
PARALLEL COMPLEX
```

이 Skill은 구현하지 않고 routing recommendation만 반환합니다.

구체 model/reasoning mapping은 시간이 지나면 바뀔 수 있으므로 현재 runtime/catalog 지원 여부를 확인하도록 설계되어 있습니다.

## Global AGENTS 개선

v6는 실제 사용 중 발전한 규칙을 공개 배포에 맞게 다시 정리했습니다.

추가/강화된 원칙:

- Problem → Requirements → Architecture → Task → Implementation → Verification
- Repository Source of Truth
- Task discipline
- Evidence 기반 completion
- Verification budget
- Human-readable code
- Hardware acceleration validation
- Autonomous Codex operation
- reusable workflow → Skill 승격 기준
- global policy budget
- 6개 Skill selection guide

개인 session 이름, 특정 날짜, 사용자 PC 경로 같은 개인 환경 정보는 공개용 전역 규칙에서 제거했습니다.

## 중요한 설치 구조 수정

실제 전역 `AGENTS.md`에서 발전한 규칙을 단순 복사하지 않고, 설치 스크립트가 실제 배포하는 다음 marker 내부로 통합했습니다.

```text
<!-- BEGIN AI_AGENT_PLAYBOOK_KIT -->
...
<!-- END AI_AGENT_PLAYBOOK_KIT -->
```

이렇게 해야 기존 사용자 전역 규칙을 보존하면서 Kit 규칙만 안전하게 추가/업데이트할 수 있습니다.

## GitHub 사용자 문서 추가

v6에는 GitHub에서 처음 보는 사용자도 따라갈 수 있도록 다음 문서를 추가합니다.

```text
README.md
docs/QUICKSTART.md
docs/HOW_IT_WORKS.md
docs/SKILLS.md
docs/DEVELOPMENT.md
```

`qwen-harness-test`와 비슷하게 README를 진입점으로 두고 목적별 상세 문서로 이동하는 구조입니다.

## v6 Skill 목록

```text
$ai-agent-development-playbook
$human-readable-code
$human-centered-project-builder
$guide-ppt-creator
$codex-long-run
$codex-task-router
```

## 버전 상태

현재 상태는 공식 `v6` Release입니다.

설치 구조, Manifest, 문서, 개인 정보 노출 여부, 기존 v5 호환성 및 Windows 설치/제거 E2E 검증을 완료한 뒤 main에 병합하고 v6로 확정했습니다.
