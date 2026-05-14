#!/usr/bin/env python3
"""AgentSingleCase: an agent task is wired and debug returns the occurrence of the letter 'r' in the input word 'arrow' (2: r, r)."""

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
    task = assert_task_type_present("agent")
    if task_is_skeleton(task):
        sys.exit(
            "FAIL: agent task is a skeleton — debug requires a resolved "
            "CountLetters registry entry with a real taskTypeId"
        )
    payload = run_debug(timeout=600)
    # CountLetters returns the count of the letter 'r' for the input word.
    # 'arrow' → 2. Tight range so a stray digit
    # outside the task output cannot satisfy the assertion.
    hit = assert_output_int_in_range(payload, 2, 2)
    print(
        f"OK: agent task wired (displayName={task.get('displayName')!r}); "
        f"debug returned 'r' letter count {hit} for 'arrow'"
    )


if __name__ == "__main__":
    main()
