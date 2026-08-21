#!/usr/bin/env python3
"""Shared sdd.md parsing for stage entry/exit rule graders.

Reads ONLY authored condition tables — the tables under `#### Stage Entry
Conditions` and `#### Stage Exit Conditions`. Design Rationale prose is never
read: the skill *requires* rationale that names the anti-pattern it avoided
("routed deterministically rather than via `user-selected-stage`"), so a naive
whole-file grep marks a complying design as a violation.

Rows are keyed by normalized column header, not position — condition tables
ship with or without the optional trailing `Display Name` column.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ENTRY_SECTION = "Stage Entry Conditions"
EXIT_SECTION = "Stage Exit Conditions"

# Blocks are cut at EVERY `###` heading, then classified. Cutting only at headings we
# recognize would let an unrecognized one (`### Exception Stage: X`) extend the previous
# stage's block, so its tables would be graded as that stage's own.
_H3 = re.compile(r"(?m)^###\s+(?P<title>\S.*?)\s*$")
# `Stage 2: Vendor Approval (`stage-vendor-approval`)`, `Secondary Stage: Compliance Hold`,
# `Exception Stage: Payment Failure`.
_STAGE_TITLE = re.compile(r"(?i)^(?:(?P<kind>[a-z]+)\s+)?stage(?:\s+\d+)?\s*:\s*(?P<label>.+?)$")


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def read_sdd(name: str = "sdd.md") -> str:
    path = Path(name)
    if not path.is_file():
        fail(f"missing {name} in {Path.cwd()}")
    return path.read_text(encoding="utf-8", errors="ignore")


def normalize(cell: str) -> str:
    """Strip markdown emphasis/backticks and collapse whitespace."""
    return re.sub(r"\s+", " ", cell.replace("`", "").replace("*", "")).strip()


def stage_blocks(text: str) -> dict[str, str]:
    """Map stage label -> the markdown body of that stage's section.

    Non-stage `###` headings terminate the preceding block and are dropped, so no
    section is ever attributed to a neighbouring stage.
    """
    headings = list(_H3.finditer(text))
    blocks: dict[str, str] = {}
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        match = _STAGE_TITLE.match(normalize(heading.group("title")))
        if not match:
            continue
        label = re.sub(r"\([^)]*\)$", "", match.group("label")).strip()
        blocks[normalize(label)] = text[heading.start() : end]
    return blocks


def stage_kind(block: str) -> str:
    """`primary`, `secondary`, or whatever qualifier the heading carries."""
    first = normalize(block.splitlines()[0]) if block.strip() else ""
    match = re.match(r"(?i)^#+\s*(?:([a-z]+)\s+)?stage\b", first)
    return (match.group(1) or "primary").lower() if match else "primary"


def find_stage(blocks: dict[str, str], label: str) -> str:
    for name, block in blocks.items():
        if name.lower() == label.lower():
            return block
    fail(f"missing stage section for {label!r}; found {sorted(blocks)}")
    raise AssertionError("unreachable")


def table_rows(block: str, section: str) -> list[dict[str, str]]:
    """Rows of the markdown table under `#### <section>`, keyed by header.

    Returns [] when the section or its table is absent.
    """
    heading = re.search(rf"(?im)^#{{2,6}}\s*{re.escape(section)}\s*$", block)
    if not heading:
        return []
    lines = block[heading.end() :].splitlines()
    table: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|"):
            table.append(stripped)
        elif table:
            break
        elif stripped.startswith("#"):
            break
    if len(table) < 2:
        return []

    def cells(row: str) -> list[str]:
        return [normalize(cell) for cell in row.strip("|").split("|")]

    headers = [header.lower() for header in cells(table[0])]
    rows = []
    for row in table[1:]:
        values = cells(row)
        if values and set("".join(values)) <= {"-", ":", " ", ""}:
            continue  # separator row
        rows.append({headers[i]: values[i] for i in range(min(len(headers), len(values)))})
    return rows


def entry_rows(block: str) -> list[dict[str, str]]:
    return table_rows(block, ENTRY_SECTION)


def exit_rows(block: str) -> list[dict[str, str]]:
    return table_rows(block, EXIT_SECTION)


def column(row: dict[str, str], *candidates: str) -> str:
    """Value of the first matching column: exact header match first, substring only after.

    Substring-first would let a short candidate (`if`) latch onto an unrelated header.
    """
    for candidate in candidates:
        if candidate.lower() in row:
            return row[candidate.lower()]
    for candidate in candidates:
        for header, value in row.items():
            if candidate.lower() in header:
                return value
    return ""


def when(row: dict[str, str]) -> str:
    return column(row, "when")


def guard(row: dict[str, str]) -> str:
    return column(row, "if")


def rule_type(row: dict[str, str]) -> str:
    """Bare rule token from a WHEN cell: `selected-stage-exited("X")` -> that name."""
    match = re.match(r"([a-z][a-z0-9-]*)", when(row).strip().lower())
    return match.group(1) if match else ""


def is_empty(value: str) -> bool:
    return value.strip() in {"", "-", "—", "--", "n/a", "na", "none"}
