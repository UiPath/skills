"""The Flow skill's SKILL.md must not grow without an explicit budget bump.

Why this exists. SKILL.md is loaded whole, on the first turn of every run, and
then rides along as cached context on every later turn. In coder-eval run
adhoc-2026-10-01_19-24-36 (n8n vs Flow v2, 27 runs per arm) the 921-line,
55,055-byte SKILL.md cost 21.3K cache-write tokens on the Skill call, and 22 of
27 runs then also read references/CLI-LOOP.md (7.1K more) for the emit-only
loop. With 1.65x the turns, that resident context was the whole 3.7x
cache-read gap against the n8n arm (UiPath/skills#3718).

Where the gap became possible. flow-builder-sdk kept a size gate on this file:
`typescript/tests/skill-router-docs.test.ts` capped every router-governed H2 at
MAX_SECTION_BYTES = 1300 (bytes, not lines: a reflow changes the line count by
a quarter and the token cost by ~1%). flow-builder-sdk #776 (2026-09-23)
deleted that test with the tree it read, and #3624 (09-30) promoted the
921-line file here with no budget at all.

This file re-homes that gate and adds the whole-file budget it never had:

- MAX_BYTES / MAX_LINES for the whole file. Bytes are the real unit (they
  order the same way as tokens); the line cap is set loosely so a reflow
  cannot trip it, and exists so a file of many short lines still has a ceiling.
- MAX_SECTION_BYTES = 1300 for every H2, ported unchanged from the deleted
  gate, with explicit larger budgets in SECTION_BUDGETS for the few sections
  that carry the scaffold, the lifecycle loop and the router.

Raising any number here is a deliberate act: say in the PR what the new text
buys that a reference file could not, and what it costs in tokens. The
estimate uses BYTES_PER_TOKEN = 2.56, measured in the run above (55,055 bytes
-> 21,357 cache-write tokens on the Skill call); it is indicative only.

Regex only: CI installs only pytest (see test-helpers.yml, pytest-flow-check).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.normpath(os.path.join(_HERE, "..", "..", "..", ".."))
SKILL_PATH = os.path.join(_REPO, "skills", "uipath-maestro-flow", "SKILL.md")

# Whole file. Set at the #3718 trim (265 lines, 27,606 bytes, ~10.8K tok) with
# ~5% byte headroom; the line cap is looser on purpose (see above).
MAX_BYTES = 29_000
MAX_LINES = 320

# Per H2, ported from flow-builder-sdk skill-router-docs.test.ts.
MAX_SECTION_BYTES = 1300

# H2 title -> its own byte budget, for the sections that must stay larger.
# Each is the #3718 size plus ~5%.
SECTION_BUDGETS = {
    "Project layout": 8_100,  # scaffold + node choice + connector loop (7,725)
    "Lifecycle": 2_500,  # loop choice + the emit-only command block (2,374)
    "Editing an existing flow": 1_600,  # brownfield pointer + pipeline block (1,495)
    "Builder frame": 2_050,  # vars, return/terminate, expression table (1,930)
    "Supported node types": 9_400,  # the router: 53 rows (8,956)
}

BYTES_PER_TOKEN = 2.56

REMEDY = (
    "SKILL.md is resident context on every turn of every run; growth here is paid "
    "per turn. Move detail that is not needed on every run into the matching "
    "references/ file and leave a one-line routing pointer (the router table row "
    "is usually that pointer). Raise a budget only with a stated reason, in the "
    "same PR, and report the token cost."
)

_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
_H2 = re.compile(r"^##(?!#)\s+(.+?)\s*#*\s*$")


@dataclass(frozen=True)
class Section:
    title: str
    start: int  # 1-based line of the `## ` heading
    size: int  # UTF-8 bytes from the heading to the line before the next H2


def _code_mask(lines: list[str]) -> list[bool]:
    """True for fence lines and every line inside a fenced block."""
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
    heads = [
        (m.group(1), i)
        for i, line in enumerate(lines)
        if not code[i] and (m := _H2.match(line))
    ]
    sections = []
    for k, (title, i) in enumerate(heads):
        stop = heads[k + 1][1] if k + 1 < len(heads) else len(lines)
        size = len("\n".join(lines[i:stop]).encode("utf-8"))
        sections.append(Section(title, i + 1, size))
    return sections


def _tok(size: int) -> int:
    return round(size / BYTES_PER_TOKEN)


def _lines(text: str) -> list[str]:
    lines = text.replace("\r\n", "\n").split("\n")
    if lines and lines[-1] == "":
        lines.pop()  # a trailing newline is not a line
    return lines


def budget_problems(text: str) -> list[str]:
    """Every budget violation in one SKILL.md, as readable lines."""
    lines = _lines(text)
    size = len(text.encode("utf-8"))
    problems = []
    if size > MAX_BYTES:
        problems.append(
            f"SKILL.md is {size} bytes (~{_tok(size)} tok); maximum is {MAX_BYTES} "
            f"(~{_tok(MAX_BYTES)} tok), {size - MAX_BYTES} over"
        )
    if len(lines) > MAX_LINES:
        problems.append(
            f"SKILL.md is {len(lines)} lines; maximum is {MAX_LINES}, "
            f"{len(lines) - MAX_LINES} over"
        )
    for s in h2_sections(lines):
        budget = SECTION_BUDGETS.get(s.title, MAX_SECTION_BYTES)
        if s.size > budget:
            problems.append(
                f'section "## {s.title}" (line {s.start}) is {s.size} bytes '
                f"(~{_tok(s.size)} tok); maximum is {budget}"
            )
    return problems


def budget_slack(text: str) -> dict[str, int]:
    lines = _lines(text)
    return {
        "bytes": MAX_BYTES - len(text.encode("utf-8")),
        "lines": MAX_LINES - len(lines),
    }


def test_flow_skill_fits_budget():
    with open(SKILL_PATH, encoding="utf-8") as f:
        text = f.read()
    problems = budget_problems(text)
    assert not problems, (
        f"{os.path.relpath(SKILL_PATH, _REPO)}:\n  "
        + "\n  ".join(problems)
        + f"\nSlack now: {budget_slack(text)}\n{REMEDY}"
    )


def test_every_named_budget_is_a_real_section():
    # A renamed section would otherwise fall back to 1300 bytes silently, or a
    # stale name would keep a large budget nobody uses.
    with open(SKILL_PATH, encoding="utf-8") as f:
        titles = {s.title for s in h2_sections(_lines(f.read()))}
    stale = sorted(set(SECTION_BUDGETS) - titles)
    assert not stale, f"SECTION_BUDGETS names sections SKILL.md does not have: {stale}"


def test_budgets_are_consistent():
    assert MAX_SECTION_BYTES == 1300  # the deleted gate's value; change it on purpose
    assert sum(SECTION_BUDGETS.values()) < MAX_BYTES


# --- synthetic documents ---------------------------------------------------


def _doc(*sections: tuple[str, int]) -> str:
    """H1 plus one H2 per (title, body bytes), body as one ASCII line."""
    out = ["# Flow", ""]
    for title, body in sections:
        out += [f"## {title}", "", "x" * body, ""]
    return "\n".join(out) + "\n"


def test_small_document_passes():
    assert budget_problems(_doc(("Script", 100), ("Branch", 100))) == []


def test_rejects_whole_file_over_bytes():
    # Many sections, each under its own cap, still add up past the file cap.
    n = MAX_BYTES // 1200 + 1
    text = _doc(*((f"Node {i}", 1200) for i in range(n)))
    problems = budget_problems(text)
    assert len(problems) == 1 and problems[0].startswith("SKILL.md is ")
    assert f"maximum is {MAX_BYTES}" in problems[0]


def test_rejects_whole_file_over_lines():
    text = "# Flow\n" + "x\n" * MAX_LINES
    assert budget_problems(text) == [
        f"SKILL.md is {MAX_LINES + 1} lines; maximum is {MAX_LINES}, 1 over"
    ]


def test_rejects_one_section_over_the_ported_cap():
    # One line wide enough to blow the cap on its own: the case a line cap misses.
    problems = budget_problems(_doc(("Script", MAX_SECTION_BYTES)))
    assert len(problems) == 1
    assert re.fullmatch(
        r'section "## Script" \(line 3\) is \d+ bytes \(~\d+ tok\); maximum is 1300',
        problems[0],
    )


def test_named_section_uses_its_own_budget():
    budget = SECTION_BUDGETS["Lifecycle"]
    assert budget_problems(_doc(("Lifecycle", budget - 50))) == []
    assert len(budget_problems(_doc(("Lifecycle", budget + 1)))) == 1


def test_heading_inside_a_fence_is_not_a_section():
    # The fenced "## Inner" must count toward "## Script", not start a new section.
    text = "# Flow\n\n## Script\n\n```md\n## Inner\n" + "x" * 1300 + "\n```\n"
    problems = budget_problems(text)
    assert len(problems) == 1 and '"## Script"' in problems[0]


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_line_count_ignores_the_trailing_newline(newline):
    text = newline.join(["# Flow"] + ["x"] * (MAX_LINES - 1)) + newline
    assert budget_problems(text) == []
