"""The provenance comments beside BASELINES_PCT must describe today's dataset.

Each baseline in ``tests/scripts/activation_gate.py`` may carry an inline
``# N/M`` saying what was measured and over how many rows. ``M`` is the size of
that skill's positive set, so a set that grows leaves the comment describing a
measurement nobody made — ``# 30/30`` beside a 38-row file, which is what
uipath-rules carried after the decision-graph prompts landed (MST-18847).

Nothing else reads these comments, so nothing else notices. The percentage
itself cannot be checked here: it comes from a run, not from the repo. The
denominator can, and it is the half that rots.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE = REPO_ROOT / "tests" / "scripts" / "activation_gate.py"
DATASET = REPO_ROOT / "tests" / "tasks" / "activation"

# `"uipath-rules": 100,  # 38/38` and `"uipath-bundles": 95,  # 36/37 (97.3%), nearest 5% below`
_ENTRY = re.compile(r'^\s*"(?P<skill>uipath-[a-z-]+)":\s*\d+,\s*#\s*(?P<hit>\d+)/(?P<rows>\d+)',
                    re.M)


def _annotated() -> list[tuple[str, int, int, int]]:
    """`(skill, hits, rows, line)` for each baseline carrying an `# N/M` comment."""
    text = GATE.read_text(encoding="utf-8")
    return [(m["skill"], int(m["hit"]), int(m["rows"]), text[: m.start()].count("\n") + 1)
            for m in _ENTRY.finditer(text)]


def _row_count(skill: str) -> int:
    path = DATASET / f"{skill}.jsonl"
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def test_some_baselines_carry_provenance():
    # Guards the regex itself: a rename that stops matching would otherwise make every
    # assertion below vacuous and the file would pass while checking nothing.
    assert _annotated(), f"no `# N/M` provenance comment found in {GATE.name}"


@pytest.mark.parametrize("skill,hits,rows,line", _annotated(),
                         ids=lambda v: v if isinstance(v, str) else str(v))
def test_the_denominator_is_the_positive_set_size(skill, hits, rows, line):
    actual = _row_count(skill)
    assert rows == actual, (
        f"{GATE.name}:{line} says {hits}/{rows} for {skill}, but "
        f"tests/tasks/activation/{skill}.jsonl holds {actual} rows. Re-measure over the full "
        f"set and update both numbers; do not edit the denominator alone."
    )


@pytest.mark.parametrize("skill,hits,rows,line", _annotated(),
                         ids=lambda v: v if isinstance(v, str) else str(v))
def test_the_numerator_does_not_exceed_the_denominator(skill, hits, rows, line):
    assert hits <= rows, f"{GATE.name}:{line} says {hits}/{rows} for {skill}"
