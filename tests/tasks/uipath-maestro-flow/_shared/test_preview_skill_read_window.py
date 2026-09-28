"""The routing part of each preview Maestro SKILL.md must arrive in an agent's first read.

Agents open SKILL.md with a line window, not the whole file. In run
adhoc-2026-09-23_16-15-07 (codex gpt-5.6-luna, v2 arm), 121 of the 122 tasks
that read `uipath-maestro-flow/SKILL.md` opened it first with
`sed -n '1,240p'` (the other used `1,280p`); only 44 of the 122 ever printed a
later range past line 240. A router row past that window is reachable only by
a lucky search: skill-flow-decision scored 0.375 in that run because its row
sat at line 250, outside the agent's only read of the file. #3364 (09-16) had
pushed the `## Supported node types` table 40 lines down, and nothing checked
where it sat. flow-builder-sdk v6.6.0 `skill-router-docs.test.ts:297-299` named the
risk ("a capability whose only link sits past that line is unreachable in
practice") but checked only that every reference had a row, and
flow-builder-sdk #776 deleted that test.

Budgets:

- ROUTER_WINDOW = 220 for the router table and `## API index`: 20 lines of
  margin under the 240-line read, and a window agents also use for references
  (`sed -n '1,220p'`).
- POINTER_WINDOW = 240 for the sections above the router that hold its
  pointers: `## Project layout`, `## Lifecycle` (points at
  references/CLI-LOOP.md), `## Editing an existing flow` (points at
  references/brownfield.md) and `## Builder frame`: the measured first read
  itself.
- WINDOW_BYTES = 32 KiB from line 1 to the end of the last checked section, so
  the line budget cannot be met by packing prose onto a few very long lines.

In the flow skill all six sections are required: a missing or renamed one
fails here, it is never skipped. Case and BPMN are checked for the sections
they have (`## API index`, `## Capability router`). Headings inside code
fences do not count.

Regex only: CI installs only pytest (see test_headless_preamble.py).
"""

from __future__ import annotations

import glob
import os
import re
from dataclasses import dataclass

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.normpath(os.path.join(_HERE, "..", "..", "..", ".."))
_PREVIEW_SKILLS = os.path.join(_REPO, "preview", "skills")

ROUTER_WINDOW = 220
POINTER_WINDOW = 240
WINDOW_BYTES = 32 * 1024

# H2 title -> the last line it may end on.
WINDOWS = {
    "Supported node types": ROUTER_WINDOW,
    "Capability router": ROUTER_WINDOW,
    "API index": ROUTER_WINDOW,
    "Project layout": POINTER_WINDOW,
    "Lifecycle": POINTER_WINDOW,
    "Editing an existing flow": POINTER_WINDOW,
    "Builder frame": POINTER_WINDOW,
}

# Skill folder -> sections that must exist. Every other skill (Case and BPMN
# today) is checked only for the WINDOWS sections it has.
REQUIRED = {
    "uipath-maestro-flow": (
        "Supported node types",
        "API index",
        "Lifecycle",
        "Editing an existing flow",
        "Project layout",
        "Builder frame",
    ),
}

ROUTER_HEADER = "| Node or surface | Emitted node type |"
_ROUTER_HEADER = re.compile(r"^\s*\|\s*Node or surface\s*\|\s*Emitted node type\s*\|")
_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
_H2 = re.compile(r"^##(?!#)\s+(.+?)\s*#*\s*$")
_TABLE_LINE = re.compile(r"^\s*\|")
_TABLE_SEPARATOR = re.compile(r"^\s*\|?(\s*:?-+:?\s*\|)+\s*$")

REMEDY = (
    "Agents read SKILL.md from line 1 with `sed -n '1,240p'`; a routing line past "
    "the window is found only by a lucky search. Fix the layout, not the wording: "
    "join mid-sentence line wraps above the section (one sentence per line); move a "
    "non-routing section that sits above the router into a reference and leave its "
    "one-line pointer (for example `### Installing the package into a bare workspace` "
    "into references/CLI-LOOP.md); or merge rows. Do not raise a budget without new "
    "read-window evidence."
)


@dataclass(frozen=True)
class Section:
    title: str
    start: int  # 1-based line of the `## ` heading
    end: int  # 1-based last non-blank line before the next H2
    rows: tuple[int, ...]  # 1-based lines of table body rows (no header, no separator)


def _code_mask(lines: list[str]) -> list[bool]:
    """True for fence lines and every line inside a fenced block.

    A closing fence must use the opening character and be at least as long.
    """
    mask = []
    fence = None
    for line in lines:
        m = _FENCE.match(line)
        if m:
            token = m.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            mask.append(True)
            continue
        mask.append(fence is not None)
    return mask


def h2_sections(lines: list[str]) -> list[Section]:
    code = _code_mask(lines)
    heads = []
    for i, line in enumerate(lines):
        if code[i]:
            continue
        m = _H2.match(line)
        if m:
            heads.append((m.group(1), i))
    sections = []
    for k, (title, i) in enumerate(heads):
        stop = heads[k + 1][1] if k + 1 < len(heads) else len(lines)
        end = stop - 1
        while end > i and not lines[end].strip():
            end -= 1
        rows = tuple(
            j + 1
            for j in range(i + 1, stop)
            if not code[j]
            and _TABLE_LINE.match(lines[j])
            and not _TABLE_SEPARATOR.match(lines[j])
            and not (j + 1 < stop and _TABLE_SEPARATOR.match(lines[j + 1]))
        )
        sections.append(Section(title, i + 1, end + 1, rows))
    return sections


def window_problems(text: str, required: tuple[str, ...] = ()) -> list[str]:
    """Every read-window violation in one SKILL.md, as readable lines."""
    lines = text.replace("\r\n", "\n").split("\n")
    code = _code_mask(lines)
    checked = [s for s in h2_sections(lines) if s.title in WINDOWS]
    problems = []

    for title in required:
        if not any(s.title == title for s in checked):
            problems.append(
                f'missing "## {title}": this skill requires it, so a renamed or deleted '
                "section fails here instead of skipping the check"
            )

    for s in checked:
        budget = WINDOWS[s.title]
        if s.end <= budget:
            continue
        message = (
            f'"## {s.title}" (heading at line {s.start}) ends at line {s.end}, '
            f"{s.end - budget} line(s) past the {budget}-line window"
        )
        past = [r for r in s.rows if r > budget]
        if past:
            message += (
                f"; {len(past)} of {len(s.rows)} table rows are past line {budget}, "
                f"the first at line {past[0]}"
            )
        problems.append(message)

    headers = [i + 1 for i, line in enumerate(lines) if not code[i] and _ROUTER_HEADER.match(line)]
    if len(headers) > 1:
        problems.append(
            f"{len(headers)} router header lines (`{ROUTER_HEADER}`) at lines "
            f"{', '.join(map(str, headers))}; the router must stay one table, so no "
            "second table can carry rows past the window"
        )
    if "Supported node types" in required:
        for s in checked:
            if s.title == "Supported node types" and not any(s.start < h <= s.end for h in headers):
                problems.append(
                    f'"## Supported node types" (line {s.start}) has no router header line '
                    f"`{ROUTER_HEADER}`"
                )

    if checked:
        last = max(s.end for s in checked)
        size = len("\n".join(lines[:last]).encode("utf-8"))
        if size > WINDOW_BYTES:
            problems.append(
                f"lines 1-{last} are {size} bytes, {size - WINDOW_BYTES} past the "
                f"{WINDOW_BYTES}-byte ceiling; the line budget must not be met by "
                "packing text onto a few long lines"
            )
    return problems


def window_slack(text: str) -> dict[str, int]:
    """Lines to spare per checked section, plus bytes to spare under the ceiling."""
    lines = text.replace("\r\n", "\n").split("\n")
    checked = [s for s in h2_sections(lines) if s.title in WINDOWS]
    slack = {s.title: WINDOWS[s.title] - s.end for s in checked}
    if checked:
        last = max(s.end for s in checked)
        slack["bytes"] = WINDOW_BYTES - len("\n".join(lines[:last]).encode("utf-8"))
    return slack


def _preview_skills() -> list[str]:
    return sorted(glob.glob(os.path.join(_PREVIEW_SKILLS, "*", "SKILL.md")))


def _skill_id(path: str) -> str:
    return os.path.basename(os.path.dirname(path))


def test_every_required_skill_is_present():
    # Otherwise a moved folder would leave the parametrized test below with
    # nothing to check.
    missing = sorted(set(REQUIRED) - {_skill_id(p) for p in _preview_skills()})
    assert not missing, f"preview skills missing from {_PREVIEW_SKILLS}: {missing}"


@pytest.mark.parametrize("path", _preview_skills(), ids=_skill_id)
def test_real_preview_skills_fit_read_window(path):
    skill = _skill_id(path)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    problems = window_problems(text, REQUIRED.get(skill, ()))
    assert not problems, (
        f"{os.path.relpath(path, _REPO)}:\n  "
        + "\n  ".join(problems)
        + f"\nSlack now: {window_slack(text)}\n{REMEDY}"
    )


# --- synthetic documents ---------------------------------------------------

# The synthetic documents below carry four of the flow skill's required
# sections; the two pointer-only ones (Project layout, Builder frame) have
# their own controls that use the full REQUIRED tuple.
FLOW_REQUIRED = ("Supported node types", "API index", "Lifecycle", "Editing an existing flow")
assert set(FLOW_REQUIRED) <= set(REQUIRED["uipath-maestro-flow"])


def _doc(*blocks: tuple[int, list[str]]) -> str:
    """Place each block so its first line lands on the given 1-based line.

    Gaps are blank lines, which never extend a section (a section ends at its
    last non-blank line).
    """
    out: list[str] = []
    for at, block in blocks:
        assert len(out) < at, f"block at {at} overlaps line {len(out)}"
        out.extend([""] * (at - 1 - len(out)))
        out.extend(block)
    return "\n".join(out) + "\n"


def _section(title: str, body: int = 1) -> list[str]:
    return [f"## {title}", "", *(["Text."] * body)]


def _router(rows: int, title: str = "Supported node types") -> list[str]:
    # Heading, blank, preamble, blank, header, separator, rows.
    return [
        f"## {title}",
        "",
        "The table is the router.",
        "",
        f"{ROUTER_HEADER} Builder |",
        "|---|---|---|",
        *(f"| Row {i} | `node.{i}` | `row{i}()` |" for i in range(rows)),
    ]


def _flow(router_at: int = 40, rows: int = 51) -> list[tuple[int, list[str]]]:
    """A flow skill that passes: H1, Lifecycle, Editing, API index, router."""
    return [
        (1, ["# Flow"]),
        (3, _section("Lifecycle", 3)),
        (10, _section("Editing an existing flow", 3)),
        (20, _section("API index", 10)),
        (router_at, _router(rows)),
    ]


def test_the_passing_shape_passes():
    assert window_problems(_doc(*_flow()), FLOW_REQUIRED) == []


def test_rejects_pure_table_move():
    # The finder's candidate: the router moved above the API index, which then
    # spans lines 235-275. Rows alone would pass; the API index must not.
    text = _doc(
        (1, ["# Flow"]),
        (3, _section("Lifecycle", 3)),
        (10, _section("Editing an existing flow", 3)),
        (20, _router(51)),
        (80, _section("Builder frame", 150)),
        (235, _section("API index", 39)),
        (280, _section("Manual trigger", 3)),
    )
    problems = window_problems(text, FLOW_REQUIRED)
    assert problems == [
        '"## API index" (heading at line 235) ends at line 275, 55 line(s) past the 220-line window'
    ]


_MISSING_ROUTER = (
    'missing "## Supported node types": this skill requires it, so a renamed or deleted '
    "section fails here instead of skipping the check"
)

# 48 lines, ASCII only, so its byte size is len() minus the trailing newline.
_PACKED = _doc(*_flow()[:3], (20, ["## API index", "", "word " * 7000]), (40, _router(3)))

NEGATIVE_CONTROLS = {
    # A single router row one line past the window; the message names it.
    "row-at-221": (
        _doc(*_flow(router_at=215, rows=1)),
        ['"## Supported node types" (heading at line 215) ends at line 221, '
         "1 line(s) past the 220-line window; "
         "1 of 1 table rows are past line 220, the first at line 221"],
    ),
    # The API index ends one line past the window.
    "api-index-ends-221": (
        _doc(*_flow()[:3], (15, _router(3)), (200, _section("API index", 20))),
        ['"## API index" (heading at line 200) ends at line 221, '
         "1 line(s) past the 220-line window"],
    ),
    # A second router table in a later H2 could carry rows past the window.
    "second-router-header": (
        _doc(*_flow(), (150, _router(2, title="More node types"))),
        ["2 router header lines (`| Node or surface | Emitted node type |`) at lines 44, 154; "
         "the router must stay one table, so no second table can carry rows past the window"],
    ),
    # The flow skill with no router section fails; it is not skipped.
    "router-missing": (
        _doc(*_flow()[:4]),
        [_MISSING_ROUTER],
    ),
    # A heading inside a code fence is not a section.
    "router-only-in-fence": (
        _doc(*_flow()[:4], (40, ["```md", *_router(2), "```"])),
        [_MISSING_ROUTER],
    ),
    # The router heading exists but its table sits under another heading.
    "router-header-elsewhere": (
        _doc(
            *_flow()[:4],
            (40, _section("Supported node types", 2)),
            (60, _router(2, title="Nodes")),
        ),
        ['"## Supported node types" (line 40) has no router header line '
         "`| Node or surface | Emitted node type |`"],
    ),
    # A pointer section ends one line past its 240-line window.
    "lifecycle-ends-241": (
        _doc(
            (1, ["# Flow"]),
            (10, _section("Editing an existing flow", 3)),
            (20, _section("API index", 3)),
            (40, _router(3)),
            (230, _section("Lifecycle", 10)),
        ),
        ['"## Lifecycle" (heading at line 230) ends at line 241, '
         "1 line(s) past the 240-line window"],
    ),
    # Every line fits, but only because the text is packed onto long lines.
    "packed-long-lines": (
        _PACKED,
        [f"lines 1-48 are {len(_PACKED) - 1} bytes, {len(_PACKED) - 1 - 32768} past the "
         "32768-byte ceiling; the line budget must not be met by packing text onto a few "
         "long lines"],
    ),
}


@pytest.mark.parametrize("name", sorted(NEGATIVE_CONTROLS))
def test_negative_controls(name):
    text, expected = NEGATIVE_CONTROLS[name]
    assert window_problems(text, FLOW_REQUIRED) == expected


def test_everything_at_the_edge_passes_and_reports_slack():
    # Router ends exactly at 220, Lifecycle exactly at 240: both allowed.
    text = _doc(
        (1, ["# Flow"]),
        (10, _section("Editing an existing flow", 3)),
        (20, _section("API index", 3)),
        (214, _router(1)),
        (231, _section("Lifecycle", 8)),
    )
    assert window_problems(text, FLOW_REQUIRED) == []
    slack = window_slack(text)
    assert slack["Supported node types"] == 0
    assert slack["Lifecycle"] == 0
    assert slack["API index"] == 220 - 24  # heading 20, blank 21, text 22-24
    assert slack["bytes"] > 0


def test_pointer_sections_are_required_and_windowed():
    # The full flow requirement: Builder frame missing, Project layout ending
    # at line 241. Both must be reported, never skipped.
    text = _doc(
        (1, ["# Flow"]),
        (3, _section("Lifecycle", 3)),
        (10, _section("Editing an existing flow", 3)),
        (20, _section("API index", 3)),
        (40, _router(3)),
        (230, _section("Project layout", 10)),
    )
    assert window_problems(text, REQUIRED["uipath-maestro-flow"]) == [
        'missing "## Builder frame": this skill requires it, so a renamed or deleted '
        "section fails here instead of skipping the check",
        '"## Project layout" (heading at line 230) ends at line 241, '
        "1 line(s) past the 240-line window",
    ]
