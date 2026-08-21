#!/usr/bin/env python3
"""
Dependency-free structural inspection for .pptx files.

Usage:
    python inspect_pptx.py path/to/deck.pptx

Reports:
- slide count
- notes slide count
- media count
- chart count
- slide text summaries
- empty slides
- duplicate slide titles (heuristic)
"""
from __future__ import annotations

import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}

def natural_key(name: str):
    return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", name)]

def extract_text(xml_bytes: bytes) -> list[str]:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []
    vals = []
    for node in root.findall(".//a:t", NS):
        if node.text and node.text.strip():
            vals.append(node.text.strip())
    return vals

def main(path_str: str) -> int:
    path = Path(path_str)
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2
    if path.suffix.lower() != ".pptx":
        print("ERROR: expected .pptx", file=sys.stderr)
        return 2

    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        print("ERROR: invalid pptx/zip container", file=sys.stderr)
        return 3

    names = zf.namelist()
    slides = sorted(
        [n for n in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)],
        key=natural_key,
    )
    notes = [n for n in names if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", n)]
    media = [n for n in names if n.startswith("ppt/media/") and not n.endswith("/")]
    charts = [n for n in names if re.fullmatch(r"ppt/charts/chart\d+\.xml", n)]

    print(f"FILE: {path}")
    print(f"SLIDES: {len(slides)}")
    print(f"NOTES_SLIDES: {len(notes)}")
    print(f"MEDIA_FILES: {len(media)}")
    print(f"CHARTS: {len(charts)}")
    print()

    titles = []
    empty = []
    for idx, slide_name in enumerate(slides, 1):
        texts = extract_text(zf.read(slide_name))
        title = texts[0] if texts else ""
        titles.append(title)
        if not texts:
            empty.append(idx)
        preview = " | ".join(texts[:5])
        if len(preview) > 180:
            preview = preview[:177] + "..."
        print(f"{idx:02d}: {preview if preview else '[NO TEXT]'}")

    dupes = {t: c for t, c in Counter(titles).items() if t and c > 1}
    print()
    print(f"EMPTY_SLIDES: {empty if empty else 'None'}")
    print(f"DUPLICATE_TITLES: {dupes if dupes else 'None'}")

    if len(notes) < len(slides):
        print(f"NOTE: only {len(notes)}/{len(slides)} slides have notes slide XML.")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python inspect_pptx.py deck.pptx", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
