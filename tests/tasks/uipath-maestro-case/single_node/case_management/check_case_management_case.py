#!/usr/bin/env python3
"""ParentCaseSingle: caseplan.json contains a task whose type is "case-management"."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import assert_task_type_present, task_is_skeleton  # noqa: E402


def main():
    task = assert_task_type_present("case-management")
    skeleton = task_is_skeleton(task)
    print(
        f"OK: case-management task present (displayName={task.get('displayName')!r}, "
        f"skeleton={skeleton})"
    )


if __name__ == "__main__":
    main()
