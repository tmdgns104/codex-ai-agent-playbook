#!/usr/bin/env python3
"""
Render a PPTX to PDF and, when possible, PNG slide images.

Primary supported renderer:
- LibreOffice / soffice

Optional PDF-to-image:
- pdftoppm

Usage:
    python render_pptx.py deck.pptx output_dir

The script intentionally fails clearly when a renderer is unavailable.
It does not claim visual QA without rendered output.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

def which_any(names):
    for name in names:
        p = shutil.which(name)
        if p:
            return p
    return None

def run(cmd):
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)

def main(pptx_s: str, out_s: str) -> int:
    pptx = Path(pptx_s).resolve()
    out = Path(out_s).resolve()
    out.mkdir(parents=True, exist_ok=True)

    if not pptx.exists():
        print(f"ERROR: missing file: {pptx}", file=sys.stderr)
        return 2

    office = which_any(["soffice", "libreoffice"])
    if not office:
        print(
            "ERROR: LibreOffice/soffice not found. VISUAL QA is UNVERIFIED.\n"
            "Install LibreOffice or use another environment-specific PowerPoint renderer.",
            file=sys.stderr,
        )
        return 3

    run([office, "--headless", "--convert-to", "pdf", "--outdir", str(out), str(pptx)])
    pdf = out / (pptx.stem + ".pdf")
    if not pdf.exists():
        print(f"ERROR: expected rendered PDF not found: {pdf}", file=sys.stderr)
        return 4

    pdftoppm = which_any(["pdftoppm"])
    if not pdftoppm:
        print(f"PDF_RENDERED: {pdf}")
        print("NOTE: pdftoppm not found; PNG slide rendering skipped.")
        return 0

    prefix = out / "slide"
    run([pdftoppm, "-png", "-r", "144", str(pdf), str(prefix)])
    pngs = sorted(out.glob("slide-*.png"))
    print(f"PDF_RENDERED: {pdf}")
    print(f"PNG_SLIDES: {len(pngs)}")
    for p in pngs:
        print(p)
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python render_pptx.py deck.pptx output_dir", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
