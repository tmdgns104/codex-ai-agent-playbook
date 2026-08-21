---
name: guide-ppt-creator
description: >
  Use when creating, revising, or reviewing a PowerPoint/PPTX guide, training deck,
  technical explanation deck, onboarding deck, architecture walkthrough, project guide,
  or other presentation meant to help people understand a system or process.
  Requires storyboard-first planning, slide contracts, diagram planning, audience-facing
  speaker notes, editable content where practical, rendered-slide review when available,
  and visual/content QA before completion.
---

# Guide PPT Creator

Create presentations as communication systems, not as collections of text boxes.

## Core Rule

Do not jump directly from source material to PPTX generation for a non-trivial deck.

Use this flow:

`Source Analysis → Audience/Goal → Storyboard → Slide Contracts → Visual/Diagram Plan → PPTX Build → Render/Inspect → Visual QA → Content QA → Final Evidence`

For a tiny one- or two-slide edit, use the smallest process that fits.

## 1. Understand the Deck

Before building, determine:

- intended audience
- purpose of the deck
- decisions or understanding the audience should leave with
- source material and source-of-truth files
- required/forbidden content
- existing template/brand constraints
- expected length or presentation time
- whether speaker notes are required
- output file name/location

If these cannot be inferred from supplied material, ask only the minimum questions needed.

## 2. Source-of-Truth Discipline

When source files exist, inspect them before drafting.

Preserve:
- approved facts and figures
- architecture relationships
- terminology
- naming
- version/date meaning
- brand requirements

Do not invent unsupported metrics, screenshots, customer claims, benchmarks, or architecture details.

If a claim needs confirmation, mark it for review rather than presenting it as fact.

## 3. Storyboard Before Build

For non-trivial decks, create a storyboard before generating slides.

Use `references/STORYBOARD_CONTRACT.md`.

Each slide must have:
- one primary message
- purpose in the story
- intended audience takeaway
- planned visual form
- source/evidence
- notes requirement

Avoid slides whose only purpose is "continue previous slide" unless necessary.

## 4. Slide Contract

Use `references/SLIDE_CONTRACT.md`.

Each slide should define:
- title
- core message
- content blocks
- visual hierarchy
- diagram/chart/image plan
- notes
- source/evidence
- acceptance criteria

Prefer one strong message per slide.

## 5. Visual Communication

Use a diagram when relationships, process, architecture, sequence, hierarchy, state,
or data flow are easier to understand visually than in bullets.

Follow `references/DIAGRAM_CONTRACT.md`.

Do not use decorative visuals that do not improve understanding.

Keep text, charts, and diagrams editable where practical.

When a reference deck/template exists:
- match layout logic
- typography
- color system
- branding
- section rhythm
- spacing conventions

Do not approximate a provided template without first inspecting it.

## 6. Speaker Notes

For guide/training decks, speaker notes should be actual audience-facing explanation,
not instructions to the presenter.

Follow `references/SPEAKER_NOTES_CONTRACT.md`.

Good notes explain:
- what the slide means
- why it matters
- how to read the diagram/code/command
- an analogy or practical example when useful
- common misunderstanding or failure mode
- transition to the next slide

Do not write notes like:
- "Explain this diagram"
- "Tell the audience..."
- "Mention the next point..."

Instead write the explanation itself.

## 7. Build the PPTX

Implementation may use:
- an existing PPTX/template
- a code library such as `python-pptx`
- PowerPoint automation available in the environment
- another local presentation-generation workflow

Prefer modifying an approved template over recreating brand/layout from scratch.

If creating from code:
- centralize theme/layout constants
- reuse layout helpers
- avoid per-slide hard-coded formatting when a reusable layout is appropriate
- keep data and source content separate from drawing code when practical

See `references/PPTX_IMPLEMENTATION_GUIDE.md`.

## 8. Render and Inspect

Do not validate only the source code or slide XML.

When rendering is available:
1. render the PPTX
2. inspect every slide image
3. check layout, clipping, contrast, alignment, visual balance, and consistency
4. correct problems
5. render again

Use:
- `scripts/inspect_pptx.py` for structural inspection
- `scripts/render_pptx.py` when a supported renderer is available
- `scripts/make_contact_sheet.py` to build a review sheet from rendered PNG/JPG slides

If rendering is unavailable, report:
`VISUAL QA: UNVERIFIED`

Do not claim visual perfection without seeing rendered slides.

## 9. Visual QA

Follow `references/VISUAL_QA.md`.

At minimum check:
- no clipping/overflow
- no unreadably small text
- no accidental overlap
- consistent margins
- consistent title position
- adequate contrast
- chart/diagram labels readable
- no stretched images
- visual hierarchy is obvious
- slide density is appropriate
- style is consistent across sections

## 10. Content QA

Follow `references/CONTENT_QA.md`.

Check:
- story fits the intended audience
- claims match sources
- numbers/units are correct
- architecture/process direction is correct
- terminology is consistent
- slide title accurately states the message
- speaker notes do not contradict slide content
- no unsupported claims were added

## 11. Completion Evidence

A non-trivial deck is complete only when the report includes:

- output PPTX path
- slide count
- source files used
- storyboard status
- speaker notes status
- structural inspection result
- rendered visual QA status
- content QA status
- items requiring human review

Use the result format in `references/PPT_RESULT_TEMPLATE.md`.

## Progressive Disclosure

Read only what is needed:

- Story planning → `references/STORYBOARD_CONTRACT.md`
- Individual slide design → `references/SLIDE_CONTRACT.md`
- Architecture/process visuals → `references/DIAGRAM_CONTRACT.md`
- Teaching/guide narration → `references/SPEAKER_NOTES_CONTRACT.md`
- PPTX implementation → `references/PPTX_IMPLEMENTATION_GUIDE.md`
- Rendering/layout review → `references/VISUAL_QA.md`
- Facts/story review → `references/CONTENT_QA.md`
- Prompt examples → `references/STARTER_PROMPTS_KO.md`

Do not load every reference by default.
