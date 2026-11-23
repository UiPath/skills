"""
Behaviour tests for scripts/prune-task-defaults.py: it removes `agent:` /
`run_limits:` / `sandbox:` fields that repeat tests/experiments/default.yaml and
hoists the deprecated `max_turns` / `turn_timeout` / `task_timeout` fields into
`run_limits`.

The script's REPO / DEFAULTS_PATH / TASKS_ROOT are pointed at a tmp_path tree.
The file contents are asserted by parsing the result with PyYAML, so the tests
do not depend on how ruamel.yaml lays out whitespace. ruamel.yaml is not in the
CI test environment (only pytest, pyyaml and coverage are), so when it is
missing a small PyYAML-backed stand-in with the same surface the script uses
(YAML().load/.dump, CommentedMap) is installed for the import.

Run from repo root:
    pytest tests/scripts/test_prune_task_defaults.py
"""

import importlib.util
import io
import sys
import textwrap
import types
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "prune-task-defaults.py"


def plain(value):
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [plain(v) for v in value]
    return value


def _install_ruamel_stand_in():
    class CommentedMap(dict):
        def yaml_set_comment_before_after_key(self, key, before=None, indent=0, after=None, after_indent=None):
            pass

    class YAML:
        def indent(self, **kwargs):
            pass

        def load(self, text):
            data = yaml.safe_load(text)
            return CommentedMap(data) if isinstance(data, dict) else data

        def dump(self, data, stream):
            stream.write(yaml.safe_dump(plain(data), sort_keys=False))

    package = types.ModuleType("ruamel")
    package.__path__ = []
    module = types.ModuleType("ruamel.yaml")
    module.YAML = YAML
    comments = types.ModuleType("ruamel.yaml.comments")
    comments.CommentedMap = CommentedMap
    module.comments = comments
    package.yaml = module
    return {"ruamel": package, "ruamel.yaml": module, "ruamel.yaml.comments": comments}


@pytest.fixture(scope="module")
def prune():
    saved = {name: sys.modules.get(name) for name in ("ruamel", "ruamel.yaml", "ruamel.yaml.comments")}
    try:
        import ruamel.yaml  # noqa: F401
    except ImportError:
        sys.modules.update(_install_ruamel_stand_in())
    spec = importlib.util.spec_from_file_location("prune_task_defaults_behaviour", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    yield module
    for name, original in saved.items():
        if original is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = original


DEFAULTS = """\
defaults:
  agent:
    type: claude
    model: sonnet
  run_limits:
    max_turns: 30
    turn_timeout: 120
  sandbox:
    driver: docker
"""


@pytest.fixture
def tree(prune, tmp_path, monkeypatch):
    root = tmp_path.resolve()
    (root / "tests" / "experiments").mkdir(parents=True)
    (root / "tests" / "experiments" / "default.yaml").write_text(DEFAULTS, encoding="utf-8")
    (root / "tests" / "tasks").mkdir()
    monkeypatch.setattr(prune, "REPO", root)
    monkeypatch.setattr(prune, "DEFAULTS_PATH", root / "tests" / "experiments" / "default.yaml")
    monkeypatch.setattr(prune, "TASKS_ROOT", root / "tests" / "tasks")
    return root


def task(tree, name, body):
    path = tree / "tests" / "tasks" / name
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


def run(prune, monkeypatch, capsys, *args):
    monkeypatch.setattr(sys, "argv", ["prune-task-defaults.py", *map(str, args)])
    rc = prune.main()
    return rc, capsys.readouterr().out


def load(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_fields_equal_to_the_defaults_are_removed_and_reported(prune, tree, monkeypatch, capsys):
    path = task(tree, "a.yaml", """\
        name: a
        agent:
          type: claude
          model: opus
        sandbox:
          driver: docker
        """)
    rc, out = run(prune, monkeypatch, capsys, path)
    assert rc == 0
    rel = path.relative_to(tree)
    assert f"{rel}\n  - drop agent.type (matches default)\n  - drop sandbox.driver (matches default)\n" in out
    assert "  - drop empty sandbox:" in out
    assert "updated 1 / 1 file(s)" in out
    assert load(path) == {"name": "a", "agent": {"model": "opus"}}


def test_empty_collections_carry_no_config_and_are_removed(prune, tree, monkeypatch, capsys):
    path = task(tree, "a.yaml", """\
        name: a
        agent:
          model: opus
          plugins: []
          env: {}
        """)
    _, out = run(prune, monkeypatch, capsys, path)
    assert "drop agent.plugins (empty)" in out
    assert "drop agent.env (empty)" in out
    assert load(path) == {"name": "a", "agent": {"model": "opus"}}


def test_deprecated_agent_limits_are_hoisted_into_a_new_run_limits_block(prune, tree, monkeypatch, capsys):
    path = task(tree, "a.yaml", """\
        name: a
        agent:
          model: opus
          max_turns: 50
        """)
    _, out = run(prune, monkeypatch, capsys, path)
    assert "hoist agent.max_turns → run_limits.max_turns" in out
    assert load(path) == {"name": "a", "agent": {"model": "opus"}, "run_limits": {"max_turns": 50}}


def test_agent_limit_repeating_run_limits_is_dropped_as_a_duplicate(prune, tree, monkeypatch, capsys):
    path = task(tree, "a.yaml", """\
        name: a
        agent:
          model: opus
          max_turns: 50
        run_limits:
          max_turns: 50
        """)
    _, out = run(prune, monkeypatch, capsys, path)
    assert "drop agent.max_turns (duplicate of run_limits.max_turns)" in out
    assert load(path)["run_limits"] == {"max_turns": 50}
    assert "max_turns" not in load(path)["agent"]


def test_conflicting_agent_limit_loses_to_run_limits(prune, tree, monkeypatch, capsys):
    path = task(tree, "a.yaml", """\
        name: a
        agent:
          model: opus
          max_turns: 99
        run_limits:
          max_turns: 50
        """)
    _, out = run(prune, monkeypatch, capsys, path)
    assert "drop agent.max_turns=99 (conflicts with run_limits.max_turns=50; kept run_limits)" in out
    assert load(path)["run_limits"] == {"max_turns": 50}


def test_top_level_limits_are_hoisted_deduplicated_or_dropped_on_conflict(prune, tree, monkeypatch, capsys):
    hoisted = task(tree, "hoisted.yaml", """\
        name: a
        task_timeout: 600
        """)
    duplicate = task(tree, "duplicate.yaml", """\
        name: b
        max_turns: 50
        run_limits:
          max_turns: 50
        """)
    conflict = task(tree, "conflict.yaml", """\
        name: c
        turn_timeout: 300
        run_limits:
          turn_timeout: 200
        """)
    _, out = run(prune, monkeypatch, capsys, hoisted, duplicate, conflict)
    assert "hoist top-level task_timeout → run_limits.task_timeout" in out
    assert "drop top-level max_turns (duplicate of run_limits.max_turns)" in out
    assert "drop top-level turn_timeout=300 (conflicts with run_limits.turn_timeout=200; kept run_limits)" in out
    assert load(hoisted) == {"name": "a", "run_limits": {"task_timeout": 600}}
    assert load(duplicate) == {"name": "b", "run_limits": {"max_turns": 50}}
    assert load(conflict) == {"name": "c", "run_limits": {"turn_timeout": 200}}
    assert "updated 3 / 3 file(s)" in out


def test_run_limits_matching_the_defaults_are_pruned_and_an_empty_block_dropped(prune, tree, monkeypatch, capsys):
    path = task(tree, "a.yaml", """\
        name: a
        run_limits:
          max_turns: 30
          turn_timeout: 120
        """)
    _, out = run(prune, monkeypatch, capsys, path)
    assert "drop run_limits.max_turns (matches default)" in out
    assert "drop empty run_limits:" in out
    assert load(path) == {"name": "a"}


def test_task_that_needs_no_change_is_left_byte_identical(prune, tree, monkeypatch, capsys):
    path = task(tree, "a.yaml", "name: a\nagent:\n  model: opus\n")
    before = path.read_bytes()
    rc, out = run(prune, monkeypatch, capsys, path)
    assert rc == 0
    assert out.strip() == "updated 0 / 1 file(s)"
    assert path.read_bytes() == before


def test_dry_run_reports_without_writing(prune, tree, monkeypatch, capsys):
    path = task(tree, "a.yaml", "name: a\nagent:\n  type: claude\n  model: opus\n")
    before = path.read_bytes()
    _, out = run(prune, monkeypatch, capsys, "--dry-run", path)
    assert "drop agent.type (matches default)" in out
    assert "would update 1 / 1 file(s)" in out
    assert path.read_bytes() == before


def test_a_yaml_that_is_not_a_mapping_is_skipped(prune, tree, monkeypatch, capsys):
    path = task(tree, "list.yaml", "- one\n- two\n")
    before = path.read_bytes()
    _, out = run(prune, monkeypatch, capsys, path)
    assert "updated 0 / 1 file(s)" in out
    assert path.read_bytes() == before


def test_without_paths_every_task_under_the_tasks_root_is_processed(prune, tree, monkeypatch, capsys):
    (tree / "tests" / "tasks" / "sub").mkdir()
    first = task(tree, "a.yaml", "name: a\nagent:\n  type: claude\n")
    nested = tree / "tests" / "tasks" / "sub" / "b.yaml"
    nested.write_text("name: b\nsandbox:\n  driver: docker\n", encoding="utf-8")
    task(tree, "untouched.yaml", "name: c\n")
    _, out = run(prune, monkeypatch, capsys)
    assert "updated 2 / 3 file(s)" in out
    assert load(first) == {"name": "a"}
    assert load(nested) == {"name": "b"}


def test_rewritten_file_never_keeps_runs_of_blank_lines(prune, tree, monkeypatch, capsys):
    path = task(tree, "a.yaml", """\
        name: a

        agent:
          type: claude


        sandbox:
          driver: docker


        description: kept
        """)
    run(prune, monkeypatch, capsys, path)
    text = path.read_text(encoding="utf-8")
    assert "\n\n\n" not in text
    assert load(path) == {"name": "a", "description": "kept"}


def test_load_yaml_returns_the_parser_and_the_parsed_document(prune, tmp_path):
    path = tmp_path / "x.yaml"
    path.write_text("a: 1\n", encoding="utf-8")
    parser, data = prune.load_yaml(path)
    assert data["a"] == 1
    buf = io.StringIO()
    parser.dump(data, buf)
    assert yaml.safe_load(buf.getvalue()) == {"a": 1}
