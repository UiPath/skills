"""E2 format_preserves_prose: `sdd format` never touches what a person wrote.

The fixture is cm_golden_expense with two human-style paragraphs wedged
between tables — a blockquote reviewer note between Manager Approval's entry
table and its envelope table, and a sentence carrying a mid-line `|` between
Wait for HTTP Webhook's two tables. The machine-written corpus never places
prose there; a person editing the file does.

`uip maestro case sdd format` rewrites a copy in place. Asserted:

- every non-table line of the original comes back byte-identical and in order
  (tables themselves may be normalized: outer pipes, separator, padding);
- the first format reports Changed: true (the fixture's separator rows are
  not normalized), so a format that does nothing cannot pass;
- formatting twice is byte-identical to formatting once;
- every table row keeps its cells, trimmed, in order — format may restore
  outer pipes, the separator and padding, never content, rows or columns.
  Compared directly because the parsed Model does not reflect every cell
  (Tasks Starts When, Persona and SLA are not read from that table);
- the formatted document parses to exactly the original's Model, so what gets
  built never changes.

Interface per the provisional B5 sketch (UiPath/cli, not yet built): in place,
`Code: "SddFormat"`, `Data: {File, Changed}`. Skips while the installed CLI has
no `sdd format`; needs `uip` on PATH, and fails without it when REQUIRE_UIP=1.

Run from repo root:
    REQUIRE_UIP=1 pytest tests/tasks/uipath-maestro-case/format_preserves_prose/ -rs
"""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "sdd.md"
SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")


def _uip(*args):
    r = subprocess.run(["uip", "maestro", "case", "sdd", *args, "--output", "json"],
                       capture_output=True, text=True, timeout=120)
    return r.returncode, json.loads(r.stdout)


def non_table_lines(text):
    """Lines outside GFM tables. A table starts at a row followed by a
    delimiter row and runs until a blank line; rows may lack outer pipes."""
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


def table_cells(text):
    """Each table row as its tuple of trimmed cells; delimiter rows dropped."""
    lines = text.split("\n")
    rows, i = [], 0
    while i < len(lines):
        if "|" in lines[i] and i + 1 < len(lines) and SEPARATOR.match(lines[i + 1]):
            while i < len(lines) and lines[i].strip():
                if not SEPARATOR.match(lines[i]):
                    row = lines[i].strip()
                    row = row[1:] if row.startswith("|") else row
                    row = row[:-1] if row.endswith("|") else row
                    rows.append(tuple(c.strip() for c in row.split("|")))
                i += 1
            continue
        i += 1
    return rows


def test_fixture_prose_is_outside_tables():
    kept = non_table_lines(FIXTURE.read_text(encoding="utf-8"))
    assert "The webhook payload is trusted as sent: finance owns the schema | not the case." in kept
    assert any(line.startswith("> Reviewer note:") for line in kept)


@pytest.fixture(scope="module")
def formatted(tmp_path_factory):
    if shutil.which("uip") is None:
        if os.environ.get("REQUIRE_UIP") == "1":
            pytest.fail("REQUIRE_UIP=1 but no `uip` on PATH")
        pytest.skip("no `uip` on PATH")
    work = tmp_path_factory.mktemp("format")
    doc = work / "sdd.md"
    shutil.copy(FIXTURE, doc)
    code, out = _uip("format", str(doc))
    if "unknown command" in (out.get("Message") or ""):
        pytest.skip("not checking: the installed CLI has no `sdd format`")
    assert code == 0, out
    assert (out.get("Data") or {}).get("Changed") is True, "the fixture's tables are not normalized, so the first format must change them"
    once = doc.read_text(encoding="utf-8")
    code, out2 = _uip("format", str(doc))
    assert code == 0, out2
    return {"once": once, "twice": doc.read_text(encoding="utf-8"), "second": out2, "path": doc}


def test_non_table_lines_are_byte_identical(formatted):
    assert non_table_lines(formatted["once"]) == non_table_lines(FIXTURE.read_text(encoding="utf-8"))


def test_table_cells_are_unchanged(formatted):
    assert table_cells(formatted["once"]) == table_cells(FIXTURE.read_text(encoding="utf-8"))


def test_format_is_idempotent(formatted):
    assert formatted["twice"] == formatted["once"]
    assert (formatted["second"].get("Data") or {}).get("Changed") is False


def test_format_never_changes_what_is_built(formatted):
    _, want = _uip("parse", str(FIXTURE))
    _, got = _uip("parse", str(formatted["path"]))
    assert got["Data"]["Model"] == want["Data"]["Model"]
