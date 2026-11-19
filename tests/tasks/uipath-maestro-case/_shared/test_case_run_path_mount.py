"""case_run_path imports from the sandbox mount (/work/references), where the repo tree above it is absent.

Modules that locate the repo with parents[N] (like _shared.task_types) raise there, so the
_shared import closure stays within ALLOWED_SHARED.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parent.parent
MOUNTED = ("_shared", "_setup")
ALLOWED_SHARED = {"_shared", "_shared.case_check", "_shared.case_run_path"}
IMPORT_SCRIPT = (
    "import sys; sys.path.insert(0, sys.argv[1]); "
    "import _shared.case_run_path as m; "
    "print(len(m.AUTOMATED_TYPES), *sorted(k for k in sys.modules if k.startswith('_shared')))"
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
    count, *shared = result.stdout.split()
    assert int(count) > 0
    assert set(shared) <= ALLOWED_SHARED, sorted(set(shared) - ALLOWED_SHARED)
