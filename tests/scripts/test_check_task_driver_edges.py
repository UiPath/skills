"""
Edge-case behaviour of scripts/check-task-driver.py that test_check_task_driver.py
does not exercise: inputs the gate must tolerate (malformed or non-mapping YAML,
odd hook and template_sources shapes) and the location it reports when the
offending line cannot be found in the raw file.

The script is loaded in-process and driven through main(argv); fixtures live in
tmp_path.

Run from repo root:
    pytest tests/scripts/test_check_task_driver_edges.py
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check-task-driver.py"

_spec = importlib.util.spec_from_file_location("check_task_driver_edges", SCRIPT)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


def write(tmp_path, name, text):
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def run(capsys, *paths):
    rc = gate.main([str(p) for p in paths])
    return rc, capsys.readouterr().out


def test_malformed_and_non_mapping_yaml_are_skipped_not_crashed(tmp_path, capsys):
    bad = write(tmp_path, "bad.yaml", "key: [unclosed\n")
    scalar = write(tmp_path, "list.yaml", "- a\n- b\n")
    rc, out = run(capsys, bad, scalar)
    assert rc == 0
    assert "OK — no task pins `sandbox.driver: tempdir`." in out
    assert "OK — no task stages a skill directory via template_sources." in out


def test_a_directory_is_scanned_for_yaml_and_yml(tmp_path, capsys):
    write(tmp_path, "tasks/a.yaml", "sandbox:\n  driver: tempdir\n")
    write(tmp_path, "tasks/nested/b.yml", "sandbox:\n  driver: tempdir\n")
    rc, out = run(capsys, tmp_path / "tasks")
    assert rc == 1
    assert "FAIL — 2 task(s) pin `sandbox.driver: tempdir`:" in out
    assert "a.yaml:2" in out
    assert "b.yml:2" in out


def test_tempdir_pin_the_text_search_cannot_find_is_reported_without_a_line(tmp_path, capsys):
    path = write(tmp_path, "task.yaml", 'sandbox:\n  driver: "tempdir"\n')
    rc, out = run(capsys, path)
    assert rc == 1
    assert f"::error file={path},line=0::Task pins sandbox.driver: tempdir" in out
    assert f"  {path}\n" in out


def test_non_mapping_sandbox_and_odd_template_sources_are_ignored(tmp_path, capsys):
    scalar_sandbox = write(tmp_path, "a.yaml", "sandbox: docker-ish\n")
    odd_sources = write(tmp_path, "b.yaml", "sandbox:\n  template_sources:\n    - just-a-string\n    - path:\n    - 3\n")
    rc, out = run(capsys, scalar_sandbox, odd_sources)
    assert rc == 0
    assert "no task stages a skill directory" in out


def test_docker_pins_are_listed_as_a_note(tmp_path, capsys):
    path = write(tmp_path, "task.yaml", "sandbox:\n  driver: docker\n")
    rc, out = run(capsys, path)
    assert rc == 0
    assert "note: 1 task(s) pin `sandbox.driver: docker` (redundant with the Linux default, harmless — not blocked):" in out


def test_hook_shapes_the_gate_cannot_read_are_ignored(tmp_path, capsys):
    path = write(tmp_path, "nightly.yaml", "\n".join([
        "experiment_id: e",
        "defaults:",
        "  pre_run: not-a-list",
        "  post_run:",
        "    - just-a-string",
        "    - command: 7",
        "    - command: echo single line",
        "variants:",
        "  - plain-string",
        "  - post_run:",
        "      - command: echo variant single line",
        "",
    ]))
    rc, out = run(capsys, path)
    assert rc == 0
    assert "OK — 2 Windows-reachable hook command(s) are single-line." in out


def test_multi_line_hook_with_a_short_first_line_is_reported_without_a_line(tmp_path, capsys):
    path = write(tmp_path, "nightly.yaml", "experiment_id: e\ndefaults:\n  pre_run:\n    - command: |\n        a\n        b\n")
    rc, out = run(capsys, path)
    assert rc == 1
    assert "FAIL — 1 Windows-reachable hook command(s) span multiple lines:" in out
    assert f"::error file={path},line=0::defaults.pre_run[0].command spans multiple lines" in out
    assert f"  {path}  (defaults.pre_run[0].command)" in out
    assert "cmd.exe on the Windows split parses only the first line" in out


def test_multi_line_hook_is_reported_at_the_line_its_first_command_line_starts(tmp_path, capsys):
    path = write(tmp_path, "nightly.yaml", "experiment_id: e\ndefaults:\n  pre_run:\n    - command: |\n        echo first line\n        echo second\n")
    rc, out = run(capsys, path)
    assert rc == 1
    assert f"{path}:5  (defaults.pre_run[0].command)" in out


def test_staged_skill_directory_is_reported_with_the_source_path(tmp_path, capsys):
    path = write(tmp_path, "task.yaml", "sandbox:\n  template_sources:\n    - path: ../../skills/uipath-rpa\n")
    rc, out = run(capsys, path)
    assert rc == 1
    assert "FAIL — 1 task(s) stage a skill directory into the sandbox:" in out
    assert "Task stages a skill directory (../../skills/uipath-rpa) via template_sources" in out
    assert "Arm neutrality" in out


def test_default_root_is_the_live_task_corpus(monkeypatch, tmp_path, capsys):
    write(tmp_path, "t.yaml", "sandbox:\n  driver: tempdir\n")
    monkeypatch.setattr(gate, "DEFAULT_ROOT", tmp_path)
    rc, out = run(capsys)
    assert rc == 1
    assert "t.yaml:2" in out


def test_script_runs_as_a_command(tmp_path):
    path = write(tmp_path, "task.yaml", "sandbox:\n  driver: tempdir\n")
    done = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True, check=False)
    assert done.returncode == 1
    assert "pin `sandbox.driver: tempdir`" in done.stdout
