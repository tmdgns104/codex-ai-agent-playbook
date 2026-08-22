# Codex AI Agent Playbook Kit

Codex를 **더 적은 고정 컨텍스트와 더 강한 검증 루프**로 여러 프로젝트에서 일관되게 사용하기 위한 전역 Playbook + Skills + Harness 세트입니다.

현재 개발 버전: **V8 Candidate (`v8-harness-core`)**

## 핵심 구조

```text
.codex/AGENTS.md
  항상 필요한 최소 전역 원칙

.agents/skills/
  ai-agent-development-playbook/
  codex-long-run/
  codex-task-router/
  codex-skill-router/
  guide-ppt-creator/
  human-centered-project-builder/
  human-readable-code/

harness/
  profiles/
    minimal.json
    standard.json
    strict.json
  quality/quality_gate.py
  security/harness_audit.py

install.ps1 / install.sh
  전역 설치/업데이트

verify-install.ps1
  Repository와 Windows 전역 설치 상태 비교 + Harness Audit
```

Windows 전역 설치 위치:

```text
%USERPROFILE%\.codex\AGENTS.md
%USERPROFILE%\.agents\skills\<skill-name>\
%USERPROFILE%\.codex\playbook-harness\
```

---

# V8 핵심 변경

V8은 Everything Claude Code/Claude Code 계열의 장점 중 **Codex에 맞고 토큰 대비 효과가 큰 운영 패턴만** 흡수합니다.

LangChain/LlamaIndex 같은 Agent 애플리케이션 프레임워크를 Playbook Core에 추가하지 않습니다.
상시 멀티에이전트도 기본값으로 사용하지 않습니다.

목표:

```text
User Request
  -> 최소 Skill 선택
  -> MINIMAL / STANDARD / STRICT 프로필
  -> Implementation
  -> Repository Verification
  -> Deterministic Quality Gate
  -> Evidence
```

## 1. Context-aware Skill Routing

새 Skill:

```text
$codex-skill-router
```

Skill 선택이 애매한 비단순 작업에서만 사용합니다.

라우터는:

- 필요한 최소 Skill 집합
- `MINIMAL / STANDARD / STRICT` 검증 프로필
- long-run 필요 여부
- capability router 필요 여부
- Human Gate 필요 여부

만 추천하고 구현은 하지 않습니다.

명확한 작업에는 라우터를 호출하지 않습니다.

예:

```text
오타 한 줄 수정
-> Skill 없음

가독성 리팩터링
-> human-readable-code

복잡한 RAG 아키텍처 변경
-> ai-agent-development-playbook
-> 필요하면 codex-long-run
```

## 2. Risk-based Verification Profiles

### MINIMAL

명확하고 격리된 저위험 변경.

### STANDARD

일반적인 비단순 개발의 기본값.

### STRICT

보안/권한/마이그레이션/배포/중요 아키텍처/파괴적 변경 등 고위험 작업.

강한 모델을 쓰는 것과 검증 강도는 별개입니다.

## 3. Deterministic Quality Gate

Repository에서 직접 실행:

```powershell
python "$HOME\.codex\playbook-harness\quality\quality_gate.py" --repo . --profile standard
```

STRICT 예:

```powershell
python "$HOME\.codex\playbook-harness\quality\quality_gate.py" `
  --repo . `
  --profile strict `
  --verify "python -m pytest"
```

검사 항목:

- `git diff --check`
- staged diff whitespace
- unresolved conflict
- conflict marker
- 변경 파일 수 경고
- STANDARD/STRICT의 suspicious-secret scan
- 명시적으로 전달된 repository verification command

STRICT에서 실행 Evidence가 필요한데 `--verify`가 없으면:

```text
RESULT     UNVERIFIED
```

으로 끝납니다.

Quality Gate는 Repository 테스트/Acceptance Criteria를 대체하지 않고 **보조 Evidence**로 사용합니다.

## 4. Harness Audit

Playbook 자체 검증:

```powershell
python .\harness\security\harness_audit.py --root .
```

검사 항목:

- 전역 `AGENTS.md` 크기 예산
- 마커 무결성
- 전역 문서의 현재 모델명 hardcoding
- Skill frontmatter/name 중복
- Skill 검색 경로 안의 backup 폴더
- 과도하게 큰 SKILL.md 경고
- profile JSON 구조
- Harness Python syntax
- MANIFEST drift
- 재사용 문서의 개인 절대 경로/명백한 secret material

목적은 ECC AgentShield를 복사하는 것이 아니라 **이 Playbook에 필요한 정적 하네스 감사만 경량으로 구현**하는 것입니다.

---

# V7에서 유지되는 개선

- 전역 `AGENTS.md` 경량화
- Repository Source of Truth
- Progressive Disclosure Skills
- 고정 모델표 제거
- Windows 설치 멱등화
- Skill 백업을 검색 경로 밖으로 이동
- `verify-install.ps1` 기반 drift 검증

V8은 이 구조를 버리지 않고 위에 Quality/Route 계층만 추가합니다.

---

# Windows 설치 / 업데이트

V8 Candidate 테스트:

```powershell
cd <codex-ai-agent-playbook 폴더>

git status --short
git fetch origin
git switch v8-harness-core
git pull origin v8-harness-core

Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

CMD에서 실행한다면:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

설치 후 `verify-install.ps1`가 자동 실행됩니다.

직접 확인:

```powershell
.\verify-install.ps1
```

정상 상태:

```text
PASS     global AGENTS.md playbook block
PASS     skill '...'
PASS     playbook harness
...
RESULT   PASS
```

동일 버전을 다시 설치했을 때 변경이 없다면 새 백업/재복사를 만들지 않습니다.

---

# 포함 Skills

| Skill | 용도 |
| --- | --- |
| `codex-skill-router` | 애매한 비단순 작업의 최소 Skill/Profile 추천 |
| `ai-agent-development-playbook` | 비단순 개발, 설계, Agent/RAG/tooling, 계약, 검증 |
| `codex-long-run` | 여러 구현/디버깅/검증 사이클이 필요한 장기 작업 |
| `codex-task-router` | 모델/Reasoning/병렬 실행 선택이 실제로 필요한 경우의 추천 |
| `human-readable-code` | 사람이 읽고 배우기 쉬운 코드, 구조, 설명 |
| `human-centered-project-builder` | 요구부터 구현·검증까지 한 번에 진행하는 프로젝트 워크플로 |
| `guide-ppt-creator` | 기술 문서/프로젝트를 가이드 PPTX로 변환 |

원칙은 **전부 사용하지 않는 것**입니다.
현재 작업에 필요한 최소 Skill만 사용합니다.

---

# 추천 사용 예

Skill 선택이 애매할 때:

```text
$codex-skill-router

현재 작업에 필요한 최소 Skill과 검증 Profile만 추천해.
구현은 하지 마.
```

비단순 개발:

```text
$ai-agent-development-playbook

Repository 요구사항/아키텍처와 현재 Task 범위를 확인하고
최소 변경으로 구현한 뒤 실제 Evidence로 완료 여부를 판단해.
```

장기 작업:

```text
$codex-long-run

현재 Repository 상태를 기준으로 하나의 결과만 끝까지 진행해.
불필요한 전체 스캔과 반복 로그를 줄이고 필요한 Evidence를 남겨.
```

---

# 제거

Windows:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\uninstall.ps1
```

Linux/macOS:

```bash
./uninstall.sh
```

전역 `AGENTS.md`에서는 Playbook 마커 구간만 제거하고,
이 Repository가 관리하는 Skills와 `~/.codex/playbook-harness`만 제거합니다.

백업은 자동 삭제하지 않습니다.

```text
%USERPROFILE%\.codex\playbook-backups\
```

---

# 설계 원칙

- Chat 기록보다 Repository를 지속 가능한 Source of Truth로 사용
- 한 번에 하나의 coherent outcome
- 자기 보고 PASS가 아니라 Test/Diff/Artifact Evidence로 완료 판단
- 전역 규칙은 짧게 유지
- 상세 워크플로는 Skill로 Progressive Disclosure
- Skill Router도 선택이 애매할 때만 사용
- Quality Gate는 LLM이 아니라 결정론적 코드로 수행
- 고위험 작업만 STRICT/강한 검증 사용
- 상시 멀티에이전트와 무거운 Agent framework는 기본 Core에서 제외
- 토큰 절감이 정확성이나 검증 신뢰성을 낮추면 채택하지 않음
