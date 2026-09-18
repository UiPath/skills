"""nightly-claude.yaml is nightly.yaml with exactly one delta: run_limits.

The two files must not drift anywhere else — nightly.yaml carries load-bearing
config (the cmd.exe-safe pre_run polyglot, docker env passthrough, the judge
route) that would fail the claude arm silently if a copy went stale. Nothing
else in the build reads both files, so this guard is the only thing that
notices.
"""

from __future__ import annotations

import copy
from pathlib import Path

import yaml

EXPERIMENTS = Path(__file__).resolve().parents[1] / "experiments"

# The one intentional difference. The claude-code harness streams the whole
# session as one turn, so turn_timeout is its effective wall budget (#3376).
CLAUDE_RUN_LIMITS = {"max_turns": 200, "task_timeout": 2400, "turn_timeout": 1800}
SHARED_RUN_LIMITS = {"max_turns": 200, "task_timeout": 1200, "turn_timeout": 900}


def _load(name: str) -> dict:
    with open(EXPERIMENTS / name, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_run_limits_carry_the_intended_values() -> None:
    assert _load("nightly.yaml")["defaults"]["run_limits"] == SHARED_RUN_LIMITS
    assert _load("nightly-claude.yaml")["defaults"]["run_limits"] == CLAUDE_RUN_LIMITS


def test_task_timeout_covers_the_turn_in_both() -> None:
    # task_timeout silently caps the turn (orchestrator arms it around agent +
    # grading), so task >= turn must hold in every experiment default.
    for name in ("nightly.yaml", "nightly-claude.yaml"):
        limits = _load(name)["defaults"]["run_limits"]
        assert limits["task_timeout"] >= limits["turn_timeout"], name


def test_everything_else_is_identical() -> None:
    nightly = _load("nightly.yaml")
    claude = _load("nightly-claude.yaml")

    for config in (nightly, claude):
        config.pop("experiment_id")
        config.pop("description")
        config["defaults"].pop("run_limits")

    assert copy.deepcopy(nightly) == copy.deepcopy(claude), (
        "nightly-claude.yaml drifted from nightly.yaml outside run_limits — "
        "mirror the nightly.yaml change (or revert the stray edit)"
    )


def test_ids_are_distinct() -> None:
    assert _load("nightly.yaml")["experiment_id"] == "skill-tests-nightly"
    assert _load("nightly-claude.yaml")["experiment_id"] == "skill-tests-nightly-claude"
