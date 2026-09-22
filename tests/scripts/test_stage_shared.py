"""Regression tests for staging shared checker helpers."""

import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).with_name("stage_shared.sh")


def test_stage_shared_anchors_to_checkout_and_stages_nested_checkers(tmp_path):
    repo = tmp_path / "skills"
    script = repo / "tests" / "scripts" / "stage_shared.sh"
    shared = repo / "tests" / "tasks" / "example" / "_shared"
    shallow = repo / "tests" / "tasks" / "example" / "scenario"
    nested = repo / "tests" / "tasks" / "example" / "nested" / "scenario"
    unrelated_shared = repo / "tests" / "tasks" / "unrelated" / "_shared"
    unrelated_task = repo / "tests" / "tasks" / "unrelated" / "scenario"

    script.parent.mkdir(parents=True)
    shared.mkdir(parents=True)
    shallow.mkdir(parents=True)
    nested.mkdir(parents=True)
    unrelated_shared.mkdir(parents=True)
    unrelated_task.mkdir(parents=True)
    shutil.copy2(SCRIPT, script)
    (shared / "__init__.py").write_text("", encoding="utf-8")
    (shared / "checker.py").write_text("VALUE = 42\n", encoding="utf-8")
    checker = "from _shared.checker import VALUE\nassert VALUE == 42\n"
    (shallow / "check.py").write_text(checker, encoding="utf-8")
    (nested / "check.py").write_text(checker, encoding="utf-8")
    (unrelated_shared / "__init__.py").write_text("", encoding="utf-8")
    (unrelated_shared / "checker.py").write_text("VALUE = 42\n", encoding="utf-8")
    (unrelated_task / "check.py").write_text(checker, encoding="utf-8")

    subprocess.run(["git", "init", "--quiet", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)

    manifest = tmp_path / "staged-paths.txt"
    first = subprocess.run(
        [
            "env",
            f"STAGE_SHARED_MANIFEST={manifest}",
            "STAGE_SHARED_ROOT=tests/tasks/example",
            "bash",
            str(script),
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    second = subprocess.run(
        ["env", "STAGE_SHARED_ROOT=tests/tasks/example", "bash", str(script)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "co-located _shared into 2 task dir(s)" in first.stdout
    assert "co-located _shared into 0 task dir(s)" in second.stdout
    assert manifest.read_text(encoding="utf-8").splitlines() == [
        str(nested / "_shared"),
        str(shallow / "_shared"),
    ]
    for task in (shallow, nested):
        assert (task / "_shared" / "checker.py").read_text(encoding="utf-8") == "VALUE = 42\n"
        subprocess.run([sys.executable, str(task / "check.py")], cwd=tmp_path, check=True)
    assert not (unrelated_task / "_shared").exists()
