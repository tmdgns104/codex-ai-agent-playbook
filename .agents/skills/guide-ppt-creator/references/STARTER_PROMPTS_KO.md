# Guide PPT Creator 시작 Prompt

## 1. 프로젝트 문서로 기술 가이드 PPT

```text
$guide-ppt-creator

이 프로젝트의 다음 문서를 기반으로 기술 가이드 PPT를 만들어.

- PROJECT.md
- ARCHITECTURE.md
- AGENT_ARCHITECTURE.md
- STATE.md

대상:
이 프로젝트를 처음 보는 개발자

목적:
전체 시스템 구조와 데이터/Agent 흐름을 이해시키는 것

먼저 Storyboard를 설계하고,
슬라이드별 Slide Contract를 작성한 뒤 PPTX를 생성해.

필요한 구조는 도식화하고,
발표자 노트에는 강사용 지침이 아니라
청중에게 실제로 설명하는 강의문을 작성해.

생성 후 가능한 방식으로 렌더링하여
모든 슬라이드를 Visual QA하고 결과를 보고해.
```

## 2. 기존 PPT 개선

```text
$guide-ppt-creator

existing.pptx를 수정해.

목표:
내용은 유지하되 더 이해하기 쉬운 기술 가이드로 개선.

먼저 기존 덱의:
- 슬라이드 구조
- 스타일
- 글꼴/색상
- 반복 레이아웃
- 핵심 메시지
를 분석해.

원본은 덮어쓰지 말고 새 파일로 저장해.

불필요한 전면 재디자인은 하지 말고,
가독성/스토리/도식/노트를 개선해.

완료 후 렌더링하여 전체 Visual QA를 수행해.
```

## 3. 코드/명령어 교육 자료

```text
$guide-ppt-creator

이 코드베이스의 설치 및 실행 방법을
초보 개발자용 가이드 PPT로 만들어.

각 명령어 슬라이드는:
- 명령어
- 각 옵션의 의미
- 실행 시 시스템에서 일어나는 일
- 성공 여부 확인법
- 자주 발생하는 오류
를 설명해.

발표자 노트는 실제 강의문 형태로 작성해.
```

## 4. Architecture 설명 덱

```text
$guide-ppt-creator

ARCHITECTURE.md를 기반으로
시스템 Architecture 설명 PPT를 만들어.

텍스트를 그대로 옮기지 말고:
Context → Components → Data Flow → Failure Boundary → Operations
순서로 Storyboard를 구성해.

복잡한 관계는 Diagram Contract를 먼저 작성해.
```

## 5. PPT 결과 검수만

```text
$guide-ppt-creator

이 PPTX를 수정하지 말고 먼저 검수해.

- 구조
- 스토리
- 텍스트 밀도
- 시각적 일관성
- Diagram 정확성
- Speaker Notes
- 출처/수치
를 확인해.

가능하면 렌더링해서 전 슬라이드를 보고,
문제를 HIGH / MEDIUM / LOW로 분류해.
```
