#!/usr/bin/env python3
"""RpaSingleCase: an rpa task is wired and debug completes successfully."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    assert_task_type_present,
    run_debug,
    task_is_skeleton,
)


def main():
    task = assert_task_type_present("rpa")
    if task_is_skeleton(task):
        sys.exit(
            "FAIL: rpa task is a skeleton — data.name and data.folderPath "
            "are unset. Resolve the HelpDeskLookup registry entry and wire it "
            "into the task; debug cannot run against an unwired reference."
        )
    run_debug(timeout=720)
    print(
        f"OK: rpa task wired (displayName={task.get('displayName')!r}); "
        f"debug finalStatus=Completed"
    )


if __name__ == "__main__":
    main()
