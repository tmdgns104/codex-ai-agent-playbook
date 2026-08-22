# Codex AI Agent Playbook

Codex를 **적은 고정 컨텍스트, 필요한 Skill만 선택하는 구조, 실제 Evidence 기반 검증**으로 운용하기 위한 경량 Playbook + Skills + Harness입니다.

> 현재 안정 버전: **V8 — `main`**  
> Windows 실환경 검증 완료 / GitHub `main` 병합 완료

상세 설명: [README_KO.md](README_KO.md)

## 왜 만들었나

Codex를 오래 사용하다 보면 다음 문제가 생길 수 있습니다.

- 전역 지침이 커져 매 작업마다 불필요한 Context를 소비함
- 모든 Skill을 읽어 단순 작업도 무거워짐
- Agent가 스스로 PASS라고 말한 것을 검증으로 착각함
- 작은 수정과 고위험 변경에 같은 검증 비용을 씀
- 긴 작업에서 Chat history에 의존해 상태가 흔들림

V8은 이를 다음 구조로 줄입니다.

```text
사용자 요청
  ↓
필요한 경우에만 Skill Router
  ↓
최소 Skill 집합 선택
  ↓
MINIMAL / STANDARD / STRICT
  ↓
구현
  ↓
Repository Verification
  ↓
Deterministic Quality Gate
  ↓
PASS / UNVERIFIED / FAIL
```

## V8 핵심 기능

### 1. 짧은 Global AGENTS.md

항상 주입되는 전역 규칙은 최소한만 유지합니다.

상세 절차는 필요한 순간에만 Skill로 읽습니다.

```text
항상 필요한 원칙 -> .codex/AGENTS.md
상황별 상세 절차 -> .agents/skills/
프로젝트 사실/상태 -> 각 Repository
```

V8은 Skill Router와 검증 Profile을 추가했지만 전역 AGENTS 크기를 V7 수준 이하로 유지했습니다.

### 2. 7개 Skill + 최소 선택 원칙

```text
codex-skill-router
ai-agent-development-playbook
codex-long-run
codex-task-router
guide-ppt-creator
human-centered-project-builder
human-readable-code
```

원칙은 **7개를 전부 사용하는 것이 아니라 현재 작업에 필요한 최소 Skill만 사용하는 것**입니다.

### 3. 위험도 기반 검증 Profile

- `MINIMAL` — 작고 격리된 저위험 변경
- `STANDARD` — 일반적인 비단순 개발
- `STRICT` — 보안, 권한, 배포, 마이그레이션, 파괴적 변경, 중요 Architecture/Public Contract 변경

### 4. Deterministic Quality Gate

```cmd
python "%USERPROFILE%\.codex\playbook-harness\quality\quality_gate.py" --repo . --profile standard
```

STRICT에서 실제 검증 Evidence가 필요한데 `--verify`가 없다면 거짓 PASS 대신:

```text
RESULT     UNVERIFIED
```

을 반환합니다.

Exit code:

```text
0 = PASS
1 = FAIL
2 = UNVERIFIED
```

### 5. Harness Audit

Playbook 자체도 검사합니다.

```cmd
python harness\security\harness_audit.py --root .
```

전역 Context 크기, Skill metadata, profile JSON, MANIFEST, backup discovery 문제, Python 문법, 명백한 secret 패턴 등을 점검합니다.

## 설치 — Windows CMD

```cmd
git clone https://github.com/tmdgns104/codex-ai-agent-playbook.git
cd codex-ai-agent-playbook
powershell -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

이미 내려받은 Repository가 있다면:

```cmd
git switch main
git pull origin main
powershell -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

설치 후 자동 검증이 실행됩니다.

직접 다시 확인:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\verify-install.ps1"
```

정상 예:

```text
PASS     global AGENTS.md playbook block
PASS     skill 'codex-skill-router'
PASS     ...
PASS     playbook harness
PASS     harness audit
RESULT   PASS
```

## 전역 설치 위치

```text
%USERPROFILE%\.codex\AGENTS.md
%USERPROFILE%\.agents\skills\<managed-skill>\
%USERPROFILE%\.codex\playbook-harness\
```

백업은 Skill 검색 경로 밖에 저장됩니다.

```text
%USERPROFILE%\.codex\playbook-backups\<timestamp>\
```

동일 버전을 다시 설치하면 변경이 없는 항목은 `OK`로 끝나며 불필요한 백업/재복사를 만들지 않습니다.

## 실제 Windows에서 확인한 V8 동작

- V7 → V8 업데이트 PASS
- 7개 Skill 전역 설치 PASS
- playbook harness 설치/fingerprint PASS
- Harness Audit warnings 0 / PASS
- 동일 V8 재설치 no-op PASS
- MINIMAL → PASS
- STRICT + 검증 없음 → UNVERIFIED / exit 2
- STRICT + 실제 검증 → PASS
- conflict marker + 가짜 GitHub token → FAIL / exit 1
- uninstall 시 사용자 소유 AGENTS 내용 보존
- uninstall 후 V8 재설치 및 전체 검증 PASS

자세한 기록: [V8_CHANGES_KO.md](V8_CHANGES_KO.md)

## 의도적으로 넣지 않은 것

V8 Core에는 다음을 기본 의존성으로 넣지 않습니다.

- LangChain / LlamaIndex
- 상시 Multi-Agent
- 자동 Skill/Instinct 승격
- Claude 전용 Hook의 억지 호환 계층

필요성이 실제 사용 Evidence로 확인되기 전까지 Core를 가볍게 유지합니다.

## 문서

- [상세 한글 가이드](README_KO.md)
- [빠른 시작](docs/QUICKSTART.md)
- [동작 원리](docs/HOW_IT_WORKS.md)
- [Skills 가이드](docs/SKILLS.md)
- [Playbook 개발 가이드](docs/DEVELOPMENT.md)
- [V8 변경사항 및 검증 기록](V8_CHANGES_KO.md)
- [V7 변경사항](V7_CHANGES_KO.md)

## 핵심 원칙

```text
적은 영구 Context
+ 최소 Skill 선택
+ 위험도에 맞는 검증
+ Repository Source of Truth
+ 실제 Evidence
- 불필요한 Agent 계층
- 자기보고 PASS
```

토큰 절감이 정확성이나 검증 신뢰성을 낮추는 방식이면 채택하지 않습니다.
