# Development Guide

이 문서는 Codex AI Agent Playbook Kit 자체를 수정하거나 다음 버전으로 발전시킬 때 사용하는 가이드입니다.

## 기본 원칙

Playbook 자체도 일반 프로젝트와 같은 원칙을 따릅니다.

```text
Problem
→ Requirements
→ Architecture
→ Task
→ Implementation
→ Verification
```

새 규칙이나 Skill을 바로 추가하지 말고, 먼저 기존 책임과 중복되는지 확인합니다.

## Source of Truth

이 Repository에서는 다음을 중심으로 판단합니다.

- `.codex/AGENTS.md`: 전역 최소 규칙
- `.agents/skills/*/SKILL.md`: 역할별 상세 workflow
- 각 Skill의 `references/`, `scripts/`, `assets/`: 보조 자료
- `install.ps1`, `install.sh`: 설치 동작
- `uninstall.ps1`, `uninstall.sh`: 제거 동작
- `MANIFEST.txt`: 배포 파일 목록
- `README.md`, `docs/`: 사용자 문서
- `V*_CHANGES_KO.md`: 버전 변경 기록

## 전역 규칙 vs Skill vs Repository 규칙

새 규칙을 어디에 둘지 먼저 판단합니다.

### 전역 AGENTS.md에 둘 것
- 거의 모든 Repository에서 재사용됨
- 짧고 안정적인 원칙
- instruction context에 항상 있어도 비용 대비 가치가 큼

예:
- Repository Source of Truth
- Architecture 변경 Human Gate
- Evidence 기반 완료

### Skill에 둘 것
- 특정 종류의 작업에서만 필요
- 세부 절차가 길거나 자주 바뀜
- 모든 작업에 항상 로드할 필요가 없음

예:
- long-run resume workflow
- task capability routing
- PPT render/QA

### Repository에 둘 것
- 특정 프로젝트의 기술 stack, 명령, scope, architecture, acceptance criteria

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
5. 프로젝트 경로/개인 정보 없이 일반화 가능한가?
6. 실제 사용 또는 검증 Evidence가 있는가?

기존 Skill로 충분하면 새 Skill을 만들지 말고 기존 Skill을 확장합니다.

## Skill 작성 구조

최소 Skill은 `SKILL.md` 하나로 충분할 수 있습니다.

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

이유는 설치 스크립트가 marker 블록만 기존 사용자 `$HOME/.codex/AGENTS.md`에 추가하거나 교체하기 때문입니다.

marker 밖에 중요한 배포 규칙을 두면 Repository에는 존재하지만 실제 설치 사용자에게 적용되지 않는 오류가 생길 수 있습니다.

## 설치 스크립트 검증

v6의 설치 스크립트는 `.agents/skills` 하위 디렉터리를 순회하는 방식이므로 Skill 디렉터리를 추가하면 별도 목록 수정 없이 설치되는 구조입니다.

새 버전에서는 최소 다음을 확인합니다.

### Windows

- 기존 전역 `AGENTS.md`가 없는 경우 설치
- 기존 `AGENTS.md`가 있는 경우 marker block append
- marker가 이미 있으면 replace
- 기존 Skill 백업 생성
- 모든 배포 Skill 복사
- uninstall 시 Kit marker와 설치 Skill 제거

### Linux/macOS

동일한 의미가 `install.sh` / `uninstall.sh`에서 유지되는지 확인합니다.

## 공개 전 개인정보/환경 검사

다음은 공개 Repository에 넣지 않습니다.

- 사용자 이름이 포함된 로컬 경로
- API key/token/password
- 개인 이메일이나 계정 정보가 내용상 필요 없는 경우
- 특정 프로젝트 내부 정보
- transient log
- 개인 대화 날짜나 session 이름을 규칙 근거로 기록한 내용
- machine-specific cache/state

예제 경로는 `$HOME`, `%USERPROFILE%`, `<repo>`처럼 일반화합니다.

## 모델/도구 이름의 시간 의존성

`codex-task-router`처럼 현재 모델 catalog에 의존하는 Skill은 모델명을 영구 진리처럼 취급하면 안 됩니다.

- 현재 runtime/catalog 우선
- 공식 문서나 현재 지원 metadata로 재확인
- 지원되지 않는 조합을 추측하지 않음
- 논리적 route와 구체 model mapping을 분리

## 문서 갱신

사용자 경험이나 설치 구조가 바뀌면 함께 확인합니다.

- `README.md`
- `docs/QUICKSTART.md`
- `docs/HOW_IT_WORKS.md`
- `docs/SKILLS.md`
- `MANIFEST.txt`
- 해당 `V*_CHANGES_KO.md`

문서가 실제 설치 동작과 달라지지 않도록 합니다.

## 권장 Git 흐름

새 버전은 main을 바로 수정하기보다 branch에서 검증합니다.

예:

```powershell
git switch -c v7-candidate
```

작업 후:

```powershell
git diff --check
git status --short
```

변경 파일과 검증 결과를 확인한 다음 commit/push합니다.

## Release Gate

새 버전을 main에 병합하기 전에 최소 확인:

- Skill 목록이 의도한 것과 일치
- 전역 규칙이 marker 내부에 있음
- install/uninstall이 실제 구조와 일치
- `MANIFEST.txt` 최신
- 사용자 문서 최신
- 비밀값/개인 경로 없음
- Markdown 기본 형식 이상 없음
- 기존 vN 기능을 의도치 않게 잃지 않음

완료는 "문서가 좋아 보인다"가 아니라 실제 diff와 설치 구조 Evidence로 판단합니다.
