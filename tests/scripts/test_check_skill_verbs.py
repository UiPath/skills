"""
Behaviour tests for scripts/check-skill-verbs.py.

The catalog path is a module constant, so tests point it at a fixture catalog
under tmp_path and drive main() with argv, asserting exit code, stdout and the
report file.

Run from repo root:
    pytest tests/scripts/test_check_skill_verbs.py
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check-skill-verbs.py"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sv = _load("check_skill_verbs_behaviour", SCRIPT)

CATALOG = {
    "cli_version": "9.9.9",
    "verbs": ["solution", "solution list", "solution pack", "flow", "flow init", "rpa"],
    "unwalkable_groups": ["rpa"],
}


@pytest.fixture
def catalog(tmp_path, monkeypatch):
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(CATALOG), encoding="utf-8")
    monkeypatch.setattr(sv, "CATALOG_PATH", path)
    return path


def _md(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def _run(monkeypatch, capsys, *argv):
    monkeypatch.setattr(sys, "argv", ["check-skill-verbs.py", *argv])
    code = sv.main()
    out = capsys.readouterr()
    return code, out.out, out.err


# --- load_catalog -----------------------------------------------------------

def test_load_catalog_returns_verbs_unwalkable_and_version(catalog):
    verbs, unwalkable, version = sv.load_catalog()
    assert "solution list" in verbs
    assert unwalkable == {"rpa"}
    assert version == "9.9.9"


def test_load_catalog_defaults_when_optional_keys_missing(catalog):
    catalog.write_text(json.dumps({"verbs": ["x"]}), encoding="utf-8")
    assert sv.load_catalog() == ({"x"}, set(), "unknown")


def test_load_catalog_missing_file_exits_with_hint(tmp_path, monkeypatch):
    monkeypatch.setattr(sv, "CATALOG_PATH", tmp_path / "nope.json")
    with pytest.raises(SystemExit) as exc:
        sv.load_catalog()
    assert "Catalog not found" in str(exc.value)
    assert "build-uip-catalog.py" in str(exc.value)


# --- extract_verb_tokens ----------------------------------------------------

@pytest.mark.parametrize(
    "tail, expected",
    [
        ("", []),
        ("   ", []),
        (" solution list", ["solution", "list"]),
        (" solution list --output json", ["solution", "list"]),
        (" solution list | jq .", ["solution", "list"]),
        (" solution pack <proj> --x", ["solution", "pack"]),
        (" solution pack $DIR", ["solution", "pack"]),
        (" solution pack ...", ["solution", "pack"]),
        (" solution pack ./dir", ["solution", "pack"]),
        (" solution pack key=value", ["solution", "pack"]),
        (" solution pack 12345", ["solution", "pack"]),
        (" solution pack core.action.script", ["solution", "pack"]),
        (" solution pack # refresh the cache", ["solution", "pack"]),
        (" `solution` list`", ["solution", "list"]),
        (" — heading", []),
        (" -x flag", []),
        (" <placeholder> thing", []),
        (" solution list.", ["solution", "list"]),
        (" _private cmd", ["_private", "cmd"]),
        (" ``` ", []),
    ],
)
def test_extract_verb_tokens(tail, expected):
    assert sv.extract_verb_tokens(tail) == expected


def test_extract_verb_tokens_cuts_at_line_continuation():
    assert sv.extract_verb_tokens(" solution list \\\n --x") == ["solution", "list"]


def test_best_prefix_returns_longest_catalog_match_or_none():
    catalog = {"solution", "solution list"}
    assert sv.best_prefix(["solution", "list", "extra"], catalog) == "solution list"
    assert sv.best_prefix(["solution", "bogus"], catalog) == "solution"
    assert sv.best_prefix(["bogus"], catalog) is None


# --- scan_file --------------------------------------------------------------

def _scan(path):
    verbs = set(CATALOG["verbs"])
    return sv.scan_file(path, verbs, set(CATALOG["unwalkable_groups"]))


def test_scan_file_exact_catalog_hit_yields_no_finding(tmp_path):
    md = _md(tmp_path, "a.md", "Run `uip solution list --output json`.\n")
    assert _scan(md) == []


def test_scan_file_unknown_verb_is_stale_with_longest_prefix(tmp_path):
    md = _md(tmp_path, "a.md", "ok\nRun `uip solution bogus --x` now.\n")
    findings = _scan(md)
    assert len(findings) == 1
    f = findings[0]
    assert f["line"] == 2
    assert f["verb_path"] == "solution bogus"
    assert f["matched_prefix"] == "solution"
    assert f["severity"] == "Stale"
    assert "uip solution bogus" in f["context"]


def test_scan_file_unknown_group_has_no_matched_prefix(tmp_path):
    md = _md(tmp_path, "a.md", "`uip zzz run`\n")
    (f,) = _scan(md)
    assert f["matched_prefix"] is None
    assert f["severity"] == "Stale"


def test_scan_file_unwalkable_group_is_uncertain(tmp_path):
    md = _md(tmp_path, "a.md", "`uip rpa debug start`\n")
    (f,) = _scan(md)
    assert f["severity"] == "Uncertain"
    assert f["verb_path"] == "rpa debug start"


def test_scan_file_prose_noise_is_ignored(tmp_path):
    md = _md(tmp_path, "a.md", "Use the uip CLI to do things. uip is great.\n")
    assert _scan(md) == []


def test_scan_file_skip_marker_suppresses_line(tmp_path):
    md = _md(tmp_path, "a.md", "`uip old verb` <!-- uip-check-skip -->\n")
    assert _scan(md) == []


def test_scan_file_bare_uip_without_tail_is_ignored(tmp_path):
    md = _md(tmp_path, "a.md", "Install uip\n")
    assert _scan(md) == []


def test_scan_file_unreadable_file_warns_and_returns_nothing(tmp_path, capsys):
    bad = tmp_path / "actually-a-directory.md"
    bad.mkdir()
    assert _scan(bad) == []
    assert "warning: cannot read" in capsys.readouterr().err


# --- iter_markdown ----------------------------------------------------------

def test_iter_markdown_walks_dirs_sorted_and_accepts_files(tmp_path):
    (tmp_path / "d" / "sub").mkdir(parents=True)
    b = _md(tmp_path / "d", "b.md", "x")
    a = _md(tmp_path / "d" / "sub", "a.md", "x")
    _md(tmp_path / "d", "note.txt", "x")
    single = _md(tmp_path, "single.md", "x")
    ignored = _md(tmp_path, "single.txt", "x")
    got = list(sv.iter_markdown([tmp_path / "d", single, ignored, tmp_path / "missing"]))
    assert got == [b, a, single]


# --- main: text / json / report --------------------------------------------

def test_main_ok_when_no_findings(catalog, tmp_path, monkeypatch, capsys):
    md = _md(tmp_path, "a.md", "`uip solution list`\n")
    code, out, _ = _run(monkeypatch, capsys, str(md))
    assert code == 0
    assert out.strip() == "OK — no stale uip verbs found (catalog: uip 9.9.9, 6 verbs)."


def test_main_text_reports_stale_and_uncertain_and_exits_one(catalog, tmp_path, monkeypatch, capsys):
    md = _md(tmp_path, "a.md", "`uip solution bogus`\n`uip solution bogus`\n`uip rpa debug`\n")
    code, out, _ = _run(monkeypatch, capsys, str(md))
    assert code == 1
    assert "1 Stale, 1 Uncertain" not in out  # two stale findings, one verb
    assert out.startswith("2 Stale, 1 Uncertain findings (catalog: uip 9.9.9, 6 verbs, 1 unwalkable groups)")
    assert "Top stale verb paths:" in out
    assert "  2  solution bogus" in out
    assert "Files with most stale findings:" in out
    assert str(md) in out
    assert "1 Uncertain findings under unwalkable groups (rpa)" in out


def test_main_only_uncertain_exits_zero(catalog, tmp_path, monkeypatch, capsys):
    md = _md(tmp_path, "a.md", "`uip rpa debug`\n")
    code, out, _ = _run(monkeypatch, capsys, str(md))
    assert code == 0
    assert "0 Stale, 1 Uncertain" in out
    assert "Top stale verb paths:" not in out


def test_main_json_emits_findings_with_path_and_exits_zero(catalog, tmp_path, monkeypatch, capsys):
    md = _md(tmp_path, "a.md", "`uip solution bogus`\n")
    code, out, _ = _run(monkeypatch, capsys, "--json", str(md))
    assert code == 0
    (finding,) = [json.loads(line) for line in out.splitlines()]
    assert finding["path"] == str(md)
    assert finding["verb_path"] == "solution bogus"
    assert finding["severity"] == "Stale"


def test_main_report_writes_markdown_and_exits_one_on_stale(catalog, tmp_path, monkeypatch, capsys):
    skills = tmp_path / "skills" / "my-skill"
    skills.mkdir(parents=True)
    md = _md(skills, "SKILL.md", "`uip solution bogus`\n`uip flow nope sub`\n`uip rpa debug`\n")
    report = tmp_path / "out" / "report.md"
    code, out, _ = _run(monkeypatch, capsys, "--report", str(report), str(md))
    assert code == 1
    assert out.strip() == f"wrote {report} (2 Stale, 1 Uncertain)"
    text = report.read_text()
    assert "# Skill CLI Verb Audit" in text
    assert "Catalog: uip 9.9.9 — 6 verbs, 1 unwalkable groups (rpa)" in text
    assert "| **Stale** | 2 | 2 | 1 |" in text
    assert "| **Uncertain** | 1 | 1 | 1 |" in text
    # Suggestions come from sibling verbs under the parent path.
    assert "| 1 | `solution bogus` | `solution list` or `solution pack` |" in text
    assert "| 1 | `flow nope sub` | `flow init` |" in text
    assert "## Uncertain findings" in text
    assert "| 1 | `rpa debug` |" in text
    assert f"--report {report} skills/" in text


def test_main_report_exits_zero_without_stale_and_omits_uncertain_section(catalog, tmp_path, monkeypatch, capsys):
    md = _md(tmp_path, "a.md", "`uip solution list`\n")
    report = tmp_path / "r.md"
    code, out, _ = _run(monkeypatch, capsys, "--report", str(report), str(md))
    assert code == 0
    assert "(0 Stale, 0 Uncertain)" in out
    assert "## Uncertain findings" not in report.read_text()


def test_report_has_no_replacement_for_single_token_verb(catalog, tmp_path, monkeypatch, capsys):
    md = _md(tmp_path, "a.md", "`uip zzz`\n")
    report = tmp_path / "r.md"
    _run(monkeypatch, capsys, "--report", str(report), str(md))
    assert "| 1 | `zzz` | — |" in report.read_text()


def test_report_suggests_grandparent_siblings_for_deep_unknown_verbs(tmp_path):
    findings = [{
        "line": 3, "verb_path": "flow x y z", "matched_prefix": "flow",
        "severity": "Stale", "context": "uip flow x y z | tee", "path": "docs/a.md",
    }]
    report = tmp_path / "r.md"
    sv.write_report(findings, {"flow", "flow x a", "flow x b"}, set(), "1", report)
    text = report.read_text()
    assert "`flow x a` or `flow x b`" in text
    assert "context: `uip flow x y z \\| tee`" in text
    assert "longest catalog prefix: `flow`" in text


def test_report_prints_none_when_no_catalog_prefix_matches(tmp_path):
    findings = [{
        "line": 1, "verb_path": "zzz run", "matched_prefix": None,
        "severity": "Stale", "context": "uip zzz run", "path": "docs/a.md",
    }]
    report = tmp_path / "r.md"
    sv.write_report(findings, {"flow"}, set(), "1", report)
    assert "longest catalog prefix: `(none)`" in report.read_text()


def test_report_counts_stale_findings_per_skill(tmp_path):
    findings = [
        {"line": 1, "verb_path": "a b", "matched_prefix": None, "severity": "Stale",
         "context": "c", "path": str(Path("skills") / "one" / "SKILL.md")},
        {"line": 2, "verb_path": "a c", "matched_prefix": None, "severity": "Stale",
         "context": "c", "path": str(Path("skills") / "one" / "ref.md")},
        {"line": 1, "verb_path": "a d", "matched_prefix": None, "severity": "Stale",
         "context": "c", "path": str(Path("skills") / "two" / "SKILL.md")},
        {"line": 1, "verb_path": "a e", "matched_prefix": None, "severity": "Stale",
         "context": "c", "path": "README.md"},
    ]
    report = tmp_path / "r.md"
    sv.write_report(findings, set(), set(), "1", report)
    text = report.read_text()
    assert "| `one` | 2 |" in text
    assert "| `two` | 1 |" in text


# --- as a subprocess --------------------------------------------------------

def test_script_run_for_real_exits_one_on_unknown_verb(tmp_path):
    """Running the script for real: stale references against the shipped snapshot exit 1."""
    md = _md(tmp_path, "a.md", "`uip definitely-not-a-real-group frobnicate`\n")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(md)],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 1
    assert "definitely-not-a-real-group frobnicate" in proc.stdout
