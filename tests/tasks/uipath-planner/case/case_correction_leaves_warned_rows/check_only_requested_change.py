"""E5: the correction touched only the line it named.

Compares the sandbox sdd.md with the staged fixture. Passes when the only
changed lines are the Case-Level SLA row (now 4 d) and, optionally, rows
added inside `## Document History`. Every other line — including the
row written without outer pipes, which `sdd validate` only warns about —
must be byte-identical.
"""

import difflib
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL = (HERE / "fixtures" / "sdd.md").read_text(encoding="utf-8").split("\n")
FINAL = Path(os.environ.get("SDD", "sdd.md")).read_text(encoding="utf-8").split("\n")
SLA_OLD, SLA_NEW = "| Case-Level SLA | 5 d |", "| Case-Level SLA | 4 d |"


def history_span(lines):
    start = lines.index("## Document History")
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
    return start, end


def main():
    hs, he = history_span(ORIGINAL)
    bad = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=ORIGINAL, b=FINAL, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        old, new = ORIGINAL[i1:i2], FINAL[j1:j2]
        if tag == "replace" and old == [SLA_OLD] and new == [SLA_NEW]:
            continue
        if tag == "insert" and hs <= i1 <= he:
            continue
        bad.append((tag, i1 + 1, old[:2], new[:2]))
    if SLA_NEW not in FINAL:
        bad.append(("missing", None, [SLA_OLD], [SLA_NEW]))
    for b in bad:
        print(b)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
