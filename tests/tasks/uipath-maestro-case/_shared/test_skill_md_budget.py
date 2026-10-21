"""Byte budget for the case skill's SKILL.md (MST-17096).

SKILL.md is loaded on every invocation, before any reference is opened, so its
size is paid by every build. It went from 38,442 bytes (#3018) to 52,370 in six
weeks with nothing deciding the growth. The budget makes the next increase a
reviewed decision: raise BUDGET_BYTES in the same PR that needs the room, and
say in the PR what the new text earns. Moving detail into a reference that a
phase names is the usual alternative.
"""

from pathlib import Path

BUDGET_BYTES = 52_500
SKILL_MD = Path(__file__).resolve().parents[4] / "skills" / "uipath-maestro-case" / "SKILL.md"


def test_skill_md_fits_its_byte_budget():
    size = len(SKILL_MD.read_bytes())
    assert size <= BUDGET_BYTES, (
        f"skills/uipath-maestro-case/SKILL.md is {size:,} bytes, over its {BUDGET_BYTES:,}-byte budget "
        f"by {size - BUDGET_BYTES:,}. Move the new detail into the reference the phase already names, "
        f"or raise BUDGET_BYTES in this PR and say what the extra always-loaded text earns."
    )
