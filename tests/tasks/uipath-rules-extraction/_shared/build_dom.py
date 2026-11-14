#!/usr/bin/env python3
"""Regenerate _setup/policy_digitized/dom.json from document.md.

A synthetic stand-in for the digitizer's dom.json: each text line of document.md
becomes one visual line, each word a box. Only the fields resolve-refs.mjs and
policy_check.py read are written (pages[].pageIndex/size and nested words with
box [top, left, width, height], text, visualLineNumber). Run after editing
document.md:  python3 build_dom.py
"""
import json
import re
from pathlib import Path

SETUP = Path(__file__).resolve().parent.parent / "_setup"
SIZE = [0.0, 0.0, 2295.0, 2970.0]
LEFT, TOP, LINE_STEP, HEIGHT = 200, 200, 60, 44
CHAR_W, GAP = 22, 14


def build(markdown: str) -> dict:
    pages, lines = [], []
    for raw in markdown.splitlines():
        marker = re.fullmatch(r"<!-- page: (\d+) -->", raw.strip())
        if marker:
            if lines:
                pages.append(lines)
            lines = []
        elif raw.strip():
            lines.append(raw.strip())
    pages.append(lines)
    out = []
    for index, page_lines in enumerate(pages):
        words = []
        for line_no, line in enumerate(page_lines):
            x = LEFT
            for token in line.split():
                width = CHAR_W * len(token)
                words.append({"box": [float(TOP + LINE_STEP * line_no), float(x), float(width), float(HEIGHT)],
                              "text": token, "visualLineNumber": line_no})
                x += width + GAP
        out.append({"pageIndex": index, "size": SIZE,
                    "sections": [{"type": "Paragraph", "wordGroups": [{"type": "Sentence", "words": words}]}]})
    return {"dataContractVersion": "synthetic-1", "pages": out}


if __name__ == "__main__":
    text = (SETUP / "policy_digitized" / "document.md").read_text(encoding="utf-8")
    (SETUP / "policy_digitized" / "dom.json").write_text(json.dumps(build(text), indent=1), encoding="utf-8")
    print("wrote policy_digitized/dom.json")
