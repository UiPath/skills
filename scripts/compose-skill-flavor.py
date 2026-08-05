#!/usr/bin/env python3
"""Compose a complete skill tree from canonical files and sparse flavor blocks.

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

Build both complete trees from the repository root::

    python3 scripts/compose-skill-flavor.py validate skill-flavors/studioweb
    python3 scripts/compose-skill-flavor.py build skill-flavors/studioweb

The build command writes ``build/skills/default`` and
``build/skills/studioweb`` by default. Marker boundary comments are source
syntax and are removed from every built Markdown file. Each artifact directory
is itself a complete skills tree (for example,
``build/skills/default/uipath-example/SKILL.md``); packaging may later place
that tree under a package-level ``skills/`` directory.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST_FILENAME = "skills.allowlist"
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKER_TOKEN = "<!-- skill-flavor:"
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
        "validate", help="validate the default and custom flavor contracts"
    )
    validate.add_argument("flavor_root", type=Path)
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
        "build", help="write complete default and custom flavor trees"
    )
    build.add_argument("flavor_root", type=Path)
    build.add_argument(
        "output_root",
        type=Path,
        nargs="?",
        default=None,
        help="defaults to build/skills under the repository root",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            default_plan = create_default_plan(args.repo_root)
            flavor_plan = create_composition_plan(args.repo_root, args.flavor_root)
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
        else:
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
        return 0
    except FlavorCompositionError as exc:
        for finding in exc.findings:
            print(f"ERROR: {finding}", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
