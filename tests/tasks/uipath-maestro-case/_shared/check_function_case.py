#!/usr/bin/env python3
"""FunctionSingleCase: a function task is bound as a Function in the SDD's
folder, and debug completes successfully."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import (  # noqa: E402
    assert_task_type_present,
    get_bindings,
    read_caseplan,
    run_debug,
    task_is_skeleton,
)

EXPECTED_FOLDER = "Shared/acme-echo"


def _binding_for(ref: object, bindings: list[dict]) -> dict:
    if not isinstance(ref, str) or not ref.startswith("=bindings."):
        sys.exit(f"FAIL: function task reference {ref!r} is not a =bindings.<id> reference.")
    binding_id = ref[len("=bindings."):]
    for b in bindings:
        if b.get("id") == binding_id:
            return b
    sys.exit(f"FAIL: function task references binding {binding_id!r}, which is not in bindings[].")


def main():
    task = assert_task_type_present("function")
    if task_is_skeleton(task):
        sys.exit(
            "FAIL: function task is a skeleton — data.name and data.folderPath "
            "are unset. Resolve the acme-echo function-index.json entry and wire "
            "it into the task; debug cannot run against an unwired reference."
        )

    bindings = get_bindings(read_caseplan())
    data = task.get("data") or {}
    for attr in ("name", "folderPath"):
        b = _binding_for(data.get(attr), bindings)
        if b.get("resourceSubType") != "Function":
            sys.exit(
                f"FAIL: {attr} binding has resourceSubType={b.get('resourceSubType')!r}; "
                "a function task binds with resourceSubType 'Function'."
            )
    folder = _binding_for(data.get("folderPath"), bindings).get("default")
    if folder != EXPECTED_FOLDER:
        sys.exit(
            f"FAIL: folderPath binding default is {folder!r}, expected {EXPECTED_FOLDER!r}. "
            "acme-echo is deployed in six folders; the SDD's folder selects which one."
        )

    run_debug(timeout=540)
    print(
        f"OK: function task wired (displayName={task.get('displayName')!r}, "
        f"folder={folder!r}); debug finalStatus=Completed"
    )


if __name__ == "__main__":
    main()
