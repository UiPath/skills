#!/usr/bin/env python3
"""RpaSingleCase: caseplan.json contains exactly one task whose type is "rpa"."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import assert_task_type_present, task_is_skeleton  # noqa: E402


def main():
    task = assert_task_type_present("rpa")
    skeleton = task_is_skeleton(task)
    print(
        f"OK: rpa task present (displayName={task.get('displayName')!r}, "
        f"skeleton={skeleton})"
    )


if __name__ == "__main__":
    main()
