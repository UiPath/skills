#!/usr/bin/env python3
"""ApiWorkflowSingleCase: an api-workflow task is wired and debug returns
an integer age in [0, 120] for the input name='tomasz'."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    assert_output_int_in_range,
    assert_task_type_present,
    run_debug,
    task_is_skeleton,
)


def main():
    task = assert_task_type_present("api-workflow")
    if task_is_skeleton(task):
        sys.exit(
            "FAIL: api-workflow task is a skeleton — debug requires a "
            "resolved name-to-age registry entry with a real taskTypeId"
        )
    payload = run_debug(timeout=540)
    age = assert_output_int_in_range(payload, 0, 120)
    print(
        f"OK: api-workflow task wired (displayName={task.get('displayName')!r}); "
        f"debug returned age={age} for 'tomasz'"
    )


if __name__ == "__main__":
    main()
