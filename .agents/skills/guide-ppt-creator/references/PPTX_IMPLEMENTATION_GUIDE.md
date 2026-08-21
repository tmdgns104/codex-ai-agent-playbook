# PPTX Implementation Guide

## Preferred Order

1. Reuse an existing approved deck/template when supplied.
2. Reuse theme/layout helpers.
3. Build editable shapes/text/charts where practical.
4. Generate image assets only when they improve communication.
5. Render and visually inspect the result.

## Code Organization

For code-generated decks, prefer:

```text
presentation/
├── source/
├── assets/
├── build/
├── render/
├── deck_spec.md
├── build_deck.py
└── helpers/
```

Separate:
- content/data
- theme tokens
- layout helpers
- slide-building functions

Avoid repeating raw coordinates/styles across every slide when the same layout recurs.

## Editable Content

Prefer editable:
- titles
- body text
- shapes
- connectors
- tables
- native charts

Images are appropriate for:
- screenshots
- photos
- complex illustrations
- visual backgrounds
- generated explanatory artwork

Do not rasterize an entire slide merely because it is easier to generate.

## Notes

When the chosen implementation supports PowerPoint notes, insert the approved speaker notes into each slide.

If notes cannot be embedded by the available library/tool:
- create a parallel `speaker_notes.md`
- report `EMBEDDED NOTES: UNVERIFIED/UNSUPPORTED`
- do not silently drop the notes requirement

## Rendering

Supported renderers differ by environment.

Use `scripts/render_pptx.py` to try:
- LibreOffice/soffice conversion to PDF
- PDF-to-image tools when present

If native Microsoft PowerPoint automation is already available in the environment, it may also be used.

Always inspect the rendered output rather than assuming the file looks correct.

## File Safety

For revision tasks:
- preserve the original input deck
- write to a new output path unless user explicitly requests in-place editing
- avoid deleting unused master/layout elements unless needed
