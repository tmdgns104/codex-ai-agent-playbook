# Codex AI Agent Playbook Kit

이 패키지는 `AI Agent Development Playbook v3`를 Codex CLI에서 재사용하기 위한 설치형 세트입니다.

## 포함 내용

```text
.codex/
└── AGENTS.md
    모든 프로젝트에서 적용할 최소 작업 원칙

.agents/
└── skills/
    └── ai-agent-development-playbook/
        ├── SKILL.md
        ├── references/
        │   ├── PLAYBOOK.md
        │   ├── STARTER_PROMPTS_KO.md
        │   └── 각종 Contract/Result/Review 템플릿
        └── assets/
            └── project-template/
                새 프로젝트에 복사해 사용할 문서 구조
```

## Windows 설치

PowerShell에서 압축을 푼 폴더로 이동한 뒤:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

설치 위치:

```text
$HOME\.codex\AGENTS.md
$HOME\.agents\skills\ai-agent-development-playbook\
```

기존 `$HOME\.codex\AGENTS.md`가 있다면 설치 스크립트는
`AI_AGENT_PLAYBOOK_KIT` 마커 구간만 추가/갱신하여 기존 사용자 지침을 보존합니다.

기존 Skill 폴더가 있다면 timestamp 백업 후 새 버전을 설치합니다.

## 제거

```powershell
.\uninstall.ps1
```

전역 `AGENTS.md`에서는 이 Kit가 추가한 마커 구간만 제거합니다.

## 설치 확인

새 터미널에서 프로젝트 폴더로 이동해:

```powershell
codex
```

그리고:

```text
$ai-agent-development-playbook

이 skill의 목적과 현재 프로젝트에서 언제 사용해야 하는지 요약해.
코드는 수정하지 마.
```

처럼 확인합니다.

## 새 프로젝트 시작 권장 방식

1. 새 repo 생성
2. `assets/project-template`에서 필요한 문서만 프로젝트 루트에 복사
3. Codex 실행
4. `$ai-agent-development-playbook`을 사용해 Problem/Requirements/Architecture 확정
5. `TASK-XXX.md` 단위로 구현
6. 테스트/Evidence 생성
7. 필요하면 ChatGPT로 Architecture/Result Review

## 중요한 원칙

모든 프로젝트에 모든 문서를 강제로 만들지 않습니다.

- 작은 script: Task + Test 정도로 충분할 수 있음
- 일반 web app: Project/Requirements/Architecture/AGENTS
- RAG: Resource contract + retrieval eval 추가
- Tool-using agent: State/Node/Tool contracts 추가
- Production agent: Persistence/Observability/Security/HITL 추가

프로젝트 복잡성에 맞춰 Playbook을 단계적으로 적용합니다.


---

# V4 추가: guide-ppt-creator

V4에는 두 개의 사용자 Skill이 포함됩니다.

```text
$ai-agent-development-playbook
→ 프로젝트를 설계하고 구현/검증하는 방법론

$guide-ppt-creator
→ 프로젝트/문서/코드를 사람이 이해하기 쉬운 PPT 가이드로 변환하는 워크플로
```

`guide-ppt-creator`는 다음 순서를 기본으로 합니다.

```text
Source Analysis
→ Audience / Goal
→ Storyboard Contract
→ Slide Contract
→ Diagram Contract
→ Speaker Notes
→ PPTX Build
→ Structural Inspect
→ Render
→ Visual QA
→ Content QA
```

주요 파일:

```text
.agents/skills/guide-ppt-creator/
├── SKILL.md
├── references/
│   ├── STORYBOARD_CONTRACT.md
│   ├── SLIDE_CONTRACT.md
│   ├── DIAGRAM_CONTRACT.md
│   ├── SPEAKER_NOTES_CONTRACT.md
│   ├── VISUAL_QA.md
│   ├── CONTENT_QA.md
│   ├── PPTX_IMPLEMENTATION_GUIDE.md
│   ├── PPT_RESULT_TEMPLATE.md
│   └── STARTER_PROMPTS_KO.md
├── scripts/
│   ├── inspect_pptx.py
│   ├── render_pptx.py
│   └── make_contact_sheet.py
└── assets/
    ├── default-theme.json
    └── deck-template/
```

## 사용 예

```text
$guide-ppt-creator

PROJECT.md, ARCHITECTURE.md, AGENT_ARCHITECTURE.md를 기반으로
프로젝트 구조 가이드 PPT를 만들어.

대상은 프로젝트를 처음 보는 개발자야.

먼저 Storyboard를 설계하고,
그 다음 PPTX를 만들어.

발표자 노트에는 발표자 지침이 아니라
청중에게 실제로 설명하는 강의문을 작성해.

완료 후 가능한 방식으로 렌더링해서
Visual QA와 Content QA 결과를 보고해.
```

## 렌더링 주의

`render_pptx.py`는 로컬 환경에 LibreOffice/soffice가 있으면
PPTX를 PDF로 렌더링하고, `pdftoppm`이 있으면 PNG까지 생성합니다.

렌더러가 없다면 Skill은 반드시:

```text
VISUAL QA: UNVERIFIED
```

라고 보고하도록 설계되어 있습니다.


---

# V5: 사람이 이해할 수 있는 개발 워크플로

추가 Skill:

```text
$human-readable-code
→ 사람이 읽고 배우고 유지보수하기 쉬운 코드 작성/리뷰

$human-centered-project-builder
→ 설계 + Task + 가독성 + 구현 + 테스트 + 설명을 한 번에 시작
```

가장 간단한 사용:

```text
$human-centered-project-builder

BUILD_REQUEST.md를 읽고 프로젝트를 시작해.
설계를 먼저 정리하고, 승인된 범위에서 TASK-001부터 구현해.
테스트와 Readability Review까지 수행해.
```

세부 Skill을 직접 조합할 수도 있습니다:

```text
$ai-agent-development-playbook
$human-readable-code

PROJECT.md와 ARCHITECTURE.md를 기준으로 TASK-001을 구현해.
```
