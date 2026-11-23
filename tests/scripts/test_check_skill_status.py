"""
Behaviour tests for scripts/check-skill-status.py.

The script reads fixed repo paths, so each test points the module's path
constants at a fixture tree under tmp_path and drives main() the way the CLI
does (argv in, exit code + stdout/stderr + README out).

Run from repo root:
    pytest tests/scripts/test_check_skill_status.py
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


status = _load("check_skill_status", REPO_ROOT / "scripts" / "check-skill-status.py")

STATUSES = {
    "stable": {"label": "Stable", "meaning": "Ready for use."},
    "preview": {"label": "Preview", "meaning": "May change."},
    "in-development": {"label": "In development", "meaning": "Not ready."},
}


def _skill(skills_dir, name, description="Does things.", body="# Body\n"):
    d = skills_dir / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n{body}",
        encoding="utf-8",
    )


class Repo:
    def __init__(self, root, skills, manifest, manifest_path, readme):
        self.root = root
        self.skills = skills
        self.manifest = manifest
        self.manifest_path = manifest_path
        self.readme = readme

    def save_manifest(self):
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """Fixture repo with two valid skills and a README carrying the markers."""
    skills = tmp_path / "skills"
    skills.mkdir()
    _skill(skills, "alpha")
    _skill(skills, "beta")
    manifest = {
        "statuses": STATUSES,
        "skills": {"alpha": {"status": "stable"}, "beta": {"status": "preview"}},
    }
    manifest_path = tmp_path / "skill-status.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    readme = tmp_path / "README.md"
    readme.write_text(
        f"# Repo\n\n{status.BEGIN_MARKER}\nstale\n{status.END_MARKER}\n\ntail\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(status, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(status, "SKILLS_DIR", skills)
    monkeypatch.setattr(status, "README_PATH", readme)
    return Repo(tmp_path, skills, manifest, manifest_path, readme)


def _run(monkeypatch, capsys, *argv):
    monkeypatch.setattr(sys, "argv", ["check-skill-status.py", *argv])
    code = status.main()
    out = capsys.readouterr()
    return code, out.out, out.err


# --- frontmatter helpers ----------------------------------------------------

def test_split_frontmatter_without_fences_returns_whole_text_as_body():
    assert status.split_frontmatter("# Just body\n") == ("", "# Just body\n")


def test_split_frontmatter_unterminated_fence_returns_whole_text_as_body():
    text = "---\nname: x\nno closing fence\n"
    assert status.split_frontmatter(text) == ("", text)


def test_split_frontmatter_separates_frontmatter_from_body():
    fm, body = status.split_frontmatter("---\nname: x\n---\nline1\nline2\n")
    assert fm == "name: x"
    assert body == "line1\nline2"


def test_extract_description_returns_empty_when_absent():
    assert status.extract_description("name: x") == ""
    assert status.extract_description("name: x\ndescription: hi there").strip() == "hi there"


# --- default validation mode ------------------------------------------------

def test_valid_manifest_reports_ok_and_exits_zero(repo, monkeypatch, capsys):
    code, out, _ = _run(monkeypatch, capsys)
    assert code == 0
    assert out.strip() == "OK — 2 skills, manifest valid."


def test_skill_folder_without_manifest_entry_is_reported(repo, monkeypatch, capsys):
    _skill(repo.skills, "gamma")
    code, out, _ = _run(monkeypatch, capsys)
    assert code == 1
    assert "1 finding(s)" in out
    assert "gamma: no entry in assets/skill-status.json" in out


def test_manifest_entry_without_skill_folder_is_reported(repo, monkeypatch, capsys):
    repo.manifest["skills"]["ghost"] = {"status": "stable"}
    repo.save_manifest()
    code, out, _ = _run(monkeypatch, capsys)
    assert code == 1
    assert "ghost: manifest entry has no skills/<name>/SKILL.md" in out


def test_invalid_status_is_reported_with_legal_values(repo, monkeypatch, capsys):
    repo.manifest["skills"]["alpha"]["status"] = "bogus"
    repo.save_manifest()
    code, out, _ = _run(monkeypatch, capsys)
    assert code == 1
    assert "alpha: invalid status 'bogus'" in out
    assert "['in-development', 'preview', 'stable']" in out


def test_status_tag_in_description_is_reported(repo, monkeypatch, capsys):
    (repo.skills / "alpha" / "SKILL.md").write_text(
        "---\nname: alpha\ndescription: [PREVIEW] Does things.\n---\n# Body\n",
        encoding="utf-8",
    )
    code, out, _ = _run(monkeypatch, capsys)
    assert code == 1
    assert "alpha: status tag (e.g. [PREVIEW]) in frontmatter description" in out


def test_stale_body_callout_is_reported_once(repo, monkeypatch, capsys):
    (repo.skills / "beta" / "SKILL.md").write_text(
        "---\nname: beta\ndescription: ok\n---\n> **Preview** this is new\n"
        "> **Status:** beta\n",
        encoding="utf-8",
    )
    code, out, _ = _run(monkeypatch, capsys)
    assert code == 1
    assert out.count("stale status callout in body") == 1
    assert "> **Preview** this is new" in out


def test_non_status_blockquote_is_not_flagged(repo, monkeypatch, capsys):
    (repo.skills / "beta" / "SKILL.md").write_text(
        "---\nname: beta\ndescription: ok\n---\n> **Two entry points.** fine\n",
        encoding="utf-8",
    )
    code, _, _ = _run(monkeypatch, capsys)
    assert code == 0


def test_json_mode_emits_one_object_per_finding(repo, monkeypatch, capsys):
    _skill(repo.skills, "gamma")
    code, out, _ = _run(monkeypatch, capsys, "--json")
    assert code == 1
    lines = [json.loads(line) for line in out.splitlines()]
    assert lines == [{"skill": "gamma", "error": "no entry in assets/skill-status.json"}]


def test_json_mode_is_silent_and_zero_when_valid(repo, monkeypatch, capsys):
    code, out, _ = _run(monkeypatch, capsys, "--json")
    assert code == 0
    assert out == ""


def test_missing_manifest_exits_with_message(repo, monkeypatch, capsys):
    repo.manifest_path.unlink()
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, capsys)
    assert "Manifest not found" in str(exc.value)


# --- README generation ------------------------------------------------------

def test_build_status_block_lists_skills_sorted_and_legend_in_order(repo):
    block = status.build_status_block(repo.manifest)
    assert block.splitlines() == [
        "| Skill | Status |",
        "|-------|--------|",
        "| `alpha` | Stable |",
        "| `beta` | Preview |",
        "",
        "**Status legend:**",
        "- **Stable** — Ready for use.",
        "- **Preview** — May change.",
        "- **In development** — Not ready.",
    ]


def test_build_status_block_skips_legend_entries_the_manifest_lacks(repo):
    del repo.manifest["statuses"]["in-development"]
    block = status.build_status_block(repo.manifest)
    assert "In development" not in block


def test_write_readme_replaces_block_and_preserves_surroundings(repo, monkeypatch, capsys):
    code, out, _ = _run(monkeypatch, capsys, "--write-readme")
    assert code == 0
    assert out.strip() == "Updated skill status table in README.md."
    text = repo.readme.read_text(encoding="utf-8")
    assert text.startswith("# Repo\n\n" + status.BEGIN_MARKER)
    assert text.endswith(status.END_MARKER + "\n\ntail\n")
    assert "| `alpha` | Stable |" in text
    assert "stale" not in text


def test_write_readme_twice_reports_already_current(repo, monkeypatch, capsys):
    _run(monkeypatch, capsys, "--write-readme")
    before = repo.readme.read_text(encoding="utf-8")
    code, out, _ = _run(monkeypatch, capsys, "--write-readme")
    assert code == 0
    assert out.strip() == "README.md skill status table already current."
    assert repo.readme.read_text(encoding="utf-8") == before


def test_write_readme_without_markers_exits_with_instructions(repo, monkeypatch, capsys):
    repo.readme.write_text("# no markers\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, capsys, "--write-readme")
    assert "Marker pair not found" in str(exc.value)
    assert status.BEGIN_MARKER in str(exc.value)


def test_write_readme_without_readme_exits(repo, monkeypatch, capsys):
    repo.readme.unlink()
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, capsys, "--write-readme")
    assert "README not found" in str(exc.value)


def test_check_readme_fails_when_table_is_stale(repo, monkeypatch, capsys):
    code, out, err = _run(monkeypatch, capsys, "--check-readme")
    assert code == 1
    assert out == ""
    assert "out of date" in err
    assert "--write-readme" in err


def test_check_readme_passes_after_write(repo, monkeypatch, capsys):
    _run(monkeypatch, capsys, "--write-readme")
    code, out, _ = _run(monkeypatch, capsys, "--check-readme")
    assert code == 0
    assert out.strip() == "OK — README.md skill status table is current."


def test_check_readme_fails_when_markers_missing(repo, monkeypatch, capsys):
    repo.readme.write_text("# no markers\n", encoding="utf-8")
    code, _, err = _run(monkeypatch, capsys, "--check-readme")
    assert code == 1
    assert "marker pair not found" in err


def test_check_readme_without_readme_exits(repo, monkeypatch, capsys):
    repo.readme.unlink()
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, capsys, "--check-readme")
    assert "README not found" in str(exc.value)
