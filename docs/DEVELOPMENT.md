# Playbook 개발 가이드 - V8

이 문서는 Codex AI Agent Playbook 자체를 수정하거나 다음 버전으로 발전시킬 때 사용하는 기준입니다.

## 기본 원칙

Playbook 자체도 일반 프로젝트와 같은 원칙을 따릅니다.

```text
Problem
-> Requirements
-> Architecture
-> Task
-> Implementation
-> Verification
-> Evidence
```

새 규칙이나 Skill을 바로 추가하지 말고 먼저 기존 책임과 중복되는지 확인합니다.

## Source of Truth

이 Repository에서는 다음을 중심으로 판단합니다.

- `.codex/AGENTS.md`: 전역 최소 규칙
- `.agents/skills/*/SKILL.md`: 역할별 상세 workflow
- `harness/profiles/*.json`: MINIMAL/STANDARD/STRICT 검증 Profile
- `harness/quality/quality_gate.py`: 결정론적 Quality Gate
- `harness/security/harness_audit.py`: Playbook 자체 Audit
- `install.ps1`, `install.sh`: 설치/업데이트
- `verify-install.ps1`: Windows 전역 설치 drift 검증
- `uninstall.ps1`, `uninstall.sh`: 제거
- `MANIFEST.txt`: 배포 파일 목록
- `README.md`, `README_KO.md`, `docs/`: 사용자 문서
- `V*_CHANGES_KO.md`: 버전 변경/검증 기록

## 전역 규칙 vs Skill vs Repository 규칙

### 전역 AGENTS.md에 둘 것

- 거의 모든 Repository에서 재사용됨
- 짧고 안정적인 원칙
- 항상 Context에 있어도 비용 대비 가치가 큼

예:

- Repository Source of Truth
- Evidence 기반 완료
- Human Gate
- minimum sufficient context

전역 문서는 **커질수록 좋은 것이 아닙니다.**
새 규칙을 넣을 때는 영구 Context 비용을 먼저 고려합니다.

### Skill에 둘 것

- 특정 종류의 작업에서만 필요
- 세부 절차가 길거나 자주 바뀜
- 모든 작업에서 항상 읽을 필요가 없음

예:

- long-run resume workflow
- Skill routing
- capability routing
- PPT render/QA

### Harness에 둘 것

LLM 판단보다 결정론적 코드로 검사하는 편이 더 신뢰성 있고 저렴한 항목입니다.

예:

- diff whitespace
- conflict marker
- suspicious secret pattern
- profile JSON 구조
- Skill metadata
- MANIFEST coverage

### Repository에 둘 것

특정 프로젝트의 기술 stack, 명령, scope, architecture, acceptance criteria입니다.

예:

- Python version
- 특정 model/provider
- 특정 CI command
- 현재 Task scope

## 새 Skill 추가 기준

다음 질문에 대부분 YES일 때 새 Skill을 고려합니다.

1. 다른 Repository에서도 반복될 가능성이 있는가?
2. 기존 Skill의 책임과 명확히 다른가?
3. 전역 AGENTS.md에 넣기에는 너무 상세한가?
4. 독립적으로 호출했을 때 역할을 설명할 수 있는가?
5. 개인 경로나 프로젝트 비밀 없이 일반화 가능한가?
6. 실제 사용 또는 검증 Evidence가 있는가?
7. 기존 Skill을 확장하는 것보다 새 Skill이 Context를 더 줄이는가?

기존 Skill로 충분하면 새 Skill을 만들지 않습니다.

## Skill 작성 구조

최소 Skill은 `SKILL.md` 하나면 충분할 수 있습니다.

```text
.agents/skills/example-skill/
└─ SKILL.md
```

필요할 때만 확장합니다.

```text
example-skill/
├─ SKILL.md
├─ references/
├─ scripts/
└─ assets/
```

모든 Skill에 모든 폴더를 만들 필요는 없습니다.

## AGENTS.md 수정 규칙

배포되는 전역 규칙은 반드시 다음 marker 안에 있어야 합니다.

```text
<!-- BEGIN AI_AGENT_PLAYBOOK_KIT -->
...
<!-- END AI_AGENT_PLAYBOOK_KIT -->
```

설치 스크립트는 marker block만 사용자의 `$HOME/.codex/AGENTS.md`에 추가/교체합니다.
marker 밖 사용자 내용은 보존합니다.

V8에서는 uninstall 후에도 marker 밖 사용자 내용이 실제 Windows에서 보존되는 것을 확인했습니다.

## V8 설치 구조

전역 관리 대상:

```text
~/.codex/AGENTS.md
~/.agents/skills/<managed-skill>/
~/.codex/playbook-harness/
```

백업:

```text
~/.codex/playbook-backups/<timestamp>/
```

Skill 검색 경로 안에 backup directory를 만들지 않습니다.
`SKILL.md`가 들어 있는 backup이 중복 Skill로 발견되는 문제를 막기 위해서입니다.

## 설치 스크립트 검증

### Windows

최소 확인 항목:

- 기존 전역 AGENTS가 없는 경우 설치
- 기존 AGENTS에 marker가 없으면 append
- marker가 있으면 managed block만 replace
- 기존 사용자 marker 밖 내용 보존
- 7개 managed Skill 설치
- playbook harness 설치
- 변경 없는 재설치 no-op
- 실제 변경 시만 backup
- backup은 discovery path 밖에 저장
- `verify-install.ps1` fingerprint PASS
- Harness Audit PASS
- uninstall 후 사용자 영역 보존
- uninstall 후 재설치 가능

### Linux/macOS

`install.sh` / `uninstall.sh`도 의미상 같은 정책을 유지해야 합니다.

## Quality Gate 개발 규칙

`quality_gate.py`의 목적은 Repository 테스트를 대체하는 것이 아닙니다.

```text
Repository-defined test / build / acceptance
+
Deterministic supplemental checks
```

STRICT에서 필요한 실행 Evidence가 없으면 거짓 PASS 대신 `UNVERIFIED`를 유지합니다.

Exit code 계약:

```text
0 = PASS
1 = FAIL
2 = UNVERIFIED
```

이 계약을 변경하면 사용자 문서와 검증 시나리오도 같이 갱신해야 합니다.

## Harness Audit 개발 규칙

Audit에는 다음과 같은 **낮은 오탐률의 정적 검사**를 우선합니다.

- Global AGENTS size budget
- marker integrity
- Skill frontmatter/name/duplicate
- backup discovery hazard
- profile JSON schema 기본 구조
- Python syntax
- MANIFEST coverage/drift
- 재사용 파일의 명백한 개인 절대 경로/secret material

모호한 스타일 취향이나 LLM 판단을 필수 FAIL 조건으로 넣지 않습니다.

## 공개 전 개인정보/환경 검사

다음은 공개 Repository에 넣지 않습니다.

- 사용자 이름이 포함된 로컬 절대 경로
- API key/token/password
- 불필요한 개인 이메일/계정 정보
- 특정 비공개 프로젝트 내부 정보
- transient log
- 개인 session 이름이나 대화 기록
- machine-specific cache/state

예제 경로는 `$HOME`, `%USERPROFILE%`, `<repo>`처럼 일반화합니다.

## 모델/도구 이름의 시간 의존성

`codex-task-router`는 현재 제품 상태에 의존하므로 모델 이름/가격을 영구 진리처럼 하드코딩하지 않습니다.

- 현재 runtime/catalog 우선
- 필요 시 공식 문서 재확인
- 지원되지 않는 조합을 추측하지 않음
- 논리적 route와 실제 model mapping을 분리

## 문서 갱신

사용자 경험이나 설치 구조가 바뀌면 함께 확인합니다.

- `README.md`
- `README_KO.md`
- `docs/QUICKSTART.md`
- `docs/HOW_IT_WORKS.md`
- `docs/SKILLS.md`
- `docs/DEVELOPMENT.md`
- `MANIFEST.txt`
- 해당 `V*_CHANGES_KO.md`

문서가 실제 `main` 동작과 다르면 Release 완료로 보지 않습니다.

## 권장 Git 흐름

새 기능이나 큰 문서 개편은 `main`을 바로 수정하기보다 branch에서 검증합니다.

```cmd
git switch -c <candidate-branch>
```

작업 후:

```cmd
git diff --check
git status --short
```

Playbook 자체에는 추가로:

```cmd
python harness\security\harness_audit.py --root .
```

을 권장합니다.

고위험 변경이면 Quality Gate STRICT와 실제 verification command도 사용합니다.

## Release Gate

`main` 병합 전 최소 확인:

- managed Skill 목록이 의도한 것과 일치
- 전역 규칙이 marker 내부에 있음
- Global AGENTS Context budget 유지
- install/verify/uninstall이 실제 구조와 일치
- Harness profile/Quality/Audit 정합성
- `MANIFEST.txt` 최신
- README/docs가 현재 안정 버전을 가리킴
- 비밀값/개인 경로 없음
- negative-path 검증 필요 시 FAIL이 실제로 검출됨
- 기존 기능을 의도치 않게 잃지 않음

완료는 "문서가 좋아 보인다"가 아니라 실제 diff, 설치, 테스트, exit code Evidence로 판단합니다.
