#!/usr/bin/env python3
"""ParentCaseSingle: a resolved case-management (nested case) task is wired and
debug completes successfully."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    assert_task_type_present,
    run_debug,
    task_is_skeleton,
)


def main():
    task = assert_task_type_present("case-management")
    if task_is_skeleton(task):
        sys.exit(
            "FAIL: case-management task is a skeleton — debug requires a "
            "resolved CaseTest registry entry with a real taskTypeId"
        )
    run_debug(timeout=540)
    print(
        f"OK: case-management task wired (displayName={task.get('displayName')!r}); "
        f"debug finalStatus=Completed"
    )


if __name__ == "__main__":
    main()
