"""E5: a correction changes only what it names; format may tidy tables, nothing else.

Compares the sandbox sdd.md with the staged fixture:

1. Every line outside a table is byte-identical and in order, except rows
   added inside `## Document History`.
2. Every table row has the same cells, trimmed, as the fixture with the
   Case-Level SLA changed to 4 d — `sdd format` may restore outer pipes, the
   separator and padding (including on the row written without outer pipes)
   but never a cell's content, a row, or a column. Compared cell by cell
   because the parsed Model does not reflect every Tasks cell: Starts When,
   Persona and SLA are not read from the Tasks table, and a task block that
   states its own Activation Mode overrides that column.
3. The document parses to exactly that expected document's Model.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL = (HERE / "fixtures" / "sdd.md").read_text(encoding="utf-8")
FINAL = Path(os.environ.get("SDD", "sdd.md")).read_text(encoding="utf-8")
SLA_OLD, SLA_NEW = "| Case-Level SLA | 5 d |", "| Case-Level SLA | 4 d |"
SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")


def non_table_lines(text):
    lines = text.split("\n")
    keep, i = [], 0
    while i < len(lines):
        if "|" in lines[i] and i + 1 < len(lines) and SEPARATOR.match(lines[i + 1]):
            while i < len(lines) and lines[i].strip():
                i += 1
            continue
        keep.append(lines[i])
        i += 1
    return keep


def table_rows(text):
    """Each table row as its tuple of trimmed cells; delimiter rows dropped."""
    lines = text.split("\n")
    rows, i = [], 0
    while i < len(lines):
        if "|" in lines[i] and i + 1 < len(lines) and SEPARATOR.match(lines[i + 1]):
            while i < len(lines) and lines[i].strip():
                if not SEPARATOR.match(lines[i]):
                    cells = lines[i].strip()
                    cells = cells[1:] if cells.startswith("|") else cells
                    cells = cells[:-1] if cells.endswith("|") else cells
                    rows.append(tuple(c.strip() for c in cells.split("|")))
                i += 1
            continue
        i += 1
    return rows


def without_history(lines):
    start = lines.index("## Document History")
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
    return lines[:start] + lines[end:]


def model(text):
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(text)
    out = subprocess.run(["uip", "maestro", "case", "sdd", "parse", f.name, "--output", "json"],
                         capture_output=True, text=True, timeout=120).stdout
    os.unlink(f.name)
    return json.loads(out)["Data"]["Model"]


def _only_history_rows_added(final, expected):
    """Allow extra rows only inside `## Document History`'s table."""
    def split(text):
        lines = text.split("\n")
        start = lines.index("## Document History")
        end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
        return "\n".join(lines[:start] + lines[end:]), "\n".join(lines[start:end])
    body_f, hist_f = split(final)
    body_e, hist_e = split(expected)
    rows_he = table_rows(hist_e)
    return table_rows(body_f) == table_rows(body_e) and table_rows(hist_f)[:len(rows_he)] == rows_he


def main():
    bad = []
    if without_history(non_table_lines(FINAL)) != without_history(non_table_lines(ORIGINAL)):
        bad.append("a line outside the tables changed")
    expected = ORIGINAL.replace(SLA_OLD, SLA_NEW, 1)
    if not _only_history_rows_added(FINAL, expected):
        bad.append("a table cell, row or column changed")
    if model(FINAL) != model(expected):
        bad.append("parsed content differs from the fixture with only the SLA changed")
    for b in bad:
        print(b)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
