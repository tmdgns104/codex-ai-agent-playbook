# V7 변경사항 - Context Efficient Global Playbook

상태: **Release Candidate - Windows update/no-op verification passed**

브랜치:

```text
v7-context-efficient
```

## 목표

V7의 우선순위는 다음 두 가지입니다.

1. Codex가 모든 세션에서 반복해서 읽는 전역 컨텍스트를 줄인다.
2. 검증 신뢰성과 안전 경계는 낮추지 않는다.

즉, 단순히 문장을 짧게 만드는 버전이 아니라:

```text
항상 필요한 규칙 -> 전역 AGENTS.md
상황별 상세 절차 -> Skills
프로젝트별 사실 -> Repository
```

구조를 더 명확하게 만드는 버전입니다.

## 주요 변경

### 1. 전역 AGENTS.md 축소

V6 전역 `AGENTS.md`는 역할, 개발 절차, 검증, 가독성, GPU,
리스크, 자동 운용, Skill 정책 등을 모두 자세히 담고 있었습니다.

V7에서는 항상 필요한 원칙만 남기고 상세 절차를 Skills에 맡깁니다.

핵심 유지 항목:

- Repository Source of Truth
- 한 번에 하나의 coherent outcome
- 요구/아키텍처 임의 변경 금지
- Evidence 기반 완료
- Human Gate
- 최소 충분 Context
- 최소 Skill 선택
- 다음 독립 Task 자동 시작 금지

### 2. Context Budget 명시

전역 규칙에 다음 원칙을 추가했습니다.

- 필요한 파일/섹션부터 읽기
- 변경되지 않은 대형 파일/로그 반복 로드 금지
- 성공 로그는 핵심 Evidence만 요약
- Skills는 필요한 경우만 로드
- 긴 채팅 대신 Repository checkpoint 우선
- 정확성을 희생하는 토큰 절감 금지

### 3. codex-long-run 경량화

장기 작업 Skill을 다음 핵심 책임 중심으로 재구성했습니다.

```text
Orient
-> Outcome Contract
-> Small Implementation Loop
-> Focused Verification
-> Meaningful Checkpoint
-> Resume
-> Final Evidence
```

프로젝트별 기술/명령/아키텍처를 Skill에 중복 저장하지 않습니다.

### 4. codex-task-router 경량화 및 stale-model 방지

V6의 라우터는 현재 모델 이름과 Reasoning 수준을 표로 보관했습니다.

이 방식은 모델 카탈로그가 바뀔 때 전역 Playbook 자체가 오래된 정보가 될 수 있습니다.

V7에서는 영구 모델표를 제거하고 라우팅이 필요한 순간에만
현재 세션/제품/공식 문서에서 지원 조합을 확인합니다.

라우터는 여전히 다음 Safety Floor를 유지합니다.

```text
LIGHT
STANDARD
DEEP
CRITICAL
PARALLEL COMPLEX
```

### 5. Windows 설치 멱등화

기존 설치본과 Repository Skill 내용이 같으면:

- 재복사하지 않음
- 새 백업을 만들지 않음

실제 변경이 있을 때만 백업 후 교체합니다.

### 6. 백업 폴더를 Skill 검색 경로 밖으로 이동

V6 방식:

```text
~/.agents/skills/<skill>.backup-<timestamp>
```

문제:

백업 폴더 안에도 `SKILL.md`가 있으므로 Codex가 중복 Skill로 탐색할 가능성이 있습니다.

V7:

```text
~/.codex/playbook-backups/<timestamp>/
```

기존 `*.backup-*` 폴더도 설치 시 Skill 검색 경로 밖으로 이동합니다.

### 7. verify-install.ps1 추가

전역 설치 상태를 Repository와 비교합니다.

```powershell
.\verify-install.ps1
```

검사:

- 전역 `AGENTS.md` Playbook block 일치 여부
- 관리 Skill별 파일 fingerprint 일치 여부
- 누락 Skill
- drift
- Skill 검색 경로 안의 legacy backup 잔존 여부

결과:

```text
RESULT PASS
```

또는:

```text
RESULT FAIL
```

## 기대 효과

- 매 Codex 세션의 고정 전역 컨텍스트 감소
- 장기 작업에서 불필요한 재탐색/로그 반복 감소
- 라우팅 Skill의 유지보수 부담 감소
- Skill 중복 탐색 위험 감소
- GitHub 버전과 PC 전역 적용본의 drift를 명시적으로 검증 가능
- 업데이트를 반복 실행해도 불필요한 백업 누적 감소

## V7 Candidate 검증 항목

2026-08-22 Windows 실환경에서 V6 설치본을 V7으로 갱신하여 다음 핵심 경로를 확인했습니다.

- [ ] PowerShell 설치 신규 환경
- [x] V6 -> V7 업데이트
- [x] 동일 버전 재설치 시 no-op
- [x] legacy `*.backup-*` 이동
- [x] `verify-install.ps1` PASS
- [ ] 일부 Skill 수정 후 DRIFT 검출
- [ ] `AGENTS.md` 사용자 커스텀 영역 보존 E2E
- [ ] uninstall 후 사용자 커스텀 영역 보존 E2E
- [ ] 새 Codex 세션에서 6개 Skill 인식 확인

### Windows 실환경 Evidence

첫 업데이트에서:

```text
UPDATED  C:\Users\user\.codex\AGENTS.md
MOVED    legacy backup ...
BACKUP   skill 'codex-long-run'
INSTALLED skill 'codex-long-run'
BACKUP   skill 'codex-task-router'
INSTALLED skill 'codex-task-router'
...
RESULT   PASS
```

동일 버전을 즉시 다시 설치했을 때 모든 관리 항목이 `OK`였고 새 `BACKUP`/`INSTALLED`가 생성되지 않았습니다.

```text
OK       C:\Users\user\.codex\AGENTS.md
OK       skill 'ai-agent-development-playbook'
OK       skill 'codex-long-run'
OK       skill 'codex-task-router'
OK       skill 'guide-ppt-creator'
OK       skill 'human-centered-project-builder'
OK       skill 'human-readable-code'
...
RESULT   PASS
```

따라서 V7의 핵심 Windows 업데이트 경로, legacy backup migration, 설치 검증, 멱등 재설치는 실환경 Evidence를 확보했습니다.

## 적용

Windows CMD에서:

```cmd
git fetch origin
git switch v7-context-efficient
git pull origin v7-context-efficient
powershell -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

PowerShell에서는:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
.\verify-install.ps1
```

설치 후 새 Codex 세션에서 적용 상태를 확인합니다.
