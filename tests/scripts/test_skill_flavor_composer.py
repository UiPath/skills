"""Focused contract tests for ``scripts/compose-skill-flavor.py``."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tarfile
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


def _add_package_manifest(repo: Path, version: str = "1.2.3") -> None:
    manifest = {
        "name": "@uipath/skills",
        "version": version,
        "description": "Fixture skills package",
        "license": "MIT",
        "repository": {
            "type": "git",
            "url": "https://github.com/UiPath/skills.git",
        },
        "keywords": ["uipath", "skills"],
        "files": [
            "skills",
            "assets",
            "version-manifest.json",
            "README.md",
            "LICENSE",
        ],
        "scripts": {"prepack": "exit 99"},
    }
    (repo / "package.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (repo / "README.md").write_text("# Fixture package\n", encoding="utf-8")
    (repo / "LICENSE").write_text("MIT fixture\n", encoding="utf-8")
    (repo / "version-manifest.json").write_text(
        json.dumps({"skillsVersion": version}) + "\n", encoding="utf-8"
    )
    assets = repo / "assets"
    assets.mkdir()
    (assets / "shared.txt").write_text("default-only payload\n", encoding="utf-8")


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


def test_generic_discovery_builds_every_flavor_in_stable_order(tmp_path):
    _add_skill(tmp_path, "uipath-first")
    _add_skill(tmp_path, "uipath-second")
    _write_allowlist(
        tmp_path / "skill-flavors" / "zeta-host", "uipath-second"
    )
    _write_allowlist(
        tmp_path / "skill-flavors" / "alpha-host", "uipath-first"
    )

    variants = composer.create_all_variants(tmp_path)
    assert tuple(variant.name for variant in variants) == (
        "default",
        "alpha-host",
        "zeta-host",
    )

    built_variants, output = composer.build_all_skill_trees(tmp_path)
    assert tuple(variant.name for variant in built_variants) == (
        "default",
        "alpha-host",
        "zeta-host",
    )
    assert (output / "default/uipath-first/SKILL.md").is_file()
    assert (output / "default/uipath-second/SKILL.md").is_file()
    assert (output / "alpha-host/uipath-first/SKILL.md").is_file()
    assert not (output / "alpha-host/uipath-second").exists()
    assert (output / "zeta-host/uipath-second/SKILL.md").is_file()


@pytest.mark.parametrize(
    ("flavor_name", "message"),
    [
        ("StudioWeb", "invalid flavor name"),
        ("studio_web", "invalid flavor name"),
        ("default", "is reserved"),
    ],
)
def test_generic_discovery_rejects_invalid_or_reserved_names(
    tmp_path, flavor_name, message
):
    _add_skill(tmp_path, "uipath-example")
    _write_allowlist(
        tmp_path / "skill-flavors" / flavor_name, "uipath-example"
    )

    with pytest.raises(composer.FlavorCompositionError) as error:
        composer.create_all_variants(tmp_path)
    assert message in str(error.value)


def test_generic_discovery_rejects_symlink_and_missing_allowlist(tmp_path):
    _add_skill(tmp_path, "uipath-example")
    flavors = tmp_path / "skill-flavors"
    missing_allowlist = flavors / "missing-list"
    missing_allowlist.mkdir(parents=True)

    with pytest.raises(composer.FlavorCompositionError) as error:
        composer.create_all_variants(tmp_path)
    assert "required flavor allowlist is missing" in str(error.value)

    missing_allowlist.rmdir()
    target = tmp_path / "outside-flavor"
    _write_allowlist(target, "uipath-example")
    flavors.mkdir(exist_ok=True)
    (flavors / "linked-host").symlink_to(target, target_is_directory=True)
    with pytest.raises(composer.FlavorCompositionError) as error:
        composer.create_all_variants(tmp_path)
    assert "flavor entries cannot be symlinks" in str(error.value)


def test_generic_build_failure_preserves_last_successful_output(tmp_path):
    _add_skill(tmp_path, "uipath-example")
    variants, output = composer.build_all_skill_trees(tmp_path)
    assert tuple(variant.name for variant in variants) == ("default",)
    built = output / "default/uipath-example/SKILL.md"
    before = built.read_bytes()

    (tmp_path / "skill-flavors" / "broken-host").mkdir(parents=True)
    with pytest.raises(composer.FlavorCompositionError):
        composer.build_all_skill_trees(tmp_path)
    assert built.read_bytes() == before


def test_package_name_uses_base_name_then_flavor():
    assert composer._package_name("@uipath/skills", "default") == "@uipath/skills"
    assert composer._package_name("@uipath/skills", "studioweb") == (
        "@uipath/skills-studioweb"
    )
    assert composer._package_name("skills", "future-host") == (
        "skills-future-host"
    )


def test_package_name_rejects_derived_name_over_npm_limit():
    flavor = "a" * 200
    with pytest.raises(ValueError, match="derived npm package name is too long"):
        composer._package_name("@uipath/skills", flavor)


def test_generic_build_rejects_symlinked_generated_target(tmp_path):
    _add_skill(tmp_path, "uipath-example")
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "keep.txt"
    sentinel.write_text("user data\n", encoding="utf-8")
    build = tmp_path / "build"
    build.mkdir()
    (build / "skills").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="cannot replace a symlink"):
        composer.build_all_skill_trees(tmp_path)

    assert sentinel.read_text(encoding="utf-8") == "user data\n"
    assert (build / "skills").is_symlink()


def test_pack_builds_marker_free_default_and_every_custom_package(
    tmp_path, monkeypatch
):
    if shutil.which("npm") is None:
        pytest.skip("npm is required for the package integration contract")
    monkeypatch.setenv("npm_config_cache", str(tmp_path / "npm-cache"))

    changed = _add_skill(
        tmp_path,
        "uipath-changed",
        "Before.\n\n"
        + _block("project-creation", "Use the canonical project workflow.")
        + "\nAfter.\n",
    )
    (changed / "asset.bin").write_bytes(b"\x00\x01fixture")
    _add_skill(tmp_path, "uipath-default-only")
    studio_web = tmp_path / "skill-flavors" / "studioweb"
    _write_allowlist(studio_web, "uipath-changed")
    _write_override(
        studio_web,
        "uipath-changed/SKILL.md",
        _block("project-creation", "Use the Studio Web project tool."),
    )
    _write_allowlist(
        tmp_path / "skill-flavors" / "future-host", "uipath-changed"
    )
    _add_package_manifest(tmp_path, version="1.2.3-preview.45")

    packages = composer.pack_all_variants(tmp_path)
    by_variant = {package.variant: package for package in packages}
    assert tuple(by_variant) == ("default", "future-host", "studioweb")
    assert by_variant["default"].package_name == "@uipath/skills"
    assert by_variant["future-host"].package_name == (
        "@uipath/skills-future-host"
    )
    assert by_variant["studioweb"].package_name == "@uipath/skills-studioweb"
    assert {package.version for package in packages} == {"1.2.3-preview.45"}

    default_dir = by_variant["default"].package_dir
    studio_dir = by_variant["studioweb"].package_dir
    default_text = (
        default_dir / "skills/uipath-changed/SKILL.md"
    ).read_text(encoding="utf-8")
    studio_text = (
        studio_dir / "skills/uipath-changed/SKILL.md"
    ).read_text(encoding="utf-8")
    assert "canonical project workflow" in default_text
    assert "Studio Web project tool" in studio_text
    assert "skill-flavor:" not in default_text
    assert "skill-flavor:" not in studio_text
    assert (default_dir / "skills/uipath-default-only/SKILL.md").is_file()
    assert not (studio_dir / "skills/uipath-default-only").exists()
    assert (studio_dir / "skills/uipath-changed/asset.bin").read_bytes() == (
        b"\x00\x01fixture"
    )

    default_manifest = json.loads(
        (default_dir / "package.json").read_text(encoding="utf-8")
    )
    studio_manifest = json.loads(
        (studio_dir / "package.json").read_text(encoding="utf-8")
    )
    assert default_manifest["uipathSkillsFlavor"] == "default"
    assert studio_manifest["uipathSkillsFlavor"] == "studioweb"
    assert "scripts" not in default_manifest
    assert "scripts" not in studio_manifest
    assert (default_dir / "assets/shared.txt").is_file()
    assert not (studio_dir / "assets").exists()

    for package in packages:
        assert package.tarball.is_file()
        with tarfile.open(package.tarball, "r:gz") as archive:
            names = {member.name for member in archive.getmembers()}
            assert "package/package.json" in names
            assert not any(name.startswith("package/skill-flavors/") for name in names)
            assert not any(name.startswith("package/scripts/") for name in names)


def test_pack_failure_preserves_every_last_successful_output(tmp_path, monkeypatch):
    if shutil.which("npm") is None:
        pytest.skip("npm is required for the package integration contract")
    monkeypatch.setenv("npm_config_cache", str(tmp_path / "npm-cache"))
    _add_skill(tmp_path, "uipath-example")
    _write_allowlist(
        tmp_path / "skill-flavors" / "studioweb", "uipath-example"
    )
    _add_package_manifest(tmp_path)

    composer.pack_all_variants(tmp_path)
    build = tmp_path / "build"
    before = {
        name: composer._tree_file_bytes(build / name)
        for name in ("skills", "packages", "npm")
    }

    real_run = composer.subprocess.run
    calls = 0

    def fail_second_pack(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            return composer.subprocess.CompletedProcess(
                args=args[0],
                returncode=1,
                stdout="",
                stderr="simulated npm pack failure",
            )
        return real_run(*args, **kwargs)

    monkeypatch.setattr(composer.subprocess, "run", fail_second_pack)
    with pytest.raises(ValueError, match="simulated npm pack failure"):
        composer.pack_all_variants(tmp_path)

    assert calls == 2
    assert {
        name: composer._tree_file_bytes(build / name)
        for name in ("skills", "packages", "npm")
    } == before
    assert not tuple(build.glob(".skill-flavor-pack-*"))


def test_repacking_removes_artifacts_for_deleted_flavor(tmp_path, monkeypatch):
    if shutil.which("npm") is None:
        pytest.skip("npm is required for the package integration contract")
    monkeypatch.setenv("npm_config_cache", str(tmp_path / "npm-cache"))
    _add_skill(tmp_path, "uipath-example")
    flavor = tmp_path / "skill-flavors" / "temporary-host"
    _write_allowlist(flavor, "uipath-example")
    _add_package_manifest(tmp_path)

    first = composer.pack_all_variants(tmp_path)
    assert {package.variant for package in first} == {"default", "temporary-host"}
    shutil.rmtree(flavor)

    second = composer.pack_all_variants(tmp_path)
    assert tuple(package.variant for package in second) == ("default",)
    assert not (tmp_path / "build/skills/temporary-host").exists()
    assert not (tmp_path / "build/packages/temporary-host").exists()
    assert not any(
        "temporary-host" in path.name for path in (tmp_path / "build/npm").iterdir()
    )


def test_root_pack_guard_is_explicit(tmp_path, capsys):
    result = composer.main(
        ["--repo-root", str(tmp_path), "guard-root-pack"]
    )
    assert result == 1
    assert "npm run skills:pack" in capsys.readouterr().err
