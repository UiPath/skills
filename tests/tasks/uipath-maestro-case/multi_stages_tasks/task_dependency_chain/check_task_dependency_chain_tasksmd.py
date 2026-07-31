#!/usr/bin/env python3
"""TaskDependencyChain (advisory): tasks.md T-entry format for sequential tasks.

Non-gating companion to check_task_dependency_chain.py — see
task_dependency_chain.yaml (pass_threshold: 0). Checks the Phase 1 planning
artifact (tasks.md) quotes the "First Step"/"Second Step" display names in
their T-entry headings and exposes `activation-mode: sequential` /
`entry-rule: runs-sequentially`, per uipath-maestro-case SKILL.md Rule 6.
Failing this does not fail the task — caseplan.json correctness (validated by
check_task_dependency_chain.py) is the gating signal.
"""

import glob
import re
import sys


def _read_all_tasks_md() -> str:
    matches = sorted(
        p for p in glob.glob("**/tasks.md", recursive=True) if "/.venv/" not in p
    )
    if not matches:
        sys.exit("FAIL: no tasks.md found; Phase 1 planning artifact is required")
    chunks = []
    for path in matches:
        with open(path, encoding="utf-8") as f:
            chunks.append(f"\n<!-- {path} -->\n" + f.read())
    return "\n".join(chunks)


def _task_plan_section(tasks_md: str, task_name: str) -> str:
    pattern = re.compile(
        rf"(?ims)^##\s+T\d+:.*?\"{re.escape(task_name)}\".*?(?=^##\s+T\d+:|\Z)"
    )
    match = pattern.search(tasks_md)
    if not match:
        sys.exit(f"FAIL: tasks.md has no T-entry for task {task_name!r}")
    return match.group(0)


def _assert_plan_sequential_mode(tasks_md: str, task_name: str) -> None:
    section = _task_plan_section(tasks_md, task_name)
    if not re.search(r"(?im)^-\s*activation-mode:\s*sequential\s*$", section):
        sys.exit(
            f"FAIL: tasks.md T-entry for {task_name!r} must expose "
            "`activation-mode: sequential`"
        )
    if not re.search(r"(?im)^-\s*entry-rule:\s*runs-sequentially\s*$", section):
        sys.exit(
            f"FAIL: tasks.md T-entry for {task_name!r} must expose "
            "`entry-rule: runs-sequentially`"
        )
    if re.search(r"(?im)^-\s*entry-rule:\s*selected-tasks-completed\b", section):
        sys.exit(
            f"FAIL: tasks.md T-entry for {task_name!r} models an immediate "
            "ordered step as selected-tasks-completed instead of runs-sequentially"
        )


def main():
    tasks_md = _read_all_tasks_md()
    for name in ("First Step", "Second Step"):
        _assert_plan_sequential_mode(tasks_md, name)
    print(
        "OK: tasks.md T-entries for First Step/Second Step quote the display "
        "name and expose activation-mode: sequential / entry-rule: runs-sequentially"
    )


if __name__ == "__main__":
    main()
