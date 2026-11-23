"""
Behaviour tests for the findings and output of scripts/check-skills-sh.py that
test_check_skills_sh.py (the --baseline-ref contract) does not pin: each schema
rule of skills.sh.json, the --fix repair, and the text output a PR author reads.

Fixture trees live in tmp_path; the script's MANIFEST_PATH / SKILLS_DIR are
pointed at them, so nothing here depends on the live manifest.

Run from repo root:
    pytest tests/scripts/test_check_skills_sh_findings.py
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check-skills-sh.py"

_spec = importlib.util.spec_from_file_location("check_skills_sh_findings", SCRIPT)
check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check)


def manifest(*groups, **extra):
    data = {"$schema": check.SCHEMA_URL,
            "groupings": [{"title": title, "skills": list(skills)} for title, *skills in groups]}
    data.update(extra)
    return data


def kinds(findings):
    return [f["kind"] for f in findings]


@pytest.fixture
def tree(tmp_path, monkeypatch):
    """A skills tree + manifest the script reads instead of the live ones."""
    skills = tmp_path / "skills"
    skills.mkdir()
    monkeypatch.setattr(check, "SKILLS_DIR", skills)
    monkeypatch.setattr(check, "MANIFEST_PATH", tmp_path / "skills.sh.json")

    def build(manifest_data, *names):
        for name in names:
            (skills / name).mkdir(exist_ok=True)
            (skills / name / "SKILL.md").write_text("# x\n", encoding="utf-8")
        if manifest_data is not None:
            check.MANIFEST_PATH.write_text(json.dumps(manifest_data), encoding="utf-8")
        return tmp_path

    return build


def run_main(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["check-skills-sh.py", *args])
    return check.main()


# --- loading -------------------------------------------------------------------------------------

def test_missing_manifest_exits_with_its_path(tree):
    root = tree(None)
    with pytest.raises(SystemExit) as exc:
        check.load_manifest()
    assert f"Manifest not found at {root / 'skills.sh.json'}." in str(exc.value)


def test_manifest_that_is_not_json_exits_naming_the_file(tree):
    root = tree(None)
    (root / "skills.sh.json").write_text("{nope", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        check.load_manifest()
    assert "skills.sh.json is not valid JSON" in str(exc.value)


def test_missing_skills_directory_exits_with_its_path(tmp_path, monkeypatch):
    monkeypatch.setattr(check, "SKILLS_DIR", tmp_path / "absent")
    with pytest.raises(SystemExit) as exc:
        check.skills_on_disk()
    assert "Skills directory not found at" in str(exc.value)


def test_a_skill_is_a_directory_holding_a_skill_md(tree):
    root = tree(None, "real-skill")
    (root / "skills" / "no-skill-md").mkdir()
    assert check.skills_on_disk() == {"real-skill"}


# --- schema --------------------------------------------------------------------------------------

def test_top_level_must_be_an_object():
    findings, groupings, usable = check.check_schema(["not", "an", "object"])
    assert kinds(findings) == ["top-level-type"]
    assert (groupings, usable) == ([], False)


def test_unknown_key_wrong_schema_url_and_bad_not_grouped_are_each_reported():
    data = manifest(("A", "x"), bogus=1, notGrouped="middle")
    data["$schema"] = "https://example.com/other.json"
    findings, _, usable = check.check_schema(data)
    assert usable
    assert kinds(findings) == ["unknown-top-level-key", "schema-url", "not-grouped-value"]
    messages = " ".join(f["error"] for f in findings)
    assert "unknown top-level key" in messages
    assert "'https://example.com/other.json'" in messages
    assert "must be one of ['bottom', 'top'], got 'middle'" in messages


@pytest.mark.parametrize("groupings", [None, [], "text"])
def test_groupings_must_be_a_non_empty_list(groupings):
    findings, valid, usable = check.check_schema({"groupings": groupings})
    assert kinds(findings) == ["groupings-missing"]
    assert (valid, usable) == ([], False)


def test_unusable_groupings_report_only_the_schema_finding(tree):
    on_disk = {"a", "b", "c"}
    assert kinds(check.validate({"groupings": []}, on_disk)) == ["groupings-missing"]


def test_more_than_fifty_groupings_is_reported():
    data = manifest(*[(f"G{i}", f"s{i}") for i in range(51)])
    findings, _, _ = check.check_schema(data)
    assert kinds(findings) == ["groupings-count"]
    assert "at most 50 groupings, got 51" in findings[0]["error"]


def test_grouping_that_is_not_an_object_is_reported_and_skipped():
    findings, valid, _ = check.check_schema({"groupings": ["text", {"title": "A", "skills": ["x"]}]})
    assert kinds(findings) == ["group-type"]
    assert findings[0]["key"] == "groupings[0]"
    assert [g["title"] for g in valid] == ["A"]


@pytest.mark.parametrize("title", [None, "", "x" * 121, 7])
def test_title_is_required_and_bounded(title):
    findings, _, _ = check.check_schema({"groupings": [{"title": title, "skills": ["x"]}]})
    assert kinds(findings) == ["group-title"]
    assert findings[0]["subject"] == "groupings[0]"
    assert "1-120 characters" in findings[0]["error"]


@pytest.mark.parametrize("description", ["x" * 501, 5])
def test_description_must_be_a_short_string(description):
    data = {"groupings": [{"title": "A", "description": description, "skills": ["x"]}]}
    findings, _, _ = check.check_schema(data)
    assert kinds(findings) == ["group-description"]
    assert findings[0]["key"] == "groupings[0] 'A'"
    assert findings[0]["subject"] == "A"


def test_a_short_description_is_accepted():
    data = {"groupings": [{"title": "A", "description": "fine", "skills": ["x"]}]}
    assert check.check_schema(data)[0] == []


@pytest.mark.parametrize("skills", [None, [], "x"])
def test_skills_list_is_required_and_non_empty(skills):
    findings, valid, _ = check.check_schema({"groupings": [{"title": "A", "skills": skills}]})
    assert kinds(findings) == ["group-skills-missing"]
    assert valid == []


def test_more_than_five_hundred_skills_in_a_grouping_is_reported():
    names = [f"s{i}" for i in range(501)]
    findings, _, _ = check.check_schema({"groupings": [{"title": "A", "skills": names}]})
    assert kinds(findings) == ["group-skills-count"]
    assert "at most 500 skills, got 501" in findings[0]["error"]


def test_each_bad_skill_entry_is_keyed_on_the_entry_itself():
    data = {"groupings": [{"title": "A", "skills": ["ok", "", 4, "y" * 121]}]}
    findings, _, _ = check.check_schema(data)
    assert kinds(findings) == ["skill-entry"] * 3
    assert findings[0]["subject"] == "''"
    assert findings[1]["subject"] == "4"


# --- coverage ------------------------------------------------------------------------------------

def test_duplicate_stale_and_ungrouped_skills_are_reported_with_guidance():
    findings = check.validate(manifest(("A", "dup", "gone"), ("B", "dup")), {"dup", "fresh"})
    by_kind = {f["kind"]: f for f in findings}
    assert "listed in more than one grouping ('A' and 'B')" in by_kind["duplicate-grouping"]["error"]
    assert "Run --fix to drop it." in by_kind["grouped-not-on-disk"]["error"]
    assert by_kind["grouped-not-on-disk"]["subject"] == "gone"
    assert "placement is an editorial call" in by_kind["ungrouped"]["error"]
    assert by_kind["ungrouped"]["subject"] == "fresh"


def test_non_string_names_are_ignored_by_the_coverage_check():
    findings = check.check_coverage([{"title": "A", "skills": [7, "real"]}], {"real"})
    assert findings == []


# --- baseline helpers ----------------------------------------------------------------------------

def test_git_returns_none_when_git_cannot_start(monkeypatch):
    def boom(*args, **kwargs):
        raise OSError("no git")

    monkeypatch.setattr(check.subprocess, "run", boom)
    assert check._git("status") is None


def test_baseline_without_a_readable_tree_listing_is_unreadable(monkeypatch):
    replies = iter([json.dumps(manifest(("A", "x"))), None])
    monkeypatch.setattr(check, "_git", lambda *args: next(replies))
    assert check.baseline_state("origin/main") is None


def test_baseline_lists_only_skill_md_files_directly_under_skills(monkeypatch):
    listing = "\n".join(["skills/alpha/SKILL.md", "skills/alpha/references/SKILL.md",
                         "skills/beta/README.md", "docs/gamma/SKILL.md", "skills/delta/SKILL.md"])
    replies = iter([json.dumps(manifest(("A", "alpha"))), listing])
    monkeypatch.setattr(check, "_git", lambda *args: next(replies))
    _, on_disk = check.baseline_state("origin/main")
    assert on_disk == {"alpha", "delta"}


# --- --fix ---------------------------------------------------------------------------------------

def test_fix_drops_stale_names_and_emptied_groupings_but_never_places_new_skills(tree, capsys):
    tree(manifest(("Keep", "alive", "gone"), ("Doomed", "ghost")), "alive", "fresh")
    data = check.load_manifest()
    assert check.fix(data, check.skills_on_disk()) == 1
    out = capsys.readouterr().out
    assert "Removed 2 stale entries from skills.sh.json:" in out
    assert "gone (was in 'Keep')" in out
    assert "ghost (was in 'Doomed')" in out
    assert "grouping 'Doomed' dropped — it had no surviving skills" in out
    assert "1 skill(s) still need a grouping — add by hand:" in out
    assert "  - fresh" in out
    written = json.loads(check.MANIFEST_PATH.read_text(encoding="utf-8"))
    assert [(g["title"], g["skills"]) for g in written["groupings"]] == [("Keep", ["alive"])]
    assert check.MANIFEST_PATH.read_text(encoding="utf-8").endswith("}\n")


def test_fix_reports_a_single_removal_in_the_singular(tree, capsys):
    tree(manifest(("Keep", "alive", "gone")), "alive")
    assert check.fix(check.load_manifest(), check.skills_on_disk()) == 0
    assert "Removed 1 stale entry from skills.sh.json:" in capsys.readouterr().out


def test_fix_with_nothing_stale_leaves_the_file_alone(tree, capsys):
    tree(manifest(("Keep", "alive")), "alive")
    before = check.MANIFEST_PATH.read_bytes()
    assert check.fix(check.load_manifest(), check.skills_on_disk()) == 0
    assert "skills.sh.json has no stale entries to remove." in capsys.readouterr().out
    assert check.MANIFEST_PATH.read_bytes() == before


def test_fix_keeps_malformed_groupings_for_a_human(tree):
    data = {"groupings": ["text", {"title": "NoList", "skills": "x"}, {"title": "A", "skills": ["gone", "alive"]}]}
    tree(data, "alive")
    check.fix(check.load_manifest(), check.skills_on_disk())
    written = json.loads(check.MANIFEST_PATH.read_text(encoding="utf-8"))
    assert written["groupings"] == ["text", {"title": "NoList", "skills": "x"}, {"title": "A", "skills": ["alive"]}]


def test_fix_refuses_when_groupings_is_not_a_list(tree):
    tree({"groupings": "x"})
    with pytest.raises(SystemExit) as exc:
        check.fix(check.load_manifest(), set())
    assert "Cannot --fix: `groupings` in skills.sh.json is not a list." in str(exc.value)


def test_main_fix_flag_runs_the_repair(tree, monkeypatch, capsys):
    tree(manifest(("Keep", "alive", "gone")), "alive")
    assert run_main(monkeypatch, "--fix") == 0
    assert "Removed 1 stale entry" in capsys.readouterr().out


# --- text output ---------------------------------------------------------------------------------

def test_clean_tree_prints_a_summary(tree, monkeypatch, capsys):
    tree(manifest(("A", "one", "two"), ("B", "three")), "one", "two", "three")
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    assert run_main(monkeypatch) == 0
    assert capsys.readouterr().out.strip() == "OK — 3 skills grouped across 2 section(s)."


def test_findings_are_listed_one_per_line_and_fail(tree, monkeypatch, capsys):
    tree(manifest(("A", "one")), "one", "two")
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    assert run_main(monkeypatch) == 1
    out = capsys.readouterr().out
    assert "1 finding(s):" in out
    assert "  two: exists on disk but is in no grouping" in out
    assert "::error::" not in out


def test_findings_are_annotated_under_github_actions(tree, monkeypatch, capsys):
    tree(manifest(("A", "one")), "one", "two")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert run_main(monkeypatch) == 1
    assert "::error::two: exists on disk but is in no grouping" in capsys.readouterr().out


def test_preexisting_findings_are_warnings_that_do_not_fail(tree, monkeypatch, capsys):
    tree(manifest(("A", "one")), "one", "old")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setattr(check, "baseline_state", lambda ref: (manifest(("A", "one")), {"one", "old"}))
    assert run_main(monkeypatch, "--baseline-ref", "origin/main") == 0
    out = capsys.readouterr().out
    assert "1 pre-existing finding(s) — already present at origin/main, not caused by this change:" in out
    assert "::warning::old: exists on disk but is in no grouping" in out
    assert "OK — 2 skills grouped across 1 section(s)." in out
    assert "Pre-existing drift above still needs a fix" in out


def test_preexisting_findings_print_plainly_outside_github_actions(tree, monkeypatch, capsys):
    tree(manifest(("A", "one")), "one", "old")
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setattr(check, "baseline_state", lambda ref: (manifest(("A", "one")), {"one", "old"}))
    assert run_main(monkeypatch, "--baseline-ref", "origin/main") == 0
    out = capsys.readouterr().out
    assert "  old: exists on disk" in out
    assert "::warning::" not in out


def test_script_runs_as_a_command_on_the_live_tree():
    # Baseline HEAD: drift the checkout already carries is pre-existing, so this
    # pins the command path without failing every PR while main has drift.
    done = subprocess.run([sys.executable, str(SCRIPT), "--json", "--baseline-ref", "HEAD"],
                          capture_output=True, text=True, cwd=REPO_ROOT, check=False)
    assert done.returncode == 0, done.stdout + done.stderr
    assert all(json.loads(line)["preexisting"] for line in done.stdout.splitlines())
