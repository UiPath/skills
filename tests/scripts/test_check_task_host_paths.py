"""
Behaviour tests for scripts/check-task-host-paths.py, the one-way ratchet that
blocks NEW $TASK_DIR / $SKILLS_REPO_PATH references under tests/tasks/.

Each test builds a throwaway git repository in tmp_path (the script diffs with
git), points the script at it, and asserts the exit code and the output.

Run from repo root:
    pytest tests/scripts/test_check_task_host_paths.py
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check-task-host-paths.py"

_spec = importlib.util.spec_from_file_location("check_task_host_paths_behaviour", SCRIPT)
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)


def git(repo, *args):
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false", *args],
        cwd=repo, check=True, capture_output=True, text=True,
    )


def put(repo, rel, text):
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A git repo on `main` whose tests/tasks already holds one documented old reference."""
    root = tmp_path.resolve() / "repo"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "symbolic-ref", "HEAD", "refs/heads/main")
    put(root, "tests/tasks/a/old.yaml", "name: old\nrun: cat $TASK_DIR/legacy.txt\n")
    put(root, "tests/tasks/a/gone.yaml", "run: cat $SKILLS_REPO_PATH/x\n")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base")
    git(root, "checkout", "-q", "-b", "feature")
    monkeypatch.setattr(guard, "REPO_ROOT", root)
    return root


def commit_all(repo):
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "change")


def run(repo, *flags):
    return guard.main([str(repo / "tests" / "tasks"), *flags])


def test_diff_with_no_added_reference_passes(repo, capsys):
    put(repo, "tests/tasks/a/new.yaml", "run: echo clean\n")
    commit_all(repo)
    assert run(repo, "--base-ref", "main") == 0
    assert "OK — no $TASK_DIR/$SKILLS_REPO_PATH references (diff vs main)." in capsys.readouterr().out


def test_preexisting_references_are_not_reported(repo, capsys):
    put(repo, "tests/tasks/a/old.yaml", "name: renamed\nrun: cat $TASK_DIR/legacy.txt\n")
    commit_all(repo)
    assert run(repo, "--base-ref", "main") == 0
    capsys.readouterr()


def test_added_references_fail_with_file_line_and_annotation(repo, capsys):
    put(repo, "tests/tasks/a/new.yaml", "name: new\nrun: |\n  cat $SKILLS_REPO_PATH/data\n")
    put(repo, "tests/tasks/a/old.yaml", "name: old\nrun: cat $TASK_DIR/legacy.txt\nextra: $TASK_DIR/more\n")
    commit_all(repo)
    assert run(repo, "--base-ref", "main") == 1
    out = capsys.readouterr().out
    assert "FAIL — 2 $TASK_DIR/$SKILLS_REPO_PATH reference(s) found under" in out
    assert "::error file=tests/tasks/a/new.yaml,line=3::retired $TASK_DIR/$SKILLS_REPO_PATH reference" in out
    assert "  tests/tasks/a/new.yaml:3  cat $SKILLS_REPO_PATH/data" in out
    assert "::error file=tests/tasks/a/old.yaml,line=3::" in out
    assert "sandbox.template_sources" in out
    assert "$REFERENCE_DIR" in out


def test_exempt_meta_test_may_mention_the_tokens(repo, capsys):
    put(repo, "tests/tasks/a/test_criterion_budgets.py", "# mentions $TASK_DIR and $SKILLS_REPO_PATH\n")
    commit_all(repo)
    assert run(repo, "--base-ref", "main") == 0
    capsys.readouterr()


def test_deleting_a_file_with_references_is_not_a_hit(repo, capsys):
    (repo / "tests" / "tasks" / "a" / "gone.yaml").unlink()
    commit_all(repo)
    assert run(repo, "--base-ref", "main") == 0
    capsys.readouterr()


def test_unknown_base_ref_exits_with_the_git_error(repo):
    with pytest.raises(SystemExit) as exc:
        run(repo, "--base-ref", "no-such-ref")
    assert "could not resolve merge-base against 'no-such-ref'" in str(exc.value)


def test_full_scan_reports_every_occurrence_but_skips_exempt_and_bytecode(repo, capsys):
    put(repo, "tests/tasks/a/test_criterion_budgets.py", "$TASK_DIR\n")
    put(repo, "tests/tasks/a/__pycache__/mod.cpython-313.pyc", "$TASK_DIR\n")
    put(repo, "tests/tasks/a/cached.pyc", "$TASK_DIR\n")
    assert run(repo, "--full") == 1
    out = capsys.readouterr().out
    assert "FAIL — 2 $TASK_DIR/$SKILLS_REPO_PATH reference(s) found under" in out
    assert f"{Path('tests/tasks/a/old.yaml')}:2  run: cat $TASK_DIR/legacy.txt" in out
    assert f"{Path('tests/tasks/a/gone.yaml')}:1" in out
    assert "budgets" not in out
    assert "pycache" not in out


def test_full_scan_of_a_clean_tree_passes(repo, capsys):
    for name in ("old.yaml", "gone.yaml"):
        (repo / "tests" / "tasks" / "a" / name).write_text("run: echo hi\n", encoding="utf-8")
    assert run(repo, "--full") == 0
    assert "OK — no $TASK_DIR/$SKILLS_REPO_PATH references (full scan)." in capsys.readouterr().out


def test_missing_root_exits_with_a_message(repo):
    with pytest.raises(SystemExit) as exc:
        guard.main([str(repo / "no-such-dir")])
    assert "root not found" in str(exc.value)


def test_a_path_outside_the_repo_is_reported_as_given(tmp_path):
    outside = tmp_path / "elsewhere" / "task.yaml"
    assert guard._rel(str(outside)) == str(outside)


def test_script_runs_as_a_command_in_full_mode(tmp_path):
    root = tmp_path / "tasks"
    root.mkdir()
    (root / "bad.yaml").write_text("run: $TASK_DIR/x\n", encoding="utf-8")
    done = subprocess.run([sys.executable, str(SCRIPT), "--full", str(root)], capture_output=True, text=True, check=False)
    assert done.returncode == 1
    assert "bad.yaml:1  run: $TASK_DIR/x" in done.stdout
