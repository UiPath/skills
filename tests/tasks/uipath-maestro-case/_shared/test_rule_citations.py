"""Guards on the case skill's `Rule N` citations.

1. Snapshot: every citation still resolves to the rule TITLE it resolved to
   when the snapshot was taken. A correct renumber changes no titles; an
   incorrect one names the file and both rules.
2. Every built tree (default and each flavor) numbers the Critical Rules
   1..N contiguously, and no citation points past them. A flavor override
   that kept an old number lands here -- the studioweb tree once shipped a
   scaffold override still numbered 23 after Rule 4 was inserted, which the
   content-only flavor check cannot see.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import rule_citations as rc  # noqa: E402

TREES = rc.built_trees()

# Flavor trees whose overrides still carry pre-renumbering rule numbers. The
# override files have their own code owner, so their fix ships in its own PR
# (branch fix/studioweb-case-rule-numbers). strict=True: once that PR lands,
# the tree passes, the xfail turns into a failure, and this entry must go.
STALE_FLAVORS: dict[str, str] = {}
VARIANTS = [
    pytest.param(v, marks=pytest.mark.xfail(strict=True, reason=STALE_FLAVORS[v]))
    if v in STALE_FLAVORS else v
    for v in sorted(TREES)
]


def test_citations_resolve_to_the_same_rules_as_the_snapshot():
    expected = json.loads(rc.SNAPSHOT.read_text(encoding="utf-8"))
    actual = rc.canonical_citation_map()
    drift = []
    for path in sorted(set(expected) | set(actual)):
        was, now = expected.get(path, {}), actual.get(path, {})
        for title in sorted(set(was) | set(now)):
            if was.get(title, 0) != now.get(title, 0):
                drift.append(f'{path}: "{title}" cited {was.get(title, 0)}x -> {now.get(title, 0)}x')
    assert not drift, (
        "citations now point at different rules than the snapshot records:\n  "
        + "\n  ".join(drift)
        + "\nIf that is intended, regenerate: python3 tests/tasks/uipath-maestro-case/_shared/"
        "rule_citations.py > tests/tasks/uipath-maestro-case/_shared/rule_citations.json"
    )


def test_there_is_a_flavor_to_check():
    assert len(TREES) >= 2, "expected the default tree plus at least one flavor"


@pytest.mark.parametrize("variant", VARIANTS)
def test_built_tree_numbers_rules_contiguously(variant):
    nums = sorted(rc.rule_titles(TREES[variant]["SKILL.md"]))
    assert len(nums) >= 2, f"{variant}: no numbered Critical Rules found"
    assert nums == list(range(1, len(nums) + 1)), (
        f"{variant}/SKILL.md numbers its rules {nums}; expected 1..{len(nums)}. "
        "A flavor override keeping an old number lands here."
    )


@pytest.mark.parametrize("variant", VARIANTS)
def test_every_citation_resolves_in_built_tree(variant):
    tree = TREES[variant]
    present = set(rc.rule_titles(tree["SKILL.md"]))
    dangling = [f"{rel} cites Rule {n}" for rel in sorted(tree)
                for n in rc.citations(tree[rel]) if n not in present]
    assert not dangling, (
        f"{variant}: citation(s) point at a rule this tree lacks (highest is {max(present)}):\n  "
        + "\n  ".join(dangling)
    )
