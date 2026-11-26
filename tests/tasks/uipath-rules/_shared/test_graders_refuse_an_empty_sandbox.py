"""Every grader a task scores on must fail when there is nothing to grade.

A `run_command` criterion is graded on the exit code alone, so a grader that
exits 0 without checking anything awards its whole weight to an agent that
built nothing. That is how `check_graph_formula_and_model_debug.py` shipped
with no `if __name__ == "__main__":` block and a weight-5.0 criterion that
passed unconditionally — the file defined `main()` and never called it.

Running each grader in an empty directory catches the class, not the instance:
no project, no `.dmn`, nothing to find, so the only correct answer is non-zero.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

TASKS = Path(__file__).resolve().parent.parent
# Any grader a criterion runs out of the reference tree, not only the per-task `check_*.py`.
# The shared ones are scored on identically -- `graph_check.py chain LoanRules` is a weight-3.0
# criterion -- and matching the `check_` prefix alone left every one of them unguarded.
COMMAND = re.compile(r"command:\s*[\"']?(?P<cmd>[^\"'\n]*\$REFERENCE_DIR/[^\"'\n]*\.py[^\"'\n]*)")


def graders() -> list[tuple[str, Path, list[str]]]:
    """Every grader a task's criteria run, with the arguments the task passes it."""
    found = []
    for task in sorted(TASKS.rglob("*.yaml")):
        for line in COMMAND.findall(task.read_text(encoding="utf-8")):
            words = line.replace("$REFERENCE_DIR/", "").split()
            script = next(word for word in words if word.endswith(".py"))
            arguments = words[words.index(script) + 1:]
            found.append((f"{task.parent.name}: {script.split('/')[-1]} {' '.join(arguments)}".strip(),
                          TASKS / script, arguments))
    return found


@pytest.mark.parametrize("label,script,arguments", graders(), ids=lambda value: value if isinstance(value, str) else "")
def test_a_grader_refuses_an_empty_sandbox(label, script, arguments, tmp_path):
    assert script.exists(), f"{label}: the task names {script}, which does not exist"
    completed = subprocess.run([sys.executable, str(script), *arguments], cwd=tmp_path,
                               capture_output=True, text=True, timeout=120)
    assert completed.returncode != 0, (
        f"{label}: {script.name} exited 0 in an empty directory, so its criterion scores an agent "
        f"that built nothing. stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
