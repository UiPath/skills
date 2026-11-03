"""
Every test file in tests/scripts/ must be run by a PR check.

GitHub jobs name their pytest files one by one, and `skills:test` in
package.json names its node files one by one, so a new test that nobody adds
to either list passes review and then never runs. Only the nightly coverage
job would notice, and it does not fail anything.

Run from repo root:
    pytest tests/scripts/test_script_tests_run_in_ci.py
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_TESTS = REPO_ROOT / "tests" / "scripts"
WORKFLOWS = REPO_ROOT / ".github" / "workflows"

# Already unrun on main when this guard landed. Wiring them into a job is their
# owners' call (they shell out to sh/bash and read the eval image's Dockerfile);
# remove an entry once a job runs it.
NOT_YET_IN_CI = {
    "tests/scripts/test_dockerfile_connectors_library_pin.py",
    "tests/scripts/test_stage_preview_sdk_workspace.py",
    "tests/scripts/test_stage_shared.py",
    "tests/scripts/test_verb_checkers.py",
}

# `run: pytest …` (with or without a leading `- `), or a `pytest …` line inside
# a `run: |` block — the same shapes scripts/run-coverage.mjs reads.
PYTEST_LINE = re.compile(r"^\s*(?:-\s+)?(?:run:\s*)?pytest\s+(.+)$", re.MULTILINE)


def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _pytest_targets() -> set[str]:
    targets = set()
    for workflow in WORKFLOWS.glob("*.yml"):
        for args in PYTEST_LINE.findall(workflow.read_text(encoding="utf-8")):
            targets.update(arg.rstrip("/") for arg in args.split() if not arg.startswith("-") and arg != "\\")
    return targets


def _runs(target: str, test: str) -> bool:
    return test == target or test.startswith(target + "/")


def test_every_python_script_test_is_run_by_a_workflow():
    targets = _pytest_targets()
    unrun = [
        _rel(path)
        for path in sorted(SCRIPT_TESTS.glob("test_*.py"))
        if _rel(path) not in NOT_YET_IN_CI and not any(_runs(t, _rel(path)) for t in targets)
    ]
    assert not unrun, (
        "no workflow runs these; add them to a `pytest` step in "
        f".github/workflows/test-helpers.yml: {unrun}"
    )


def test_every_node_script_test_is_in_skills_test():
    skills_test = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))["scripts"]["skills:test"]
    listed = set(skills_test.split())
    unrun = [_rel(path) for path in sorted(SCRIPT_TESTS.glob("*.test.mjs")) if _rel(path) not in listed]
    assert not unrun, f"add these to `skills:test` in package.json: {unrun}"


def test_not_yet_in_ci_lists_only_unrun_files():
    targets = _pytest_targets()
    stale = sorted(
        test
        for test in NOT_YET_IN_CI
        if not (REPO_ROOT / test).is_file() or any(_runs(t, test) for t in targets)
    )
    assert not stale, f"remove from NOT_YET_IN_CI (deleted, or now run by a job): {stale}"
