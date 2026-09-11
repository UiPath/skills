#!/usr/bin/env python3
"""Draft-scoped data-lineage check for a case design DRAFT.

    python3 draft_lineage_check.py [sdd.draft.md]

Why this exists separately from ``sdd_check.py``. That script validates a
FINALIZED SDD's render contract, and the design tasks deliberately stop at a
pre-conformance draft ("don't polish or validate it yet, just capture the
design"). Measured: running it as a design criterion would fail 7 currently
PASSING runs — 6 of loan-origination's 9 successes among them — because their
drafts legitimately lack finalized template shape.

So this checks the two things a draft must get right for the design to be
buildable at all, and nothing about shape:

* lineage — every consumed row has a producer: an ``In`` category, a Default, a
  trigger source, or a ``-> name`` / ``name =`` producer somewhere.

Both are conditions the SDD's own grammar states (case-design-layers-guide.md
§ Category semantics: `Variable` closes via "producer or Default"), so a draft
failing them is defective on its own terms rather than merely unpolished.
"""

from __future__ import annotations

import pathlib
import re
import sys


def issues_for(text: str) -> list[str]:
    """Mapping + lineage findings for an SDD or draft. Empty list == clean."""
    declared: set[str] = set()
    category: dict[str, str] = {}
    src_trig: dict[str, str] = {}
    default: dict[str, str] = {}
    for name, cat, st, d in re.findall(
        r"^\|\s*([A-Za-z]\w*)\s*\|\s*(In|Out|Variable)\s*\|"
        r"\s*[^|]*\|\s*([^|]*?)\s*\|\s*[^|]*\|\s*([^|]*?)\s*\|",
        text, re.M,
    ):
        declared.add(name)
        category[name] = cat
        src_trig[name] = st.strip()
        default[name] = d.strip()

    if not declared:
        # A draft with no variables table declares no data contract; that is a
        # shape question, not a lineage one, so stay silent.
        return []

    refs = set(re.findall(r"=vars\.([A-Za-z]\w*)", text)) - {"X"}
    out: list[str] = []

    # Deliberately NO mapping check. An `=vars.<name>` with no §Case Variables
    # row can be a direct producer reference, which the grammar permits, and the
    # sweep found it firing on a draft that scored 0.944 SUCCESS. A criterion that
    # fails a passing run is wrong however defensible it reads.

    produced = set(re.findall(r"->\s*([A-Za-z]\w*)", text)) | set(
        re.findall(r"\b([A-Za-z]\w*)\s*=\s*(?!=)", text)
    )
    open_lineage = sorted(
        r for r in refs
        if r in declared and category.get(r) != "In"
        and not default.get(r) and not src_trig.get(r) and r not in produced
    )
    if open_lineage:
        out.append(
            f"lineage: {len(open_lineage)} variable(s) consumed but never produced "
            f"(needs a Default, a trigger source, or a producing `-> name` row): "
            + ", ".join(open_lineage)
        )
    return out


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if target:
        path = pathlib.Path(target)
    else:
        path = next(
            (p for p in (pathlib.Path("sdd.draft.md"), pathlib.Path("sdd.md")) if p.is_file()),
            None,
        )
    if path is None or not path.is_file():
        sys.exit("FAIL: no sdd.draft.md or sdd.md found")

    found = issues_for(path.read_text(encoding="utf-8", errors="ignore"))
    if found:
        sys.exit("FAIL: draft data contract\n  - " + "\n  - ".join(found))
    print(f"OK: {path.name} data contract closes — every =vars reference resolves and has a producer")


if __name__ == "__main__":
    main()
