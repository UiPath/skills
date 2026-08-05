#!/usr/bin/env python3
"""Compose complete skill trees and npm packages from sparse flavor blocks.

Flavor directories use this deliberately small layout::

    skill-flavors/studioweb/
      skills.allowlist
      uipath-example/
        SKILL.md

``skills.allowlist`` contains one canonical skill directory name per line.
Blank lines and lines beginning with ``#`` are ignored. Every listed skill is
copied in full, so a reviewed skill needs no override to pass through.

An override file mirrors its canonical path and may contain only complete
replacement blocks, separated by whitespace::

    <!-- skill-flavor:project-creation:start -->
    Flavor-specific guidance.
    <!-- skill-flavor:project-creation:end -->

The canonical file remains complete and contains the same marked block. The
composer replaces that entire block while retaining all unmarked canonical
content. Generated trees are build outputs; this script never edits sources.

Validate and build every discovered flavor from the repository root::

    python3 scripts/compose-skill-flavor.py validate
    python3 scripts/compose-skill-flavor.py build
    python3 scripts/compose-skill-flavor.py pack

The no-argument commands discover every direct directory under
``skill-flavors/``. ``build`` writes complete trees under ``build/skills``.
``pack`` rebuilds those trees, stages one npm package per variant under
``build/packages``, and creates real tarballs under ``build/npm``. The default
package keeps the root name (``@uipath/skills``); a flavor named ``studioweb``
becomes ``@uipath/skills-studioweb``. Adding a flavor directory needs no script,
workflow, or package-manifest registration.

Marker boundary comments are source syntax. They are removed from every built
tree and verified absent from every staged package and tarball. Generated
artifacts are replaced only after every flavor validates and every tarball is
successfully inspected. The legacy explicit-flavor commands remain available
for focused debugging and never overwrite a non-empty output directory.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST_FILENAME = "skills.allowlist"
FLAVORS_DIRNAME = "skill-flavors"
DEFAULT_VARIANT = "default"
PACKAGE_NAME_MAX_LENGTH = 214
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKER_TOKEN = "<!-- skill-flavor:"
MARKER_BYTES = MARKER_TOKEN.encode("utf-8")
MARKER_LINE_RE = re.compile(
    r"^[ \t]*<!-- skill-flavor:"
    r"([a-z0-9]+(?:-[a-z0-9]+)*):(start|end) -->"
    r"[ \t]*(?:\r\n|\n|\r|$)$"
)


class FlavorCompositionError(Exception):
    """Raised when a flavor cannot be composed deterministically."""

    def __init__(self, findings: list[str]):
        self.findings = findings
        super().__init__("\n".join(findings))


@dataclass(frozen=True)
class MarkerBlock:
    """One complete marker block and its character span in a source file."""

    name: str
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class ComposedFile:
    """A file copied verbatim or written with composed UTF-8 content."""

    relative_path: PurePosixPath
    source_path: Path
    composed_bytes: bytes | None = None


@dataclass(frozen=True)
class CompositionPlan:
    """A validated, deterministic flavor composition plan."""

    flavor_root: Path | None
    skills: tuple[str, ...]
    files: tuple[ComposedFile, ...]
    overridden_files: tuple[PurePosixPath, ...]
    replacement_count: int


@dataclass(frozen=True)
class SkillVariant:
    """One complete output variant and its validated composition plan."""

    name: str
    plan: CompositionPlan


@dataclass(frozen=True)
class PackedPackage:
    """A staged npm package and the tarball created from it."""

    variant: str
    package_name: str
    version: str
    package_dir: Path
    tarball: Path


def _read_utf8(path: Path, findings: list[str], kind: str) -> str | None:
    try:
        return path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        findings.append(f"{path}: {kind} must be UTF-8")
        return None
    except OSError as exc:
        findings.append(f"{path}: could not read {kind}: {exc}")
        return None


def _read_allowlist(flavor_root: Path, findings: list[str]) -> tuple[str, ...]:
    path = flavor_root / ALLOWLIST_FILENAME
    text = _read_utf8(path, findings, "allowlist")
    if text is None:
        if not path.exists():
            findings.append(f"{path}: required flavor allowlist is missing")
        return ()

    skills: list[str] = []
    seen: set[str] = set()
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        value = raw_line.strip()
        if not value or value.startswith("#"):
            continue
        if not SKILL_NAME_RE.fullmatch(value):
            findings.append(
                f"{path}:{line_number}: invalid skill name {value!r}; "
                "use one lowercase kebab-case directory name per line"
            )
            continue
        if value in seen:
            findings.append(f"{path}:{line_number}: duplicate allowlist entry {value!r}")
            continue
        seen.add(value)
        skills.append(value)

    if not skills:
        findings.append(f"{path}: allowlist must select at least one skill")
    return tuple(sorted(skills))


def _parse_marker_blocks(
    path: Path,
    text: str,
    findings: list[str],
) -> tuple[MarkerBlock, ...]:
    blocks: list[MarkerBlock] = []
    seen: set[str] = set()
    opened_name: str | None = None
    opened_start = 0
    opened_line = 0
    offset = 0

    for line_number, line in enumerate(text.splitlines(keepends=True), start=1):
        line_start = offset
        offset += len(line)
        if MARKER_TOKEN not in line:
            continue

        match = MARKER_LINE_RE.fullmatch(line)
        if match is None:
            findings.append(
                f"{path}:{line_number}: malformed flavor marker; markers must "
                "occupy a line and use '<!-- skill-flavor:<name>:start|end -->'"
            )
            continue

        name, boundary = match.groups()
        if boundary == "start":
            if opened_name is not None:
                findings.append(
                    f"{path}:{line_number}: nested flavor marker {name!r} inside "
                    f"{opened_name!r} opened on line {opened_line}"
                )
                continue
            if name in seen:
                findings.append(f"{path}:{line_number}: duplicate flavor block {name!r}")
                continue
            opened_name = name
            opened_start = line_start
            opened_line = line_number
            continue

        if opened_name is None:
            findings.append(
                f"{path}:{line_number}: flavor marker {name!r} ends without a start"
            )
            continue
        if name != opened_name:
            findings.append(
                f"{path}:{line_number}: flavor marker {name!r} does not match "
                f"{opened_name!r} opened on line {opened_line}"
            )
            opened_name = None
            continue

        blocks.append(
            MarkerBlock(
                name=name,
                start=opened_start,
                end=offset,
                text=text[opened_start:offset],
            )
        )
        seen.add(name)
        opened_name = None

    if opened_name is not None:
        findings.append(
            f"{path}:{opened_line}: flavor block {opened_name!r} has no end marker"
        )
    return tuple(blocks)


def _validate_override_has_only_blocks(
    path: Path,
    text: str,
    blocks: tuple[MarkerBlock, ...],
    findings: list[str],
) -> None:
    if not blocks:
        findings.append(f"{path}: override must contain at least one complete flavor block")
        return

    cursor = 0
    for block in blocks:
        if text[cursor:block.start].strip():
            findings.append(f"{path}: override contains stray unmarked content")
            return
        cursor = block.end
    if text[cursor:].strip():
        findings.append(f"{path}: override contains stray unmarked content")


def _compose_text(
    canonical_text: str,
    canonical_blocks: tuple[MarkerBlock, ...],
    override_blocks: tuple[MarkerBlock, ...],
) -> str:
    replacements = {block.name: block.text for block in override_blocks}
    pieces: list[str] = []
    cursor = 0
    for block in canonical_blocks:
        pieces.append(canonical_text[cursor:block.start])
        pieces.append(replacements.get(block.name, block.text))
        cursor = block.end
    pieces.append(canonical_text[cursor:])
    return "".join(pieces)


def _strip_marker_boundaries(text: str) -> str:
    """Remove valid marker lines while retaining every block body."""

    return "".join(
        "" if MARKER_LINE_RE.fullmatch(line) else line
        for line in text.splitlines(keepends=True)
    )


def _discover_default_skills(repo_root: Path) -> tuple[str, ...]:
    skills_root = repo_root / "skills"
    if not skills_root.is_dir():
        return ()
    return tuple(
        child.name
        for child in sorted(skills_root.iterdir())
        if child.is_dir() and (child / "SKILL.md").is_file()
    )


def _collect_canonical_files(
    repo_root: Path,
    skills: tuple[str, ...],
    findings: list[str],
) -> tuple[
    dict[str, Path],
    dict[str, str],
    dict[str, tuple[MarkerBlock, ...]],
]:
    canonical_files: dict[str, Path] = {}
    canonical_text: dict[str, str] = {}
    canonical_blocks: dict[str, tuple[MarkerBlock, ...]] = {}

    for skill in skills:
        skill_root = repo_root / "skills" / skill
        for source in sorted(skill_root.rglob("*")):
            if source.is_symlink():
                findings.append(f"{source}: canonical skill trees cannot contain symlinks")
                continue
            if not source.is_file():
                continue
            relative = source.relative_to(repo_root).as_posix()
            canonical_files[relative] = source
            if source.suffix.lower() != ".md":
                continue
            text = _read_utf8(source, findings, "canonical Markdown")
            if text is None:
                continue
            canonical_text[relative] = text
            canonical_blocks[relative] = _parse_marker_blocks(source, text, findings)

    return canonical_files, canonical_text, canonical_blocks


def _planned_files(
    canonical_files: dict[str, Path],
    canonical_text: dict[str, str],
    replacements: dict[str, str] | None = None,
) -> tuple[ComposedFile, ...]:
    replacements = replacements or {}
    planned: list[ComposedFile] = []
    for relative in sorted(canonical_files):
        source = canonical_files[relative]
        composed_bytes: bytes | None = None
        text = replacements.get(relative, canonical_text.get(relative))
        if text is not None:
            final_bytes = _strip_marker_boundaries(text).encode("utf-8")
            source_bytes = source.read_bytes()
            if final_bytes != source_bytes:
                composed_bytes = final_bytes
        planned.append(
            ComposedFile(
                relative_path=PurePosixPath(relative).relative_to("skills"),
                source_path=source,
                composed_bytes=composed_bytes,
            )
        )
    return tuple(planned)


def create_default_plan(repo_root: Path = REPO_ROOT) -> CompositionPlan:
    """Build the default artifact from every complete canonical skill."""

    repo_root = repo_root.resolve()
    findings: list[str] = []
    skills = _discover_default_skills(repo_root)
    if not skills:
        findings.append(f"{repo_root / 'skills'}: no canonical skills found")
    canonical_files, canonical_text, _ = _collect_canonical_files(
        repo_root, skills, findings
    )
    if findings:
        raise FlavorCompositionError(findings)
    return CompositionPlan(
        flavor_root=None,
        skills=skills,
        files=_planned_files(canonical_files, canonical_text),
        overridden_files=(),
        replacement_count=0,
    )


def create_composition_plan(
    repo_root: Path = REPO_ROOT,
    flavor_root: Path | None = None,
) -> CompositionPlan:
    """Validate a flavor and return its complete deterministic file plan."""

    repo_root = repo_root.resolve()
    if flavor_root is None:
        raise ValueError("flavor_root is required")
    flavor_root = flavor_root.resolve()

    findings: list[str] = []
    if not flavor_root.is_dir():
        raise FlavorCompositionError([f"flavor directory does not exist: {flavor_root}"])

    skills = _read_allowlist(flavor_root, findings)
    for skill in skills:
        skill_root = repo_root / "skills" / skill
        entrypoint = skill_root / "SKILL.md"
        if not entrypoint.is_file():
            findings.append(
                f"{flavor_root / ALLOWLIST_FILENAME}: allowlisted skill {skill!r} "
                f"has no canonical skills/{skill}/SKILL.md"
            )

    present_skills = tuple(
        skill
        for skill in skills
        if (repo_root / "skills" / skill / "SKILL.md").is_file()
    )
    canonical_files, canonical_text, canonical_blocks = _collect_canonical_files(
        repo_root, present_skills, findings
    )

    overrides: dict[str, str] = {}
    replacement_count = 0
    allowlist_path = flavor_root / ALLOWLIST_FILENAME
    for override in sorted(flavor_root.rglob("*")):
        if override == allowlist_path or override.is_dir():
            continue
        if override.is_symlink():
            findings.append(f"{override}: flavor directories cannot contain symlinks")
            continue
        relative = override.relative_to(flavor_root)
        flavor_relative = PurePosixPath(relative.as_posix())
        if len(flavor_relative.parts) < 2:
            findings.append(
                f"{override}: override path must mirror <skill>/<file>.md"
            )
            continue
        skill = flavor_relative.parts[0]
        if skill not in skills:
            findings.append(
                f"{override}: override belongs to non-allowlisted skill {skill!r}"
            )
            continue
        logical = PurePosixPath("skills") / flavor_relative
        canonical = canonical_files.get(logical.as_posix())
        if canonical is None:
            findings.append(f"{override}: canonical target does not exist: {logical}")
            continue
        if override.suffix.lower() != ".md":
            findings.append(f"{override}: only Markdown files may contain flavor blocks")
            continue

        override_text = _read_utf8(override, findings, "flavor override")
        if override_text is None:
            continue
        parsed_override = _parse_marker_blocks(override, override_text, findings)
        _validate_override_has_only_blocks(
            override, override_text, parsed_override, findings
        )

        available = {block.name for block in canonical_blocks.get(logical.as_posix(), ())}
        for block in parsed_override:
            if block.name not in available:
                findings.append(
                    f"{override}: flavor block {block.name!r} has no matching "
                    f"canonical marker in {logical}"
                )

        if parsed_override and all(block.name in available for block in parsed_override):
            source_text = canonical_text.get(logical.as_posix())
            if source_text is not None:
                composed = _compose_text(
                    source_text,
                    canonical_blocks[logical.as_posix()],
                    parsed_override,
                )
                overrides[logical.as_posix()] = composed
                replacement_count += len(parsed_override)

    if findings:
        raise FlavorCompositionError(findings)

    return CompositionPlan(
        flavor_root=flavor_root,
        skills=skills,
        files=_planned_files(canonical_files, canonical_text, overrides),
        overridden_files=tuple(
            PurePosixPath(path).relative_to("skills") for path in sorted(overrides)
        ),
        replacement_count=replacement_count,
    )


def discover_flavor_roots(repo_root: Path = REPO_ROOT) -> tuple[Path, ...]:
    """Discover custom flavors by directory convention, in stable name order."""

    repo_root = repo_root.resolve()
    flavors_root = repo_root / FLAVORS_DIRNAME
    if not flavors_root.exists():
        return ()
    if flavors_root.is_symlink():
        raise FlavorCompositionError(
            [f"{flavors_root}: flavor root cannot be a symlink"]
        )
    if not flavors_root.is_dir():
        raise FlavorCompositionError(
            [f"{flavors_root}: flavor root is not a directory"]
        )

    findings: list[str] = []
    flavor_roots: list[Path] = []
    for child in sorted(flavors_root.iterdir(), key=lambda path: path.name):
        if child.is_symlink():
            findings.append(f"{child}: flavor entries cannot be symlinks")
            continue
        if not child.is_dir():
            continue
        if not SKILL_NAME_RE.fullmatch(child.name):
            findings.append(
                f"{child}: invalid flavor name {child.name!r}; "
                "use a lowercase kebab-case directory name"
            )
            continue
        if child.name == DEFAULT_VARIANT:
            findings.append(
                f"{child}: {DEFAULT_VARIANT!r} is reserved for the canonical package"
            )
            continue
        flavor_roots.append(child)

    if findings:
        raise FlavorCompositionError(findings)
    return tuple(flavor_roots)


def create_all_variants(repo_root: Path = REPO_ROOT) -> tuple[SkillVariant, ...]:
    """Validate the default and every convention-discovered custom flavor."""

    repo_root = repo_root.resolve()
    findings: list[str] = []
    variants: list[SkillVariant] = []

    try:
        variants.append(
            SkillVariant(DEFAULT_VARIANT, create_default_plan(repo_root))
        )
    except FlavorCompositionError as exc:
        findings.extend(exc.findings)

    flavor_roots: tuple[Path, ...] = ()
    try:
        flavor_roots = discover_flavor_roots(repo_root)
    except FlavorCompositionError as exc:
        findings.extend(exc.findings)

    for flavor_root in flavor_roots:
        try:
            variants.append(
                SkillVariant(
                    flavor_root.name,
                    create_composition_plan(repo_root, flavor_root),
                )
            )
        except FlavorCompositionError as exc:
            findings.extend(exc.findings)

    if findings:
        # The same malformed canonical block can be observed through multiple
        # flavor plans. Keep diagnostics comprehensive without repeating lines.
        raise FlavorCompositionError(list(dict.fromkeys(findings)))
    return tuple(variants)


def _validate_output_directory(output_dir: Path) -> Path:
    output_dir = output_dir.resolve()
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError(f"composition output is not a directory: {output_dir}")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"composition output must be empty: {output_dir}")
    return output_dir


def materialize_composition(plan: CompositionPlan, output_dir: Path) -> None:
    """Write a validated plan without deleting or overwriting existing data."""

    output_dir = _validate_output_directory(output_dir)

    for item in plan.files:
        destination = output_dir.joinpath(*item.relative_path.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if item.composed_bytes is None:
            shutil.copy2(item.source_path, destination)
        else:
            destination.write_bytes(item.composed_bytes)


def _prepare_build_root(repo_root: Path) -> Path:
    """Return the repository-owned build root after basic safety checks."""

    build_root = repo_root.resolve() / "build"
    if build_root.is_symlink():
        raise ValueError(f"generated build root cannot be a symlink: {build_root}")
    if build_root.exists() and not build_root.is_dir():
        raise ValueError(f"generated build root is not a directory: {build_root}")
    build_root.mkdir(parents=True, exist_ok=True)
    return build_root


def _materialize_variants(
    variants: tuple[SkillVariant, ...], output_root: Path
) -> None:
    output_root.mkdir(parents=True, exist_ok=False)
    for variant in variants:
        materialize_composition(variant.plan, output_root / variant.name)


def _marker_findings(root: Path, label: str) -> list[str]:
    findings: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            findings.append(f"{path}: {label} cannot contain symlinks")
            continue
        if not path.is_file():
            continue
        if MARKER_BYTES in path.read_bytes():
            findings.append(f"{path}: flavor marker leaked into {label}")
    return findings


def _replace_generated_directories(
    replacements: tuple[tuple[Path, Path], ...]
) -> None:
    """Swap validated temporary directories into their generated locations."""

    if not replacements:
        return
    parents = {target.parent.resolve() for _, target in replacements}
    if len(parents) != 1:
        raise ValueError("generated outputs must share one build directory")
    parent = next(iter(parents))

    seen_targets: set[Path] = set()
    for source, target in replacements:
        if not source.is_dir() or source.is_symlink():
            raise ValueError(f"generated source is not a real directory: {source}")
        target = target.absolute()
        if target in seen_targets:
            raise ValueError(f"duplicate generated output target: {target}")
        seen_targets.add(target)
        if target.is_symlink():
            raise ValueError(f"generated output cannot replace a symlink: {target}")
        if target.exists() and not target.is_dir():
            raise ValueError(f"generated output is not a directory: {target}")

    backup_root = Path(
        tempfile.mkdtemp(prefix=".skill-flavor-backup-", dir=parent)
    )
    backed_up: list[tuple[Path, Path]] = []
    installed: list[Path] = []
    try:
        for _, target in replacements:
            if not target.exists():
                continue
            backup = backup_root / target.name
            os.replace(target, backup)
            backed_up.append((target, backup))

        for source, target in replacements:
            os.replace(source, target)
            installed.append(target)
    except Exception:
        for target in reversed(installed):
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            elif target.exists() or target.is_symlink():
                target.unlink()
        for target, backup in reversed(backed_up):
            if backup.exists():
                os.replace(backup, target)
        raise
    finally:
        shutil.rmtree(backup_root, ignore_errors=True)


def build_all_skill_trees(
    repo_root: Path = REPO_ROOT,
) -> tuple[tuple[SkillVariant, ...], Path]:
    """Build every complete tree, replacing only generated ``build/skills``."""

    repo_root = repo_root.resolve()
    variants = create_all_variants(repo_root)
    build_root = _prepare_build_root(repo_root)
    temporary_root = Path(
        tempfile.mkdtemp(prefix=".skill-flavor-build-", dir=build_root)
    )
    temporary_skills = temporary_root / "skills"
    try:
        _materialize_variants(variants, temporary_skills)
        findings = _marker_findings(temporary_skills, "built skill tree")
        if findings:
            raise FlavorCompositionError(findings)
        final_skills = build_root / "skills"
        _replace_generated_directories(((temporary_skills, final_skills),))
        return variants, final_skills
    finally:
        shutil.rmtree(temporary_root, ignore_errors=True)


def _load_package_manifest(repo_root: Path) -> dict[str, object]:
    path = repo_root / "package.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"npm package manifest is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"npm package manifest is invalid JSON: {path}: {exc}") from exc

    if not isinstance(manifest, dict):
        raise ValueError(f"npm package manifest must be an object: {path}")
    for key in ("name", "version"):
        if not isinstance(manifest.get(key), str) or not manifest[key]:
            raise ValueError(f"npm package manifest requires a non-empty {key!r}: {path}")
    files = manifest.get("files")
    if not isinstance(files, list) or not all(
        isinstance(entry, str) and entry for entry in files
    ):
        raise ValueError(f"npm package manifest requires a string 'files' list: {path}")
    return manifest


def _package_name(base_name: str, variant: str) -> str:
    if variant == DEFAULT_VARIANT:
        return base_name
    if base_name.startswith("@"):
        if "/" not in base_name:
            raise ValueError(f"invalid scoped npm package name: {base_name!r}")
        scope, package = base_name.split("/", 1)
        result = f"{scope}/{package}-{variant}"
    else:
        result = f"{base_name}-{variant}"
    if len(result) > PACKAGE_NAME_MAX_LENGTH:
        raise ValueError(
            f"derived npm package name is too long ({len(result)} characters): {result}"
        )
    return result


def _checked_payload_path(repo_root: Path, entry: str) -> tuple[Path, Path]:
    relative = PurePosixPath(entry)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or any(character in entry for character in "*?[]\\")
    ):
        raise ValueError(f"unsupported npm package 'files' entry: {entry!r}")
    source = repo_root.joinpath(*relative.parts)
    return source, Path(*relative.parts)


def _assert_tree_has_no_symlinks(root: Path, label: str) -> None:
    if root.is_symlink():
        raise ValueError(f"{label} cannot be a symlink: {root}")
    if root.is_dir():
        for path in root.rglob("*"):
            if path.is_symlink():
                raise ValueError(f"{label} cannot contain symlinks: {path}")


def _copy_payload(source: Path, destination: Path, label: str) -> None:
    _assert_tree_has_no_symlinks(source, label)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination)
    elif source.is_file():
        shutil.copy2(source, destination)
    else:
        raise ValueError(f"{label} is neither a file nor directory: {source}")


def _generated_package_manifest(
    source_manifest: dict[str, object], variant: str, custom_files: list[str]
) -> dict[str, object]:
    manifest = copy.deepcopy(source_manifest)
    base_name = str(source_manifest["name"])
    manifest["name"] = _package_name(base_name, variant)
    manifest["uipathSkillsFlavor"] = variant
    # Repository-only lifecycle commands must never run from a published package.
    manifest.pop("scripts", None)

    if variant != DEFAULT_VARIANT:
        manifest["description"] = (
            f"UiPath agent skills composed for the {variant} host environment."
        )
        keywords = [
            item
            for item in source_manifest.get("keywords", [])
            if isinstance(item, str)
        ]
        for keyword in ("skill-flavor", variant):
            if keyword not in keywords:
                keywords.append(keyword)
        manifest["keywords"] = keywords
        manifest["files"] = custom_files
    return manifest


def _custom_package_readme(package_name: str, variant: str) -> str:
    return (
        f"# {package_name}\n\n"
        f"This package is the generated **{variant}** flavor of "
        "[UiPath skills](https://github.com/UiPath/skills).\n\n"
        "It contains complete, marker-free skill files selected and reviewed "
        f"for the `{variant}` host. Consumers should copy the files under "
        "`skills/` directly; no runtime composition is required.\n\n"
        "This package is generated from the canonical repository. Do not edit "
        "its contents directly.\n"
    )


def _stage_packages(
    repo_root: Path,
    variants: tuple[SkillVariant, ...],
    skill_trees_root: Path,
    packages_root: Path,
) -> dict[str, tuple[str, str, Path]]:
    source_manifest = _load_package_manifest(repo_root)
    base_name = str(source_manifest["name"])
    version = str(source_manifest["version"])
    source_files = list(source_manifest["files"])
    # Validate every derived name and every source payload entry before writing.
    for variant in variants:
        _package_name(base_name, variant.name)
    checked_payload = [
        (entry, *_checked_payload_path(repo_root, entry)) for entry in source_files
    ]

    packages_root.mkdir(parents=True, exist_ok=False)
    staged: dict[str, tuple[str, str, Path]] = {}
    for variant in variants:
        package_dir = packages_root / variant.name
        package_dir.mkdir()
        built_skills = skill_trees_root / variant.name
        if not built_skills.is_dir() or built_skills.is_symlink():
            raise ValueError(
                f"complete built skill tree is missing for {variant.name}: {built_skills}"
            )

        if variant.name == DEFAULT_VARIANT:
            for entry, source, relative in checked_payload:
                if PurePosixPath(entry).parts == ("skills",):
                    continue
                if not source.exists():
                    # npm itself ignores absent entries in the root `files` list.
                    continue
                _copy_payload(source, package_dir / relative, "default package payload")
            custom_files: list[str] = []
        else:
            custom_files = ["skills", "README.md", "LICENSE"]
            license_path = repo_root / "LICENSE"
            if not license_path.is_file():
                raise ValueError(f"custom packages require a LICENSE file: {license_path}")
            _copy_payload(license_path, package_dir / "LICENSE", "package license")
            version_manifest = repo_root / "version-manifest.json"
            if version_manifest.is_file():
                _copy_payload(
                    version_manifest,
                    package_dir / "version-manifest.json",
                    "package version manifest",
                )
                custom_files.append("version-manifest.json")

        _copy_payload(built_skills, package_dir / "skills", "built skill tree")
        package_name = _package_name(base_name, variant.name)
        if variant.name != DEFAULT_VARIANT:
            (package_dir / "README.md").write_text(
                _custom_package_readme(package_name, variant.name),
                encoding="utf-8",
            )
        manifest = _generated_package_manifest(
            source_manifest, variant.name, custom_files
        )
        (package_dir / "package.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        staged[variant.name] = (package_name, version, package_dir)

    findings = _marker_findings(packages_root, "staged npm package")
    if findings:
        raise FlavorCompositionError(findings)
    return staged


def _tree_file_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def _verify_tarball(
    tarball: Path, package_dir: Path, package_name: str, version: str
) -> None:
    with tarfile.open(tarball, mode="r:gz") as archive:
        members = {
            member.name: member for member in archive.getmembers() if member.isfile()
        }
        manifest_member = members.get("package/package.json")
        if manifest_member is None:
            raise ValueError(f"npm tarball has no package.json: {tarball}")
        manifest_stream = archive.extractfile(manifest_member)
        if manifest_stream is None:
            raise ValueError(f"could not read package.json from npm tarball: {tarball}")
        packed_manifest = json.loads(manifest_stream.read().decode("utf-8"))
        if packed_manifest.get("name") != package_name:
            raise ValueError(
                f"npm tarball name mismatch: expected {package_name!r}, "
                f"got {packed_manifest.get('name')!r}"
            )
        if packed_manifest.get("version") != version:
            raise ValueError(
                f"npm tarball version mismatch: expected {version!r}, "
                f"got {packed_manifest.get('version')!r}"
            )

        packed_skills: dict[str, bytes] = {}
        for name, member in members.items():
            if not name.startswith("package/skills/"):
                continue
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError(f"could not read {name} from npm tarball: {tarball}")
            relative = name.removeprefix("package/skills/")
            data = stream.read()
            if MARKER_BYTES in data:
                raise ValueError(f"flavor marker leaked into npm tarball: {name}")
            packed_skills[relative] = data

        staged_skills = _tree_file_bytes(package_dir / "skills")
        if packed_skills != staged_skills:
            raise ValueError(
                f"npm tarball skill tree differs from staged package: {tarball}"
            )
        forbidden = [
            name
            for name in members
            if name.startswith("package/skill-flavors/")
            or name.startswith("package/tests/")
            or name.startswith("package/scripts/")
        ]
        if forbidden:
            raise ValueError(
                f"npm tarball contains source-only paths: {', '.join(forbidden[:5])}"
            )


def _pack_staged_packages(
    staged: dict[str, tuple[str, str, Path]], npm_root: Path
) -> tuple[PackedPackage, ...]:
    npm_executable = shutil.which("npm")
    if npm_executable is None:
        raise ValueError("npm is required to build skill package tarballs")
    npm_root.mkdir(parents=True, exist_ok=False)

    packed: list[PackedPackage] = []
    for variant in sorted(staged, key=lambda name: (name != DEFAULT_VARIANT, name)):
        package_name, version, package_dir = staged[variant]
        completed = subprocess.run(
            [
                npm_executable,
                "pack",
                str(package_dir),
                "--json",
                "--pack-destination",
                str(npm_root),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise ValueError(f"npm pack failed for {package_name}: {detail}")
        try:
            result = json.loads(completed.stdout)
            if not isinstance(result, list) or len(result) != 1:
                raise ValueError("expected one npm pack result")
            filename = result[0]["filename"]
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"could not parse npm pack output for {package_name}: "
                f"{completed.stdout.strip()}"
            ) from exc
        tarball = npm_root / filename
        if not tarball.is_file():
            raise ValueError(f"npm pack did not create its reported tarball: {tarball}")
        _verify_tarball(tarball, package_dir, package_name, version)
        packed.append(
            PackedPackage(
                variant=variant,
                package_name=package_name,
                version=version,
                package_dir=package_dir,
                tarball=tarball,
            )
        )
    return tuple(packed)


def pack_all_variants(
    repo_root: Path = REPO_ROOT,
) -> tuple[PackedPackage, ...]:
    """Build, stage, pack, and verify every convention-discovered variant."""

    repo_root = repo_root.resolve()
    variants = create_all_variants(repo_root)
    build_root = _prepare_build_root(repo_root)
    temporary_root = Path(
        tempfile.mkdtemp(prefix=".skill-flavor-pack-", dir=build_root)
    )
    temporary_skills = temporary_root / "skills"
    temporary_packages = temporary_root / "packages"
    temporary_npm = temporary_root / "npm"
    try:
        # The phase boundary is intentional: complete files exist and are
        # validated before any package directory is staged.
        _materialize_variants(variants, temporary_skills)
        findings = _marker_findings(temporary_skills, "built skill tree")
        if findings:
            raise FlavorCompositionError(findings)
        staged = _stage_packages(
            repo_root, variants, temporary_skills, temporary_packages
        )
        packed = _pack_staged_packages(staged, temporary_npm)

        final_skills = build_root / "skills"
        final_packages = build_root / "packages"
        final_npm = build_root / "npm"
        _replace_generated_directories(
            (
                (temporary_skills, final_skills),
                (temporary_packages, final_packages),
                (temporary_npm, final_npm),
            )
        )
        return tuple(
            PackedPackage(
                variant=item.variant,
                package_name=item.package_name,
                version=item.version,
                package_dir=final_packages / item.variant,
                tarball=final_npm / item.tarball.name,
            )
            for item in packed
        )
    finally:
        shutil.rmtree(temporary_root, ignore_errors=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="canonical skills repository root",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser(
        "validate",
        help="validate all discovered flavors, or one explicit flavor",
    )
    validate.add_argument("flavor_root", type=Path, nargs="?", default=None)
    build_default = subparsers.add_parser(
        "build-default", help="write the complete default skill tree"
    )
    build_default.add_argument(
        "output_dir",
        type=Path,
        nargs="?",
        default=None,
        help="defaults to build/skills/default under the repository root",
    )
    build = subparsers.add_parser(
        "build",
        help="build all discovered trees, or the default and one explicit flavor",
    )
    build.add_argument("flavor_root", type=Path, nargs="?", default=None)
    build.add_argument(
        "output_root",
        type=Path,
        nargs="?",
        default=None,
        help="defaults to build/skills under the repository root",
    )
    subparsers.add_parser(
        "pack",
        help="build all trees, stage every npm package, and create verified tarballs",
    )
    subparsers.add_parser(
        "guard-root-pack",
        help="reject unsafe direct npm packaging from the repository root",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            if args.flavor_root is None:
                variants = create_all_variants(args.repo_root)
                summaries = [
                    f"{variant.name}: {len(variant.plan.skills)} skills, "
                    f"{len(variant.plan.files)} files, "
                    f"{variant.plan.replacement_count} replacements"
                    for variant in variants
                ]
                print("OK - " + "; ".join(summaries) + ".")
            else:
                default_plan = create_default_plan(args.repo_root)
                flavor_plan = create_composition_plan(
                    args.repo_root, args.flavor_root
                )
                print(
                    f"OK - default: {len(default_plan.skills)} skills, "
                    f"{len(default_plan.files)} files; "
                    f"{args.flavor_root.name}: {len(flavor_plan.skills)} skills, "
                    f"{len(flavor_plan.files)} files, "
                    f"{flavor_plan.replacement_count} replacements."
                )
        elif args.command == "build-default":
            plan = create_default_plan(args.repo_root)
            output_dir = args.output_dir or args.repo_root / "build/skills/default"
            materialize_composition(plan, output_dir)
            print(
                f"Built default: {len(plan.files)} files for {len(plan.skills)} "
                f"skills at {output_dir.resolve()}."
            )
        elif args.command == "build" and args.flavor_root is None:
            variants, output_root = build_all_skill_trees(args.repo_root)
            print(
                f"Built {len(variants)} complete marker-free skill trees at "
                f"{output_root.resolve()}: "
                + ", ".join(
                    f"{variant.name} ({len(variant.plan.skills)} skills)"
                    for variant in variants
                )
                + "."
            )
        elif args.command == "build":
            default_plan = create_default_plan(args.repo_root)
            flavor_plan = create_composition_plan(args.repo_root, args.flavor_root)
            output_root = (args.output_root or args.repo_root / "build/skills").resolve()
            default_output = output_root / "default"
            flavor_output = output_root / args.flavor_root.name
            # Preflight both destinations before writing either artifact.
            _validate_output_directory(default_output)
            _validate_output_directory(flavor_output)
            materialize_composition(default_plan, default_output)
            materialize_composition(flavor_plan, flavor_output)
            print(
                f"Built default ({len(default_plan.files)} files) and "
                f"{args.flavor_root.name} ({len(flavor_plan.files)} files, "
                f"{flavor_plan.replacement_count} replacements) at {output_root}."
            )
        elif args.command == "pack":
            packages = pack_all_variants(args.repo_root)
            print(f"Built and verified {len(packages)} npm packages:")
            for package in packages:
                print(
                    f"  {package.package_name}@{package.version} "
                    f"[{package.variant}] -> {package.tarball}"
                )
        else:
            print(
                "ERROR: direct npm pack/publish from the repository root would "
                "ship source flavor markers. Run 'npm run skills:pack' and use "
                "the generated package under build/packages/.",
                file=sys.stderr,
            )
            return 1
        return 0
    except FlavorCompositionError as exc:
        for finding in exc.findings:
            print(f"ERROR: {finding}", file=sys.stderr)
        return 1
    except (OSError, ValueError, tarfile.TarError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
