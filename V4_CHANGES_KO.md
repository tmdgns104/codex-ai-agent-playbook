# V4 변경사항

V4는 V3의 AI Agent Development Playbook Kit에 `guide-ppt-creator` Skill을 추가한 버전이다.

## Skill 1

`$ai-agent-development-playbook`

목적:
프로젝트를 문제 정의 → 요구사항 → Architecture → Task Contract → 구현 → 검증 → Review 구조로 진행한다.

## Skill 2

`$guide-ppt-creator`

목적:
프로젝트/문서/코드/기존 PPT를 사람이 이해하기 쉬운 가이드 PPT로 만든다.

핵심 Contract:
- Storyboard Contract
- Slide Contract
- Diagram Contract
- Speaker Notes Contract
- Visual QA
- Content QA

핵심 원칙:
- 비 trivial한 덱은 바로 PPTX부터 만들지 않는다.
- 한 슬라이드에 하나의 주요 메시지를 둔다.
- 구조/흐름은 텍스트보다 Diagram을 우선 고려한다.
- Guide/Training 발표자 노트는 실제 설명문으로 작성한다.
- 렌더링한 슬라이드를 보지 않았다면 Visual QA PASS라고 하지 않는다.
