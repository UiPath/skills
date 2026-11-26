"""Stage each task's fixture untouched and see what the graders already pass.

A criterion that passes on a fixture nobody edited awards weight for work the
agent did not do. `graph_extend_brownfield` awarded 5.0 of its 12.0 that way
(MST-18847), which no test would have noticed, because every other test here
asks a grader about a file it was handed rather than about the starting point.

This runs each task's offline graders in a copy of its own fixture and records
exactly which ones pass. Two assertions:

1. Every task with a fixture has at least one criterion that fails on a no-op —
   a task where none does grades nothing the agent does.
2. `PASSES_ON_A_NO_OP` lists every criterion that passes, with why. A new one
   fails this file; so does fixing one without removing its entry. The list is
   the inventory, not an exemption.

Graders that shell out to `uip` are out of scope: they need a CLI and, for the
e2e ones, a tenant. `uip rules validate` passing on a valid fixture is correct
anyway — the fixture is valid, which is the point of staging it.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

SUITE = Path(__file__).resolve().parent.parent

# task yaml (relative to the suite) -> {criterion index: why it passes untouched}
PASSES_ON_A_NO_OP: dict[str, dict[int, str]] = {
    "smoke/graph_extend_brownfield/graph_extend_brownfield.yaml": {
        1: "OPEN, weight 3.0 — `kept` grades only that the fixture's own decisions, ids and "
           "entry points survived, which an untouched fixture satisfies by definition. The "
           "Critical finding of MST-18847 § Grading validity; not closed by that ticket's "
           "non-critical pass.",
        3: "OPEN, weight 2.0 — `diagram` grades only that the fixture's shapes are where they "
           "were and nothing overlaps. Same finding as index 1.",
    },
    "smoke/brownfield_extend/brownfield_extend.yaml": {
        2: "BY DESIGN, weight 1.0 — `rules_check.py names` asserts every row carries an "
           "annotation, and the fixture's four rows already do. It grades the agent's new rows "
           "too, so it is not free weight for a submission that adds any; at 1.0 of 10.5 it is "
           "the supporting weight the tier guidance describes.",
    },
    "smoke/graph_extend_table/graph_extend_table.yaml": {
        4: "BY DESIGN, weight 1.0 — as brownfield_extend index 2, over both decisions.",
    },
}


def _tasks() -> list[tuple[str, dict, list[Path]]]:
    """`(relative yaml path, document, staged source dirs)` for each task staging a fixture."""
    found = []
    for path in sorted(SUITE.rglob("*.yaml")):
        if "__pycache__" in path.parts:
            continue
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(document, dict) or not document.get("success_criteria"):
            continue
        sources = [(path.parent / source["path"]).resolve()
                   for source in ((document.get("sandbox") or {}).get("template_sources") or [])
                   if source.get("type") == "template_dir" and not source.get("mount_point")]
        if sources:
            found.append((path.relative_to(SUITE).as_posix(), document, sources))
    return found


TASKS = _tasks()
IDS = [name for name, _, _ in TASKS]


def _offline_criteria(document: dict, reference: Path) -> list[tuple[int, str, str]]:
    """`(index, description, resolved command)` for each criterion this test can run offline."""
    runnable = []
    for index, criterion in enumerate(document.get("success_criteria") or []):
        command = str(criterion.get("command") or "")
        if "$REFERENCE_DIR" not in command:
            continue
        resolved = command.replace("$REFERENCE_DIR", str(reference)).strip()
        # Needs the CLI, and for `engine` a tenant. Out of scope; see the module docstring.
        if "rules_check.py validate" in resolved or "graph_check.py engine" in resolved:
            continue
        runnable.append((index, str(criterion.get("description") or ""), resolved))
    return runnable


def _stage(sources: list[Path], into: Path) -> None:
    for source in sources:
        for child in source.iterdir():
            if child.is_dir():
                shutil.copytree(child, into / child.name)
            else:
                shutil.copy2(child, into / child.name)


def _run_untouched(name: str, document: dict, sources: list[Path], workspace: Path) -> dict[int, bool]:
    """`{criterion index: passed}` with the fixture staged and not edited."""
    _stage(sources, workspace)
    reference = (SUITE / name).parent / str((document.get("reference") or {}).get("directory") or ".")
    passed = {}
    for index, _, command in _offline_criteria(document, reference.resolve()):
        completed = subprocess.run(command, shell=True, cwd=workspace, capture_output=True,
                                   text=True, timeout=120,
                                   env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        passed[index] = completed.returncode == 0
    return passed


def test_every_task_with_a_fixture_is_collected():
    # Guards the walk: a layout change that stops finding tasks would make this file vacuous.
    assert len(TASKS) >= 7, IDS
    assert set(PASSES_ON_A_NO_OP) <= set(IDS), (
        f"PASSES_ON_A_NO_OP names tasks that are not here: {sorted(set(PASSES_ON_A_NO_OP) - set(IDS))}")


@pytest.mark.parametrize("name,document,sources", TASKS, ids=IDS)
def test_something_grades_the_agents_work(name, document, sources, tmp_path):
    passed = _run_untouched(name, document, sources, tmp_path)
    if not passed:
        pytest.skip("no offline criterion to run")
    assert not all(passed.values()), (
        f"{name}: every offline criterion passes on the untouched fixture, so nothing in this "
        f"task grades what the agent did")


@pytest.mark.parametrize("name,document,sources", TASKS, ids=IDS)
def test_the_no_op_inventory_is_current(name, document, sources, tmp_path):
    passed = _run_untouched(name, document, sources, tmp_path)
    actual = {index for index, ok in passed.items() if ok}
    recorded = set(PASSES_ON_A_NO_OP.get(name, {}))
    criteria = document.get("success_criteria") or []

    def describe(indexes):
        return [f"[{i}] {criteria[i].get('description', '')} (weight {criteria[i].get('weight')})"
                for i in sorted(indexes)]

    assert actual >= recorded, (
        f"{name}: these no longer pass on an untouched fixture — delete their entries from "
        f"PASSES_ON_A_NO_OP:\n  " + "\n  ".join(describe(recorded - actual)))
    assert actual <= recorded, (
        f"{name}: these award weight for work nobody did and are not in the inventory:\n  "
        + "\n  ".join(describe(actual - recorded))
        + "\n\nGrade the edit, not the starting point. If the criterion is supporting weight "
          "that legitimately also covers untouched material, add it to PASSES_ON_A_NO_OP with "
          "that reasoning.")
