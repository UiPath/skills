"""
Behaviour tests for the CLI-walking half of scripts/build-uip-catalog.py.

Complements test_catalog_build_guards.py (pure guard functions). Here a fake
`uip` is injected at the subprocess boundary or at run_uip, so the walk,
install, snapshot-writing and refusal paths run with no network and no real CLI.

Run from repo root:
    pytest tests/scripts/test_build_uip_catalog.py
"""

import importlib.util
import json
import subprocess
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "build-uip-catalog.py"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = _load("build_uip_catalog_walk", SCRIPT)


def _subs(*names):
    return {"Data": {"Subcommands": [{"Name": n} for n in names]}}


FAKE_CLI = {
    ("--help",): _subs("solution [options]", "help", "or|orchestrator", ""),
    ("tools", "list"): {"Data": []},
    ("solution", "--help"): _subs("list <x>", "pack", "help"),
    ("or", "--help"): _subs("jobs"),
}


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    """Fresh UNWALKABLE set per test, and no real sleeping between retries."""
    monkeypatch.setattr(build, "UNWALKABLE", set())
    monkeypatch.setattr(build.time, "sleep", lambda s: None)


@pytest.fixture
def fake_cli(monkeypatch):
    """Route run_uip through FAKE_CLI; unknown commands behave like a failed help."""
    monkeypatch.setattr(build, "run_uip", lambda args: FAKE_CLI.get(tuple(args)))
    monkeypatch.setattr(build, "get_cli_version", lambda: "1.2.3-dev.4")


def _proc(returncode=0, stdout="", stderr=""):
    return types.SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


# --- run_uip ----------------------------------------------------------------

def test_run_uip_appends_json_output_flag_and_parses_stdout(monkeypatch):
    seen = {}

    def fake_run(cmd, **kwargs):
        seen["cmd"] = cmd
        return _proc(stdout='{"Data": 1}')

    monkeypatch.setattr(build.subprocess, "run", fake_run)
    assert build.run_uip(["tools", "list"]) == {"Data": 1}
    assert seen["cmd"] == ["uip", "tools", "list", "--output", "json"]


def test_run_uip_ignores_free_form_text_after_the_json_document(monkeypatch):
    monkeypatch.setattr(
        build.subprocess, "run",
        lambda cmd, **kw: _proc(stdout='  {"a": 1}\nTypical workflow: do x'))
    assert build.run_uip(["x"]) == {"a": 1}


@pytest.mark.parametrize(
    "proc",
    [_proc(returncode=1, stdout='{"a": 1}'), _proc(stdout="   \n"), _proc(stdout="not json")],
)
def test_run_uip_returns_none_on_failure_empty_or_invalid_output(monkeypatch, proc):
    monkeypatch.setattr(build.subprocess, "run", lambda cmd, **kw: proc)
    assert build.run_uip(["x"]) is None


def test_run_uip_exits_with_install_hint_when_cli_is_missing(monkeypatch):
    def boom(cmd, **kwargs):
        raise FileNotFoundError("uip")

    monkeypatch.setattr(build.subprocess, "run", boom)
    with pytest.raises(SystemExit) as exc:
        build.run_uip(["x"])
    assert "uip CLI not found on PATH" in str(exc.value)


# --- get_cli_version / tool_dist_tag ---------------------------------------

def test_get_cli_version_returns_trimmed_stdout(monkeypatch):
    monkeypatch.setattr(build.subprocess, "run", lambda cmd, **kw: _proc(stdout="1.9.0\n"))
    assert build.get_cli_version() == "1.9.0"


def test_get_cli_version_is_unknown_when_missing_or_empty(monkeypatch):
    monkeypatch.setattr(build.subprocess, "run", lambda cmd, **kw: _proc(stdout=""))
    assert build.get_cli_version() == "unknown"

    def boom(cmd, **kwargs):
        raise FileNotFoundError("uip")

    monkeypatch.setattr(build.subprocess, "run", boom)
    assert build.get_cli_version() == "unknown"


@pytest.mark.parametrize(
    "version, tag",
    [("1.199.0-dev.7923", "dev"), ("1.198.0-preview.84", "preview"),
     ("1.197.1", None), ("1.0.0-", None)],
)
def test_tool_dist_tag_follows_the_cli_prerelease_train(monkeypatch, version, tag):
    monkeypatch.setattr(build, "get_cli_version", lambda: version)
    assert build.tool_dist_tag() == tag


# --- strip_args / _ci -------------------------------------------------------

@pytest.mark.parametrize(
    "name, expected",
    [("list <x> [options]", "list"), ("or|orchestrator", "or"),
     ("pack", "pack"), ("  spaced  ", "spaced")],
)
def test_strip_args(name, expected):
    assert build.strip_args(name) == expected


def test_ci_is_case_insensitive_and_tolerates_non_dicts():
    assert build._ci({"Name": "x"}, "name") == "x"
    assert build._ci({"name": "y"}, "NAME") == "y"
    assert build._ci({"other": 1}, "name") is None
    assert build._ci(None, "name") is None
    assert build._ci({1: "x"}, "name") is None


# --- install_all_tools ------------------------------------------------------

def _install_env(monkeypatch, installed, searchable, npm_results, tag="dev"):
    npm_calls = []

    def fake_run_uip(args):
        if args == ["tools", "list"]:
            return {"Data": [{"Name": n} for n in installed]}
        if args == ["tools", "search"]:
            return {"Data": [{"Name": n} for n in searchable]}
        raise AssertionError(args)

    def fake_run(cmd, **kwargs):
        npm_calls.append(cmd)
        return npm_results(cmd)

    monkeypatch.setattr(build, "run_uip", fake_run_uip)
    monkeypatch.setattr(build, "tool_dist_tag", lambda: tag)
    monkeypatch.setattr(build.subprocess, "run", fake_run)
    return npm_calls


def test_install_all_tools_installs_only_missing_tools_at_the_cli_dist_tag(monkeypatch, capsys):
    calls = _install_env(
        monkeypatch,
        installed=["solution-tool"],
        searchable=["@uipath/solution-tool", "@uipath/maestro-tool", "", "@uipath/tm-tool"],
        npm_results=lambda cmd: _proc(),
    )
    build.install_all_tools()
    assert calls == [
        ["npm", "install", "-g", "@uipath/maestro-tool@dev"],
        ["npm", "install", "-g", "@uipath/tm-tool@dev"],
    ]
    err = capsys.readouterr().err
    assert "installing missing tool @uipath/maestro-tool@dev" in err
    assert "failed" not in err


def test_install_all_tools_uses_plain_name_on_stable_cli(monkeypatch):
    calls = _install_env(
        monkeypatch, installed=[], searchable=["@uipath/a-tool"],
        npm_results=lambda cmd: _proc(), tag=None)
    build.install_all_tools()
    assert calls == [["npm", "install", "-g", "@uipath/a-tool"]]


def test_install_all_tools_reports_a_failed_install_but_continues_when_one_succeeds(monkeypatch, capsys):
    def results(cmd):
        if "@uipath/bad-tool@dev" in cmd:
            return _proc(returncode=1, stderr="E404 not found " + "x" * 400)
        return _proc()

    _install_env(monkeypatch, installed=[],
                 searchable=["@uipath/bad-tool", "@uipath/good-tool"], npm_results=results)
    build.install_all_tools()
    err = capsys.readouterr().err
    assert "  failed: E404 not found" in err
    assert len(err.split("failed: ", 1)[1].splitlines()[0]) == 200


def test_install_all_tools_failure_falls_back_to_stdout_for_the_message(monkeypatch, capsys):
    _install_env(
        monkeypatch, installed=[], searchable=["@uipath/a-tool", "@uipath/b-tool"],
        npm_results=lambda cmd: _proc(returncode=1, stdout="from stdout")
        if "a-tool" in cmd[-1] else _proc())
    build.install_all_tools()
    assert "failed: from stdout" in capsys.readouterr().err


def test_install_all_tools_exits_when_every_install_fails(monkeypatch):
    _install_env(
        monkeypatch, installed=[], searchable=["@uipath/a-tool", "@uipath/b-tool"],
        npm_results=lambda cmd: _proc(returncode=1, stderr="nope"))
    with pytest.raises(SystemExit) as exc:
        build.install_all_tools()
    assert "All 2 tool installs failed" in str(exc.value)
    assert "base-CLI-only catalog" in str(exc.value)


def test_install_all_tools_with_nothing_to_install_is_a_no_op(monkeypatch):
    calls = _install_env(
        monkeypatch, installed=["a-tool"], searchable=["@uipath/a-tool"],
        npm_results=lambda cmd: _proc())
    build.install_all_tools()
    assert calls == []


def test_install_all_tools_tolerates_failed_tool_listings(monkeypatch):
    monkeypatch.setattr(build, "run_uip", lambda args: None)
    monkeypatch.setattr(build, "tool_dist_tag", lambda: None)
    build.install_all_tools()


# --- collect_top_level ------------------------------------------------------

def test_collect_top_level_lists_groups_and_marks_missing_rpa_unwalkable(monkeypatch, capsys, fake_cli):
    verbs, groups = build.collect_top_level()
    assert verbs == groups == {"solution", "or"}
    assert build.UNWALKABLE == {"rpa"}
    assert "platform-specific prefix 'rpa' not exposed" in capsys.readouterr().err


def test_collect_top_level_keeps_rpa_walkable_when_exposed(monkeypatch, capsys):
    cli = {("--help",): _subs("rpa", "solution"), ("tools", "list"): {"Data": []}}
    monkeypatch.setattr(build, "run_uip", lambda args: cli.get(tuple(args)))
    verbs, _ = build.collect_top_level()
    assert verbs == {"rpa", "solution"}
    assert build.UNWALKABLE == set()


def test_collect_top_level_marks_installed_tool_with_missing_prefix_unwalkable(monkeypatch, capsys):
    cli = {
        ("--help",): _subs("rpa", "solution"),
        ("tools", "list"): {"Data": [
            {"Name": "solution-tool", "CommandPrefix": "solution"},
            {"Name": "broken-tool", "CommandPrefix": "tm"},
            {"Name": "no-prefix-tool"},
        ]},
    }
    monkeypatch.setattr(build, "run_uip", lambda args: cli.get(tuple(args)))
    build.collect_top_level()
    assert build.UNWALKABLE == {"tm"}
    assert "tool 'broken-tool': installed but 'tm' is not exposed" in capsys.readouterr().err


def test_collect_top_level_exits_when_help_returns_nothing(monkeypatch):
    monkeypatch.setattr(build, "run_uip", lambda args: None)
    with pytest.raises(SystemExit) as exc:
        build.collect_top_level()
    assert "uip --help returned no JSON" in str(exc.value)


# --- collect_group / expand -------------------------------------------------

def test_collect_group_returns_children_with_group_prefix(fake_cli):
    assert build.collect_group("solution") == {"solution list", "solution pack"}
    assert build.UNWALKABLE == set()


def test_collect_group_retries_a_transient_failure_then_succeeds(monkeypatch, capsys):
    attempts = []

    def flaky(args):
        attempts.append(args)
        return None if len(attempts) < 3 else _subs("child")

    monkeypatch.setattr(build, "run_uip", flaky)
    assert build.collect_group("grp") == {"grp child"}
    assert len(attempts) == 3
    err = capsys.readouterr().err
    assert "help walk failed (attempt 1/3)" in err
    assert "(attempt 2/3)" in err
    assert build.UNWALKABLE == set()


def test_collect_group_marks_group_unwalkable_after_exhausting_attempts(monkeypatch, capsys):
    sleeps = []
    monkeypatch.setattr(build.time, "sleep", sleeps.append)
    monkeypatch.setattr(build, "run_uip", lambda args: None)
    assert build.collect_group("grp sub") == set()
    assert build.UNWALKABLE == {"grp sub"}
    assert sleeps == [1.0, 2.0]
    assert "group 'grp sub': unwalkable after 3 attempt(s)" in capsys.readouterr().err


def test_collect_group_treats_a_failure_result_as_unwalkable(monkeypatch):
    monkeypatch.setattr(build, "run_uip", lambda args: {"Result": "Failure"})
    assert build.collect_group("grp") == set()
    assert build.UNWALKABLE == {"grp"}


def test_expand_walks_the_whole_tree(fake_cli):
    verbs = build.expand({"solution", "or"}, {"solution", "or"})
    assert verbs == {"solution", "or", "solution list", "solution pack", "or jobs"}
    # Leaves emit no JSON help in the fake CLI, so they end up unwalkable.
    assert {"solution list", "solution pack", "or jobs"} <= build.UNWALKABLE


# --- main -------------------------------------------------------------------

@pytest.fixture
def run_main(monkeypatch, capsys, tmp_path, fake_cli):
    monkeypatch.setattr(build, "REPO_ROOT", tmp_path)
    output = tmp_path / "assets" / "catalog.json"

    def run(*argv, use_default_output=True):
        args = ["build-uip-catalog.py", *argv]
        if use_default_output:
            args += ["--output", str(output)]
        monkeypatch.setattr(sys, "argv", args)
        code = 0
        try:
            build.main()
        except SystemExit as exc:
            code = exc.code
        captured = capsys.readouterr()
        return code, captured.out, captured.err

    run.output = output
    return run


def test_main_writes_sorted_snapshot_and_reports_summary(run_main):
    code, out, _ = run_main()
    assert code == 0
    data = json.loads(run_main.output.read_text())
    assert data["verbs"] == ["or", "or jobs", "solution", "solution list", "solution pack"]
    assert data["cli_version"] == "1.2.3-dev.4"
    assert "rpa" in data["unwalkable_groups"]
    assert data["generated_at"].endswith("Z")
    assert out.strip() == (
        f"Wrote 5 verbs from uip 1.2.3-dev.4 to {Path('assets') / 'catalog.json'}")


def test_main_stdout_mode_prints_json_and_writes_nothing(run_main):
    code, out, _ = run_main("--stdout")
    assert code == 0
    assert json.loads(out)["verbs"][0] == "or"
    assert not run_main.output.exists()


def test_main_install_tools_flag_runs_the_installer_first(monkeypatch, run_main):
    calls = []
    monkeypatch.setattr(build, "install_all_tools", lambda: calls.append("installed"))
    run_main("--install-tools")
    assert calls == ["installed"]


def test_main_does_not_install_tools_by_default(monkeypatch, run_main):
    monkeypatch.setattr(build, "install_all_tools", lambda: pytest.fail("must not install"))
    assert run_main()[0] == 0


@pytest.mark.parametrize("frac", ["1.5", "-0.1"])
def test_main_rejects_out_of_range_max_drop_frac(run_main, frac):
    code, _, _ = run_main("--max-drop-frac", frac)
    assert "--max-drop-frac must be between 0 and 1" in str(code)
    assert not run_main.output.exists()


def test_main_refuses_to_write_below_the_verb_floor(run_main):
    code, _, _ = run_main("--min-verbs", "500")
    assert "Refusing to write catalog: only 5 verbs collected (< floor 500)" in str(code)
    assert not run_main.output.exists()


def _seed_snapshot(path, verbs, unwalkable):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"verbs": verbs, "unwalkable_groups": unwalkable}))


def test_main_refuses_a_collapse_against_the_committed_snapshot(run_main):
    _seed_snapshot(run_main.output, [f"v{i}" for i in range(100)], [])
    before = run_main.output.read_text()
    code, _, _ = run_main("--max-drop-frac", "0.2")
    assert "verb count dropped 100 -> 5" in str(code)
    assert run_main.output.read_text() == before


def test_main_ignores_a_corrupt_previous_snapshot(run_main):
    run_main.output.parent.mkdir(parents=True)
    run_main.output.write_text("{not json")
    code, _, _ = run_main("--max-drop-frac", "0.2")
    assert code == 0
    assert json.loads(run_main.output.read_text())["verbs"]


def _regressing_snapshot(path):
    # `or jobs` was a walked group in the committed snapshot (it had children);
    # in this build it is a leaf that fails to walk.
    _seed_snapshot(path, ["or", "or jobs", "or jobs list", "solution"], ["rpa"])


def test_main_refuses_when_a_previously_walked_group_becomes_unwalkable(run_main):
    _regressing_snapshot(run_main.output)
    before = run_main.output.read_text()
    code, _, _ = run_main()
    message = str(code)
    assert "Refusing to write catalog: 1 group(s) walked in the committed snapshot" in message
    assert "'or jobs' (-1: or jobs list)" in message
    assert "--allow-unwalkable-regression" in message
    assert run_main.output.read_text() == before


def test_main_accepts_the_regression_with_a_warning_when_allowed(run_main):
    _regressing_snapshot(run_main.output)
    code, out, err = run_main("--allow-unwalkable-regression")
    assert code == 0
    assert "warning: accepting unwalkable regression" in err
    assert "Wrote 5 verbs" in out
    assert "or jobs" in json.loads(run_main.output.read_text())["unwalkable_groups"]


def test_main_compares_against_no_snapshot_when_writing_to_stdout(run_main):
    _seed_snapshot(run_main.output, [f"v{i}" for i in range(100)], [])
    code, out, _ = run_main("--stdout", "--max-drop-frac", "0.2")
    assert code == 0
    assert json.loads(out)["cli_version"] == "1.2.3-dev.4"


# --- the script as a real process ------------------------------------------

def test_script_exits_nonzero_when_the_uip_cli_is_not_installed(tmp_path):
    """With an empty PATH the first run_uip call cannot find `uip`."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--stdout"],
        capture_output=True, text=True, check=False,
        env={"PATH": str(tmp_path), "SYSTEMROOT": "C:\\Windows"},
    )
    assert proc.returncode != 0
    assert "uip CLI not found on PATH" in proc.stderr
