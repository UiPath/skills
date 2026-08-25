"""Regression tests for staging shared checker helpers."""

import shutil
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).with_name("stage_shared.sh")


def test_stage_shared_resolves_its_checkout_from_the_script_path(tmp_path):
    repo = tmp_path / "skills"
    script = repo / "tests" / "scripts" / "stage_shared.sh"
    shared = repo / "tests" / "tasks" / "example" / "_shared"
    task = repo / "tests" / "tasks" / "example" / "scenario"

    script.parent.mkdir(parents=True)
    shared.mkdir(parents=True)
    task.mkdir(parents=True)
    shutil.copy2(SCRIPT, script)
    (shared / "__init__.py").write_text("", encoding="utf-8")
    (shared / "checker.py").write_text("VALUE = 42\n", encoding="utf-8")
    (task / "check.py").write_text("from _shared.checker import VALUE\n", encoding="utf-8")

    subprocess.run(["git", "init", "--quiet", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)

    first = subprocess.run(
        ["bash", str(script)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    second = subprocess.run(
        ["bash", str(script)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "co-located _shared into 1 task dir(s)" in first.stdout
    assert "co-located _shared into 0 task dir(s)" in second.stdout
    assert (task / "_shared" / "checker.py").read_text(encoding="utf-8") == "VALUE = 42\n"
