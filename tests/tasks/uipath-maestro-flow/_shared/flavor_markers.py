"""Build-only flavor markers, as scripts/compose-skill-flavor.mjs treats them.

The composer strips every marker line from each package, so a budget measures
the SKILL.md that ships, not the canonical source. `compose` applies one sparse
override the same way, for budgets on a flavor's shipped file.

Regex only: CI installs only pytest (see test-helpers.yml, pytest-flow-check).
"""

from __future__ import annotations

import re

FLAVOR_MARKER_LINE = re.compile(
    r"^<!--skill-flavor:[a-z0-9]+(?:-[a-z0-9]+)*:(?:start|end)-->\r?\n", re.M
)
_BLOCK = re.compile(
    r"^<!--skill-flavor:([a-z0-9]+(?:-[a-z0-9]+)*):start-->\r?\n.*?"
    r"^<!--skill-flavor:\1:end-->(?:\r?\n|$)",
    re.M | re.S,
)


def shipped(text: str) -> str:
    return FLAVOR_MARKER_LINE.sub("", text)


def compose(canonical: str, override: str) -> str:
    """Canonical text with each override block swapped in, markers stripped."""
    blocks = {m.group(1): m.group(0) for m in _BLOCK.finditer(override)}
    missing = sorted(set(blocks) - {m.group(1) for m in _BLOCK.finditer(canonical)})
    if missing:
        raise ValueError(f"override blocks with no canonical marker: {missing}")
    return shipped(_BLOCK.sub(lambda m: blocks.get(m.group(1), m.group(0)), canonical))
