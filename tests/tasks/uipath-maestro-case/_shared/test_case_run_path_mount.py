"""case_run_path imports from the sandbox mount (/work/references), where the repo tree above it is absent.

_shared.task_types locates the repo with parents[3], which raises there, so it must not be imported.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parent.parent
MOUNTED = ("_shared", "_setup")
IMPORT_SCRIPT = (
    "import sys; sys.path.insert(0, sys.argv[1]); "
    "import _shared.case_run_path as m; "
    "print(len(m.AUTOMATED_TYPES), '_shared.task_types' in sys.modules)"
)


def test_imports_from_a_mount_without_the_repo_tree(tmp_path: Path) -> None:
    references = tmp_path / "work" / "references"
    references.mkdir(parents=True)
    for name in MOUNTED:
        shutil.copytree(
            CASE_ROOT / name, references / name, ignore=shutil.ignore_patterns("__pycache__", "test_*")
        )

    result = subprocess.run(
        [sys.executable, "-I", "-c", IMPORT_SCRIPT, str(references)],
        cwd=references,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    count, imported_repo_module = result.stdout.split()
    assert int(count) > 0
    assert imported_repo_module == "False"
