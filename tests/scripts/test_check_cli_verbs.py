"""
Behaviour tests for scripts/check-cli-verbs.py.

Complements test_verb_checkers.py. The catalog and renames paths are module
constants, so tests point them at fixtures under tmp_path and drive main()
with argv, asserting exit code, stdout/stderr and the report file.

Run from repo root:
    pytest tests/scripts/test_check_cli_verbs.py
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cv = _load("check_cli_verbs_behaviour", REPO_ROOT / "scripts" / "check-cli-verbs.py")

CATALOG = {
    "cli_version": "7.7.7",
    "verbs": ["solution", "solution init", "solution list", "maestro",
              "maestro flow", "maestro flow init"],
}

RENAMES_MD = """# Retired verbs

| Retired                | Canonical            | Retired at |
|------------------------|----------------------|------------|
| `flow`                 | `maestro flow`       | uip 1.2.0  |
| `solution new`         | `solution init`      | uip 1.2.0  |
"""


@pytest.fixture
def env(tmp_path, monkeypatch):
    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps(CATALOG), encoding="utf-8")
    renames = tmp_path / "cli-renames.md"
    renames.write_text(RENAMES_MD, encoding="utf-8")
    monkeypatch.setattr(cv, "CATALOG_PATH", catalog)
    monkeypatch.setattr(cv, "RENAMES_PATH", renames)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _task(root, relpath, patterns, extra=None):
    """Write a task YAML with one command_executed criterion per pattern."""
    p = root / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = ["success_criteria:"]
    for i, pat in enumerate(patterns):
        lines += [
            "  - type: command_executed",
            f"    description: criterion {i}",
            f"    command_pattern: '{pat}'",
        ]
    if extra:
        lines += extra
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def _run(monkeypatch, capsys, *argv):
    monkeypatch.setattr(sys, "argv", ["check-cli-verbs.py", *argv])
    code = cv.main() or 0
    out = capsys.readouterr()
    return code, out.out, out.err


# --- load_catalog / load_renames -------------------------------------------

def test_load_catalog_returns_verbs_and_version(env):
    verbs, version = cv.load_catalog()
    assert "maestro flow init" in verbs
    assert version == "7.7.7"


def test_load_catalog_version_defaults_to_unknown(env):
    cv.CATALOG_PATH.write_text(json.dumps({"verbs": ["a"]}), encoding="utf-8")
    assert cv.load_catalog() == ({"a"}, "unknown")


def test_load_catalog_missing_file_exits_with_hint(env):
    cv.CATALOG_PATH.unlink()
    with pytest.raises(SystemExit) as exc:
        cv.load_catalog()
    assert "Catalog not found" in str(exc.value)


def test_load_renames_parses_table_rows_and_skips_header_and_separator(env):
    assert cv.load_renames() == {
        "flow": "maestro flow",
        "solution new": "solution init",
    }


def test_load_renames_missing_file_is_empty(env):
    cv.RENAMES_PATH.unlink()
    assert cv.load_renames() == {}


def test_load_renames_ignores_malformed_rows(env):
    cv.RENAMES_PATH.write_text(
        "prose line\n"
        "| only-one-cell |\n"
        "| | `empty-retired` |\n"
        "| `` | `x` |\n"
        "| `real` | `canon` |\n",
        encoding="utf-8",
    )
    assert cv.load_renames() == {"real": "canon"}


# --- enumerate_paths via extract_verb_paths ---------------------------------

@pytest.mark.parametrize(
    "pattern, expected",
    [
        (r"uip\s+solution\s+list", ["solution list"]),
        (r"\$uip\s+solution\s+list", ["solution list"]),
        (r"^uip\s+solution\s+list$", ["solution list"]),
        (r"uip\s+solution\s+list\s+--output\s+json", ["solution list"]),
        (r"uip\s+(solution|maestro)\s+list", ["solution list", "maestro list"]),
        (r"uip\s+solution\s+(list)?", ["solution", "solution list"]),
        (r"uip\s+solution\s+(?:list){1}", ["solution list"]),
        (r"uip\s*solution", ["solution"]),
        (r"uip[\s]solution", ["solution"]),
        # Dynamic tail: literal prefix up to the last whitespace is kept.
        (r"uip\s+solution\s+[a-z]", ["solution"]),
        (r"uip\s+solution\s+list[^a]", ["solution"]),
        (r"uip\s+solution\s+list+", ["solution"]),
        (r"uip\s+solution\s+(list.*)", ["solution"]),
        (r"uip\s+solution\s+(list|.*)", ["solution"]),
        (r"uip\s+solution\s+list\s+.*--flag", ["solution list"]),
        (r"uip\s+solution\s+\d+", ["solution"]),
    ],
)
def test_extract_verb_paths(pattern, expected):
    assert cv.extract_verb_paths(pattern) == expected


@pytest.mark.parametrize(
    "pattern",
    [
        r"uip\s+(",                       # invalid regex
        r"echo\s+uip\s+solution",         # not a uip command
        r"\buip\s+solution\s+list",       # word boundary is context-dependent
        r"uip\s+.*",                      # nothing literal after uip
        r"uip",                           # no verb at all
        r"uip\s+--output\s+json",         # flag directly after uip
    ],
)
def test_extract_verb_paths_returns_none_when_unanalysable(pattern):
    assert cv.extract_verb_paths(pattern) is None


def test_enumerate_paths_strict_mode_refuses_any_dynamic_element():
    import sre_parse  # noqa: PLC0415 - mirrors the script's own import
    parsed = list(sre_parse.parse(r"uip\s+solution\s+.*"))
    assert cv.enumerate_paths(parsed, allow_partial=False) is None
    assert cv.enumerate_paths(parsed, allow_partial=True) == ["uip solution "]


def test_trim_to_word_boundary_drops_partial_tokens_and_unsplittable_paths():
    assert cv._trim_to_word_boundary(["uip solution", "uip ", "solution", ""]) == [
        "uip", "uip ", ""]


# --- classify ---------------------------------------------------------------

CAT = {"solution", "solution init", "maestro", "maestro flow"}
REN = {"flow": "maestro flow", "solution new": "solution init"}


def test_classify_empty_is_unknown():
    assert cv.classify([], CAT, REN) == ("unknown", {})


def test_classify_catalog_hit_is_reachable():
    verdict, details = cv.classify(["solution init --x"], CAT, REN)
    assert verdict == "reachable"
    assert details == {"reachable": ["solution init --x"], "retired": []}


def test_classify_more_specific_rename_shadows_shallower_catalog_prefix():
    verdict, details = cv.classify(["solution new"], CAT, REN)
    assert verdict == "retired"
    assert details["suggestions"] == {"solution new": "solution init"}


def test_classify_rename_only_is_retired():
    verdict, details = cv.classify(["flow init"], CAT, REN)
    assert verdict == "retired"
    assert details["retired"] == ["flow init"]
    assert details["suggestions"] == {"flow init": "maestro flow"}


def test_classify_unmatched_is_unknown_with_paths():
    assert cv.classify(["zzz run"], CAT, REN) == ("unknown", {"unmatched": ["zzz run"]})


def test_classify_any_reachable_path_wins_over_retired_ones():
    verdict, details = cv.classify(["maestro flow", "flow init"], CAT, REN)
    assert verdict == "reachable"
    assert details["reachable"] == ["maestro flow"]
    assert details["retired"] == ["flow init"]


# --- iter_command_patterns --------------------------------------------------

def test_iter_command_patterns_yields_only_bash_command_executed_with_string_patterns():
    spec = {"success_criteria": [
        "not-a-dict",
        {"type": "file_exists", "command_pattern": "uip x"},
        {"type": "command_executed", "tool_name": "Read", "command_pattern": "uip y"},
        {"type": "command_executed", "command_pattern": 5},
        {"type": "command_executed", "command_pattern": "uip a", "description": "d"},
        {"type": "command_executed", "tool_name": "Bash", "command_pattern": "uip b"},
    ]}
    got = list(cv.iter_command_patterns(spec, Path("x.yaml")))
    assert got == [(4, "uip a", "d"), (5, "uip b", "")]


def test_iter_command_patterns_tolerates_missing_criteria():
    assert list(cv.iter_command_patterns({"success_criteria": None}, Path("x"))) == []
    assert list(cv.iter_command_patterns({}, Path("x"))) == []


# --- lint_file --------------------------------------------------------------

def _lint(path):
    verbs, _ = cv.load_catalog()
    return cv.lint_file(path, verbs, cv.load_renames())


def test_lint_file_reachable_pattern_has_no_findings(env):
    p = _task(env, "t.yaml", [r"uip\s+solution\s+list"])
    assert _lint(p) == []


def test_lint_file_classifies_high_medium_and_info(env):
    p = _task(env, "t.yaml", [
        r"uip\s+zzz\s+run",
        r"uip\s+flow\s+init",
        r"uip\s+.*anything",
    ])
    findings = _lint(p)
    assert [f["severity"] for f in findings] == ["High", "Medium", "Info"]
    high, medium, info = findings
    assert high["criterion_index"] == 0
    assert high["description"] == "criterion 0"
    assert high["message"] == "No verb in pattern matches uip catalog (unmatched: ['zzz run'])."
    assert medium["message"] == "Pattern matches only retired verbs: `flow init` → `maestro flow`"
    assert info["message"].startswith("Pattern too dynamic to verify")
    assert info["command_pattern"] == r"uip\s+.*anything"
    assert all(f["path"] == str(p) and f["axis"] == "cli-verb-reachability" for f in findings)


def test_lint_file_invalid_yaml_is_an_info_finding(env):
    p = env / "bad.yaml"
    p.write_text("key: [unclosed\n", encoding="utf-8")
    (f,) = _lint(p)
    assert f["severity"] == "Info"
    assert f["message"].startswith("YAML parse error:")


def test_lint_file_non_mapping_yaml_has_no_findings(env):
    p = env / "list.yaml"
    p.write_text("- a\n- b\n", encoding="utf-8")
    assert _lint(p) == []


def test_lint_file_without_pyyaml_exits_with_install_hint(env, monkeypatch):
    p = _task(env, "t.yaml", [r"uip\s+solution\s+list"])
    monkeypatch.setitem(sys.modules, "yaml", None)  # makes `import yaml` raise ImportError
    with pytest.raises(SystemExit) as exc:
        _lint(p)
    assert "PyYAML is required" in str(exc.value)


# --- main: text -------------------------------------------------------------

def test_main_text_ok_when_all_patterns_reachable(env, monkeypatch, capsys):
    p = _task(env, "t.yaml", [r"uip\s+solution\s+list"])
    code, out, _ = _run(monkeypatch, capsys, str(p))
    assert code == 0
    assert out.strip() == "OK — no CLI-verb issues (catalog: uip 7.7.7, 6 verbs)."


def test_main_text_lists_findings_by_severity_and_exits_one(env, monkeypatch, capsys):
    info = _task(env, "a_info.yaml", [r"uip\s+.*x"])
    high = _task(env, "z_high.yaml", [r"uip\s+zzz\s+run"])
    medium = _task(env, "m_medium.yaml", [r"uip\s+flow\s+init"])
    code, out, _ = _run(monkeypatch, capsys, str(info), str(high), str(medium))
    assert code == 1
    lines = out.splitlines()
    assert lines[0].startswith(f"[High] {high}:")
    assert any(line.startswith(f"[Medium] {medium}:") for line in lines)
    assert lines.index(f"           pattern: {r'uip\s+zzz\s+run'}") == 1
    assert out.rstrip().endswith("1 High, 1 Medium, 1 Info (catalog: uip 7.7.7)")
    assert out.index("[High]") < out.index("[Medium]") < out.index("[Info]")


def test_main_text_info_only_exits_zero(env, monkeypatch, capsys):
    p = _task(env, "t.yaml", [r"uip\s+.*x"])
    code, out, _ = _run(monkeypatch, capsys, str(p))
    assert code == 0
    assert "0 High, 0 Medium, 1 Info" in out


def test_main_skips_missing_paths_with_message(env, monkeypatch, capsys):
    ok = _task(env, "t.yaml", [r"uip\s+solution\s+list"])
    code, out, err = _run(monkeypatch, capsys, "nope.yaml", str(ok))
    assert code == 0
    assert "skip: nope.yaml (not found)" in err
    assert out.startswith("OK")


# --- main: json -------------------------------------------------------------

def test_main_json_emits_ndjson_and_exits_one_on_high(env, monkeypatch, capsys):
    p = _task(env, "t.yaml", [r"uip\s+zzz\s+run", r"uip\s+.*x"])
    code, out, _ = _run(monkeypatch, capsys, "--json", str(p))
    assert code == 1
    rows = [json.loads(line) for line in out.splitlines()]
    assert [r["severity"] for r in rows] == ["High", "Info"]


def test_main_json_with_no_findings_prints_nothing_and_exits_zero(env, monkeypatch, capsys):
    p = _task(env, "t.yaml", [r"uip\s+solution\s+list"])
    code, out, _ = _run(monkeypatch, capsys, "--json", str(p))
    assert (code, out) == (0, "")


# --- main: report -----------------------------------------------------------

def test_main_report_summarises_findings_and_exits_one_on_high(env, monkeypatch, capsys):
    t1 = _task(env, "tests/tasks/skill-a/one.yaml", [r"uip\s+zzz\s+run", r"uip\s+flow\s+init"])
    t2 = _task(env, "tests/tasks/skill-a/two.yaml", [r"uip\s+zzz\s+run"])
    t3 = _task(env, "tests/tasks/skill-b/three.yaml", [r"uip\s+qqq\s+go", r"uip\s+.*x"])
    report = env / "out" / "report.md"
    code, out, _ = _run(
        monkeypatch, capsys, "--report", str(report),
        *(str(p.relative_to(env)) for p in (t1, t2, t3)))
    assert code == 1
    assert out.strip() == f"wrote {report} (3 High, 1 Medium, 1 Info)"
    text = report.read_text()
    assert "# CLI Verb Reachability Audit" in text
    assert "7.7.7" in text and "6 reachable verbs" in text
    assert "| **High** (verb not in catalog) | 3 | 3 |" in text
    assert "| 2 | `zzz run` |" in text
    assert "| 1 | `qqq go` |" in text
    assert "| `skill-a` | 2 |" in text
    assert "| `skill-b` | 1 |" in text
    assert "### All High findings" in text
    assert f"--report {report}" in text
    assert "1 patterns could not be statically enumerated" in text


def test_main_report_without_high_findings_exits_zero_and_omits_high_sections(env, monkeypatch, capsys):
    p = _task(env, "t.yaml", [r"uip\s+flow\s+init", r"uip\s+solution\s+list"])
    report = env / "r.md"
    code, out, _ = _run(monkeypatch, capsys, "--report", str(report), str(p))
    assert code == 0
    assert "(0 High, 1 Medium, 0 Info)" in out
    text = report.read_text()
    assert "All High findings" not in text
    assert "High findings by skill" not in text
    assert "verbs not in catalog" not in text


def test_write_report_ignores_high_findings_whose_message_lacks_unmatched_list(tmp_path):
    findings = [{
        "path": "elsewhere/x.yaml", "severity": "High", "criterion_index": 0,
        "command_pattern": "uip x", "message": "something else entirely",
    }]
    report = tmp_path / "r.md"
    cv.write_report(findings, 3, "1.0", report)
    text = report.read_text()
    assert "| **High** (verb not in catalog) | 1 | 1 |" in text
    assert "verbs not in catalog\n" not in text
    assert "High findings by skill" not in text
