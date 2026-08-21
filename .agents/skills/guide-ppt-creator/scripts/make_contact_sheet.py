#!/usr/bin/env python3
"""
Create a contact sheet from rendered slide images.

Requires Pillow.

Usage:
    python make_contact_sheet.py render_dir contact_sheet.png
"""
from __future__ import annotations
import sys
from pathlib import Path

def main(src_s: str, out_s: str) -> int:
    try:
        from PIL import Image, ImageOps, ImageDraw
    except ImportError:
        print("ERROR: Pillow is required: pip install pillow", file=sys.stderr)
        return 3

    src = Path(src_s)
    imgs = sorted(list(src.glob("slide-*.png")) + list(src.glob("slide-*.jpg")))
    if not imgs:
        print(f"ERROR: no rendered slide images in {src}", file=sys.stderr)
        return 2

    thumbs = []
    target_w = 480
    pad = 20
    label_h = 28
    for i, p in enumerate(imgs, 1):
        im = Image.open(p).convert("RGB")
        ratio = target_w / im.width
        h = int(im.height * ratio)
        im = im.resize((target_w, h))
        canvas = Image.new("RGB", (target_w + pad*2, h + pad*2 + label_h), "white")
        canvas.paste(im, (pad, pad))
        d = ImageDraw.Draw(canvas)
        d.text((pad, h + pad + 5), f"Slide {i}", fill="black")
        thumbs.append(canvas)

    cols = 2
    rows = (len(thumbs) + cols - 1) // cols
    cell_w = max(x.width for x in thumbs)
    cell_h = max(x.height for x in thumbs)
    sheet = Image.new("RGB", (cell_w*cols, cell_h*rows), "#dddddd")
    for i, im in enumerate(thumbs):
        x = (i % cols) * cell_w
        y = (i // cols) * cell_h
        sheet.paste(im, (x, y))
    sheet.save(out_s)
    print(out_s)
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python make_contact_sheet.py render_dir output.png", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
