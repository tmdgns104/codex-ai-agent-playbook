# Speaker Notes Contract

## Goal

Speaker notes for guide/training decks are the actual explanation the audience should hear.

They are not presenter instructions.

## Required Style

Write in natural spoken language.

Explain:
1. What the audience is looking at.
2. What the concept means.
3. Why it matters.
4. How to interpret the important part of the slide.
5. A practical example, analogy, or failure case when useful.
6. A short transition to the next concept.

## Bad

"Explain the architecture diagram."
"Tell the audience that MCP connects tools."
"Mention that the next slide covers verification."

## Good

"이 그림에서는 Agent가 직접 모든 외부 시스템을 아는 것이 아니라 MCP를 통해 도구와 리소스에 접근합니다. 여기서 Tool은 실제 행동을 수행하고, Resource는 판단에 필요한 정보를 제공합니다. 예를 들어 장비 상태를 읽는 것은 Resource에 가깝고, 장비를 재시작하는 것은 Side Effect가 있는 Tool입니다."

## Technical Content

When code/command/API appears:
- explain important arguments
- explain input/output
- explain what changes in the system
- explain expected success/failure behavior

When a diagram appears:
- explain reading order
- explain arrows
- explain boundaries
- explain why components are separated

## Training Deck Addition

When useful, include:
- common misconception
- troubleshooting clue
- check-for-understanding question
- answer/explanation

Do not make the notes read like a checklist for a lecturer.
