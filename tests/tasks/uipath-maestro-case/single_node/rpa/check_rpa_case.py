#!/usr/bin/env python3
"""RpaSingleCase: an rpa task is wired and debug completes successfully."""

import os
import sys

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-maestro-case")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, _shared_root)
from _shared.case_check import (  # noqa: E402
    assert_task_type_present,
    run_debug,
    task_is_skeleton,
)


def main():
    task = assert_task_type_present("rpa")
    if task_is_skeleton(task):
        sys.exit(
            "FAIL: rpa task is a skeleton — debug requires a resolved "
            "HelpDeskLookup registry entry with a real taskTypeId"
        )
    run_debug(timeout=720)
    print(
        f"OK: rpa task wired (displayName={task.get('displayName')!r}); "
        f"debug finalStatus=Completed"
    )


if __name__ == "__main__":
    main()
