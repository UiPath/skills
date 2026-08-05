"""Focused contract tests for ``scripts/compose-skill-flavor.py``."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "compose-skill-flavor.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("compose_skill_flavor", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


composer = _load_module()


def _entrypoint(name: str, body: str = "Canonical guidance.\n") -> str:
    return (
        "---\n"
        f"name: {name}\n"
        f'description: "{name} test skill"\n'
        "---\n\n"
        f"# {name}\n\n"
        f"{body}"
    )


def _add_skill(repo: Path, name: str, body: str = "Canonical guidance.\n") -> Path:
    skill = repo / "skills" / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(_entrypoint(name, body), encoding="utf-8")
    return skill


def _write_allowlist(flavor: Path, *lines: str) -> None:
    flavor.mkdir(parents=True, exist_ok=True)
    (flavor / "skills.allowlist").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _block(name: str, body: str) -> str:
    return (
        f"<!-- skill-flavor:{name}:start -->\n"
        f"{body}\n"
        f"<!-- skill-flavor:{name}:end -->\n"
    )


def _write_override(flavor: Path, relative: str, text: str) -> Path:
    path = flavor / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_compose_replaces_multiple_blocks_and_copies_reviewed_pass_through(tmp_path):
    changed_body = (
        "Canonical introduction.\n\n"
        + _block("project-creation", "Use the default project workflow.")
        + "\nShared middle.\n\n"
        + _block("validation", "Run the default validation workflow.")
        + "\nCanonical ending.\n"
    )
    changed = _add_skill(tmp_path, "uipath-changed", changed_body)
    references = changed / "references"
    references.mkdir()
    (references / "guide.md").write_text("Shared guide.\n", encoding="utf-8")
    (changed / "asset.bin").write_bytes(b"\x00\x01canonical")

    pass_through = _add_skill(tmp_path, "uipath-pass-through")
    (pass_through / "notes.md").write_text("Unchanged notes.\n", encoding="utf-8")
    _add_skill(tmp_path, "uipath-not-reviewed")

    flavor = tmp_path / "flavors" / "studioweb"
    _write_allowlist(
        flavor,
        "# Reviewed Studio Web skills",
        "uipath-pass-through",
        "",
        "uipath-changed",
    )
    # Override order does not affect canonical block order in the result.
    _write_override(
        flavor,
        "uipath-changed/SKILL.md",
        _block("validation", "Use Studio Web validation.")
        + "\n"
        + _block("project-creation", "Use the Studio Web project tool."),
    )

    canonical_before = (changed / "SKILL.md").read_bytes()
    plan = composer.create_composition_plan(tmp_path, flavor)
    assert plan.skills == ("uipath-changed", "uipath-pass-through")
    assert plan.replacement_count == 2
    assert plan.overridden_files == (
        Path("uipath-changed/SKILL.md"),
    )

    output = tmp_path / "complete-flavor"
    composer.materialize_composition(plan, output)
    composed = (output / "uipath-changed/SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "Canonical introduction." in composed
    assert "Shared middle." in composed
    assert "Canonical ending." in composed
    assert "Use the Studio Web project tool." in composed
    assert "Use Studio Web validation." in composed
    assert "default project workflow" not in composed
    assert "default validation workflow" not in composed
    assert composed.index("Studio Web project tool") < composed.index(
        "Studio Web validation"
    )
    assert "<!-- skill-flavor:" not in composed

    assert (output / "uipath-changed/references/guide.md").read_text() == (
        "Shared guide.\n"
    )
    assert (output / "uipath-changed/asset.bin").read_bytes() == (
        b"\x00\x01canonical"
    )
    assert (output / "uipath-pass-through/SKILL.md").read_bytes() == (
        pass_through / "SKILL.md"
    ).read_bytes()
    assert not (output / "uipath-not-reviewed").exists()
    assert (changed / "SKILL.md").read_bytes() == canonical_before


def test_default_plan_builds_every_canonical_skill_and_strips_boundaries(tmp_path):
    marked = _add_skill(
        tmp_path,
        "uipath-marked",
        "Before.\n\n"
        + _block("project-creation", "Use the canonical project workflow.")
        + "\nAfter.\n",
    )
    unmarked = _add_skill(tmp_path, "uipath-unmarked")
    (marked / "asset.bin").write_bytes(b"canonical-asset")

    plan = composer.create_default_plan(tmp_path)
    assert plan.flavor_root is None
    assert plan.skills == ("uipath-marked", "uipath-unmarked")
    assert plan.replacement_count == 0

    output = tmp_path / "build" / "skills" / "default"
    composer.materialize_composition(plan, output)
    built_marked = (output / "uipath-marked/SKILL.md").read_text()
    assert "Before." in built_marked
    assert "Use the canonical project workflow." in built_marked
    assert "After." in built_marked
    assert "<!-- skill-flavor:" not in built_marked
    assert (output / "uipath-unmarked/SKILL.md").read_bytes() == (
        unmarked / "SKILL.md"
    ).read_bytes()
    assert (output / "uipath-marked/asset.bin").read_bytes() == (
        b"canonical-asset"
    )


def test_build_command_writes_default_and_named_custom_trees(tmp_path):
    _add_skill(
        tmp_path,
        "uipath-reviewed",
        _block("project-creation", "Canonical project workflow."),
    )
    _add_skill(tmp_path, "uipath-default-only")
    flavor = tmp_path / "skill-flavors" / "studioweb"
    _write_allowlist(flavor, "uipath-reviewed")
    _write_override(
        flavor,
        "uipath-reviewed/SKILL.md",
        _block("project-creation", "Studio Web project tool."),
    )

    output_root = tmp_path / "artifacts"
    result = composer.main(
        [
            "--repo-root",
            str(tmp_path),
            "build",
            str(flavor),
            str(output_root),
        ]
    )
    assert result == 0
    default_text = (
        output_root / "default/uipath-reviewed/SKILL.md"
    ).read_text()
    custom_text = (
        output_root / "studioweb/uipath-reviewed/SKILL.md"
    ).read_text()
    assert "Canonical project workflow." in default_text
    assert "Studio Web project tool." in custom_text
    assert "skill-flavor:" not in default_text
    assert "skill-flavor:" not in custom_text
    assert (output_root / "default/uipath-default-only/SKILL.md").is_file()
    assert not (output_root / "studioweb/uipath-default-only").exists()


def test_build_default_command_uses_first_class_default_output(tmp_path):
    _add_skill(
        tmp_path,
        "uipath-example",
        _block("project-creation", "Canonical project workflow."),
    )

    result = composer.main(["--repo-root", str(tmp_path), "build-default"])
    assert result == 0
    built = tmp_path / "build/skills/default/uipath-example/SKILL.md"
    assert built.is_file()
    assert "Canonical project workflow." in built.read_text()
    assert "skill-flavor:" not in built.read_text()


def test_paired_build_preflights_both_outputs_before_writing(tmp_path):
    _add_skill(tmp_path, "uipath-example")
    flavor = tmp_path / "skill-flavors" / "studioweb"
    _write_allowlist(flavor, "uipath-example")
    output_root = tmp_path / "artifacts"
    blocked = output_root / "studioweb"
    blocked.mkdir(parents=True)
    (blocked / "keep.txt").write_text("user data\n", encoding="utf-8")

    result = composer.main(
        [
            "--repo-root",
            str(tmp_path),
            "build",
            str(flavor),
            str(output_root),
        ]
    )
    assert result == 1
    assert not (output_root / "default").exists()
    assert (blocked / "keep.txt").read_text() == "user data\n"


def test_malformed_marker_is_rejected(tmp_path):
    _add_skill(
        tmp_path,
        "uipath-example",
        _block("project-creation", "Canonical project creation."),
    )
    flavor = tmp_path / "flavor"
    _write_allowlist(flavor, "uipath-example")
    _write_override(
        flavor,
        "uipath-example/SKILL.md",
        "<!-- skill-flavor:project-creation:start -->\n"
        "Studio Web guidance.\n"
        "<!-- skill-flavor:different:end -->\n",
    )

    with pytest.raises(composer.FlavorCompositionError) as error:
        composer.create_composition_plan(tmp_path, flavor)
    assert "does not match 'project-creation'" in str(error.value)


def test_duplicate_canonical_marker_is_rejected(tmp_path):
    _add_skill(
        tmp_path,
        "uipath-example",
        _block("project-creation", "First default.")
        + _block("project-creation", "Second default."),
    )
    flavor = tmp_path / "flavor"
    _write_allowlist(flavor, "uipath-example")

    with pytest.raises(composer.FlavorCompositionError) as error:
        composer.create_composition_plan(tmp_path, flavor)
    assert "duplicate flavor block 'project-creation'" in str(error.value)


def test_override_marker_missing_from_canonical_is_rejected(tmp_path):
    _add_skill(tmp_path, "uipath-example")
    flavor = tmp_path / "flavor"
    _write_allowlist(flavor, "uipath-example")
    _write_override(
        flavor,
        "uipath-example/SKILL.md",
        _block("project-creation", "Studio Web guidance."),
    )

    with pytest.raises(composer.FlavorCompositionError) as error:
        composer.create_composition_plan(tmp_path, flavor)
    assert "has no matching canonical marker" in str(error.value)


def test_override_with_missing_canonical_target_is_rejected(tmp_path):
    _add_skill(tmp_path, "uipath-example")
    flavor = tmp_path / "flavor"
    _write_allowlist(flavor, "uipath-example")
    _write_override(
        flavor,
        "uipath-example/references/new.md",
        _block("new-guidance", "Studio Web-only file."),
    )

    with pytest.raises(composer.FlavorCompositionError) as error:
        composer.create_composition_plan(tmp_path, flavor)
    assert "canonical target does not exist" in str(error.value)


def test_override_with_stray_unmarked_content_is_rejected(tmp_path):
    _add_skill(
        tmp_path,
        "uipath-example",
        _block("project-creation", "Canonical project creation."),
    )
    flavor = tmp_path / "flavor"
    _write_allowlist(flavor, "uipath-example")
    _write_override(
        flavor,
        "uipath-example/SKILL.md",
        "This text is outside a replacement block.\n\n"
        + _block("project-creation", "Studio Web guidance."),
    )

    with pytest.raises(composer.FlavorCompositionError) as error:
        composer.create_composition_plan(tmp_path, flavor)
    assert "override contains stray unmarked content" in str(error.value)


@pytest.mark.parametrize(
    ("allowlist", "message"),
    [
        (("uipath-example", "uipath-example"), "duplicate allowlist entry"),
        (("uipath-missing",), "has no canonical skills/uipath-missing/SKILL.md"),
        (("uipath/example",), "invalid skill name"),
    ],
)
def test_invalid_allowlist_is_rejected(tmp_path, allowlist, message):
    _add_skill(tmp_path, "uipath-example")
    flavor = tmp_path / "flavor"
    _write_allowlist(flavor, *allowlist)

    with pytest.raises(composer.FlavorCompositionError) as error:
        composer.create_composition_plan(tmp_path, flavor)
    assert message in str(error.value)


def test_override_for_non_allowlisted_skill_is_rejected(tmp_path):
    _add_skill(tmp_path, "uipath-reviewed")
    _add_skill(
        tmp_path,
        "uipath-not-reviewed",
        _block("project-creation", "Canonical project creation."),
    )
    flavor = tmp_path / "flavor"
    _write_allowlist(flavor, "uipath-reviewed")
    _write_override(
        flavor,
        "uipath-not-reviewed/SKILL.md",
        _block("project-creation", "Studio Web guidance."),
    )

    with pytest.raises(composer.FlavorCompositionError) as error:
        composer.create_composition_plan(tmp_path, flavor)
    assert "override belongs to non-allowlisted skill 'uipath-not-reviewed'" in str(
        error.value
    )


def test_materializer_refuses_nonempty_output(tmp_path):
    _add_skill(tmp_path, "uipath-example")
    flavor = tmp_path / "flavor"
    _write_allowlist(flavor, "uipath-example")
    plan = composer.create_composition_plan(tmp_path, flavor)
    output = tmp_path / "output"
    output.mkdir()
    (output / "keep.txt").write_text("user data\n", encoding="utf-8")

    with pytest.raises(ValueError, match="must be empty"):
        composer.materialize_composition(plan, output)
    assert (output / "keep.txt").read_text(encoding="utf-8") == "user data\n"
