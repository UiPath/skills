"""Regression tests for the Copilot Cowork export pipeline.

The exporter intentionally uses only the Python standard library, so these
tests load the hyphenated script directly instead of relying on it being an
installed package.
"""

from __future__ import annotations

import importlib.util
import io
import json
import posixpath
import re
import shutil
import struct
import subprocess
import sys
import uuid
import zipfile
import zlib
from collections import Counter
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "export-cowork.py"
MANIFEST_SCHEMA = (
    "https://developer.microsoft.com/json-schemas/teams/v1.28/"
    "MicrosoftTeams.schema.json"
)
REQUIRED_SECTIONS = (
    "When Not to Use",
    "Safety and Guardrails",
    "Failure Handling",
)
MAX_COMPANION_FILES = 20
MAX_COMPANION_FILE_BYTES = 5 * 1024 * 1024
MAX_COMPANION_TOTAL_BYTES = 10 * 1024 * 1024
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9_. !-]+$")
KEBAB_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_LINK = re.compile(
    r"!?\[[^\]]*\]\(\s*(?:<(?P<angle>[^>]+)>|(?P<plain>[^\s)]+))",
    re.MULTILINE,
)
REFERENCE_LINK = re.compile(
    r"^\s*\[(?!\^)[^\]]+\]:\s*(?:<([^>]+)>|(\S+))", re.MULTILINE
)


def _load_exporter():
    spec = importlib.util.spec_from_file_location("export_cowork", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # dataclasses and similar stdlib helpers expect the module to be registered
    # while its top-level code executes.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


export_cowork = _load_exporter()


def test_cowork_is_published_as_a_separate_skill_flavor():
    package = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
    assert "cowork" not in package["files"]
    assert package["scripts"]["skills:pack"] == (
        "node scripts/pack-skill-packages.mjs pack"
    )
    assert package["scripts"]["cowork:build"] == (
        "node scripts/pack-skill-packages.mjs cowork-export"
    )
    assert (REPO_ROOT / "skill-flavors" / "cowork").is_dir()

    workflow = (REPO_ROOT / ".github" / "workflows" / "publish.yml").read_text(
        encoding="utf-8"
    )
    assert "  publish-cowork-dev:" in workflow
    assert "  publish-cowork-preview:" in workflow
    assert workflow.count("vars.ENABLE_COWORK_SKILL_FLAVOR_PUBLISH == 'true'") == 2

    reusable = (
        REPO_ROOT / ".github" / "workflows" / "publish-skill-flavor.yml"
    ).read_text(encoding="utf-8")
    assert "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065" in reusable
    assert "run: npm run skills:pack" in reusable

    # Default-package jobs stay transport-neutral; only the explicit Cowork
    # flavor callers build and publish its derived upload artifacts.
    publish_dev = workflow.split("  publish-dev:", maxsplit=1)[1].split(
        "\n  ", maxsplit=1
    )[0]
    publish_npmjs = workflow.split("  publish-npmjs:", maxsplit=1)[1].split(
        "\n  ", maxsplit=1
    )[0]
    assert "cowork:build" not in publish_dev
    assert "setup-python" not in publish_dev
    assert "cowork:build" not in publish_npmjs
    assert "setup-python" not in publish_npmjs


def test_prerelease_report_preserves_exact_package_version(tmp_path):
    repo = _write_fixture_repo(tmp_path / "repo")
    package_path = repo / "package.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))
    package["version"] = "1.2.3-preview.42"
    package_path.write_text(json.dumps(package), encoding="utf-8")

    artifacts = export_cowork.build_export(repo)
    report = json.loads(artifacts["report.json"])
    assert report["source_package_version"] == "1.2.3-preview.42"
    assert report["source_version"] == "1.2.42"

    plugin = json.loads(
        _zip_files(artifacts["plugins/uipath-skills-cowork.zip"])["manifest.json"]
    )
    assert plugin["version"] == "1.2.42"

    package["version"] = "1.2.3-preview.43"
    package_path.write_text(json.dumps(package), encoding="utf-8")
    next_preview = export_cowork.build_export(repo)
    next_plugin = json.loads(
        _zip_files(next_preview["plugins/uipath-skills-cowork.zip"])["manifest.json"]
    )
    assert next_plugin["id"] == plugin["id"]
    assert next_plugin["version"] == "1.2.43"

    package["version"] = "1.2.3"
    package_path.write_text(json.dumps(package), encoding="utf-8")
    stable = export_cowork.build_export(repo)
    stable_plugin = json.loads(
        _zip_files(stable["plugins/uipath-skills-cowork.zip"])["manifest.json"]
    )
    assert stable_plugin["id"] != plugin["id"]
    assert stable_plugin["version"] == "1.2.3"


def _zip_files(payload: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        assert archive.testzip() is None
        files: dict[str, bytes] = {}
        for info in archive.infolist():
            if info.is_dir():
                continue
            assert info.filename not in files, f"duplicate ZIP member: {info.filename}"
            assert not info.flag_bits & 0x1, f"encrypted ZIP member: {info.filename}"
            # Reject Unix symlinks: Cowork expects ordinary companion files.
            assert (info.external_attr >> 16) & 0o170000 != 0o120000
            files[info.filename] = archive.read(info)
        return files


def _assert_safe_archive_path(path: str) -> None:
    assert path
    assert "\\" not in path
    assert "\x00" not in path
    assert not path.startswith("/")
    assert not re.match(r"^[A-Za-z]:", path)

    parts = PurePosixPath(path).parts
    assert parts
    assert str(PurePosixPath(*parts)) == path
    for part in parts:
        assert part not in {"", ".", ".."}
        assert not part.startswith("."), f"hidden archive path: {path}"
        assert SAFE_COMPONENT.fullmatch(part), (
            f"unsafe characters in archive path: {path}"
        )
        assert part.split(".", 1)[0].upper() not in WINDOWS_RESERVED_NAMES


def _markdown_targets(text: str):
    for match in MARKDOWN_LINK.finditer(text):
        yield match.group("angle") or match.group("plain")
    for match in REFERENCE_LINK.finditer(text):
        yield match.group(1) or match.group(2)


def _is_external_target(target: str) -> bool:
    if target.startswith("//"):
        return True
    parsed = urlsplit(target)
    return bool(parsed.scheme) or bool(parsed.netloc)


def _assert_local_markdown_links_resolve(files: dict[str, bytes]) -> None:
    names = set(files)
    for markdown_path, payload in files.items():
        if not markdown_path.lower().endswith(".md"):
            continue
        text = payload.decode("utf-8")
        for raw_target in _markdown_targets(_prose_without_code(text)):
            target = raw_target.strip()
            if not target or target.startswith("#") or _is_external_target(target):
                continue
            path_part = unquote(urlsplit(target).path)
            if not path_part:
                continue
            assert not path_part.startswith("/"), (
                f"absolute local link in {markdown_path}: {raw_target}"
            )
            resolved = posixpath.normpath(
                posixpath.join(posixpath.dirname(markdown_path), path_part)
            )
            assert resolved != ".." and not resolved.startswith("../"), (
                f"link escapes skill archive in {markdown_path}: {raw_target}"
            )
            assert resolved in names, (
                f"unresolved link in {markdown_path}: {raw_target} -> {resolved}"
            )


def _prose_without_code(text: str) -> str:
    # Scanner rewrites must not mutate examples that users need to copy. This
    # helper removes those examples before checking the remaining prose.
    without_fences = re.sub(
        r"(?ms)^[ \t]*(```+|~~~+)[^\n]*\n.*?^[ \t]*\1[ \t]*$",
        "",
        text,
    )
    return re.sub(r"`+[^`\n]*`+", "", without_fences)


def _assert_frontmatter_and_sections(skill_name: str, payload: bytes) -> str:
    text = payload.decode("utf-8")
    fields, body = export_cowork.parse_frontmatter(text)
    assert fields["name"] == skill_name
    assert KEBAB_NAME.fullmatch(fields["name"])
    assert isinstance(fields["description"], str)
    assert 1 <= len(fields["description"]) <= 1024
    assert body.strip()
    for section in REQUIRED_SECTIONS:
        assert len(re.findall(rf"(?m)^## {re.escape(section)}\s*$", body)) == 1
    assert not re.search(
        r"(?i)\b(?:prompt[ -]injection|jailbreak)\b",
        _prose_without_code(text),
    )
    return text


def _assert_skill_tree(skill_name: str, files: dict[str, bytes]) -> str:
    assert "SKILL.md" in files
    for path in files:
        _assert_safe_archive_path(path)

    companions = {path: value for path, value in files.items() if path != "SKILL.md"}
    assert len(companions) <= MAX_COMPANION_FILES
    assert all(len(value) <= MAX_COMPANION_FILE_BYTES for value in companions.values())
    assert sum(map(len, companions.values())) <= MAX_COMPANION_TOTAL_BYTES
    _assert_local_markdown_links_resolve(files)
    return _assert_frontmatter_and_sections(skill_name, files["SKILL.md"])


def _plugin_skill_tree(files: dict[str, bytes], folder: str) -> dict[str, bytes]:
    prefix = folder.removeprefix("./").rstrip("/") + "/"
    return {
        path.removeprefix(prefix): payload
        for path, payload in files.items()
        if path.startswith(prefix)
    }


def _png_dimensions(payload: bytes) -> tuple[int, int]:
    assert payload.startswith(b"\x89PNG\r\n\x1a\n")
    assert payload[12:16] == b"IHDR"
    return struct.unpack(">II", payload[16:24])


def _png_rgba_rows(payload: bytes) -> list[list[tuple[int, int, int, int]]]:
    width, height = _png_dimensions(payload)
    compressed: list[bytes] = []
    cursor = 8
    while cursor < len(payload):
        length = struct.unpack(">I", payload[cursor : cursor + 4])[0]
        kind = payload[cursor + 4 : cursor + 8]
        data = payload[cursor + 8 : cursor + 8 + length]
        cursor += 12 + length
        if kind == b"IDAT":
            compressed.append(data)
        if kind == b"IEND":
            break

    raw = zlib.decompress(b"".join(compressed))
    stride = 1 + width * 4
    assert len(raw) == stride * height
    rows: list[list[tuple[int, int, int, int]]] = []
    for y in range(height):
        row = raw[y * stride : (y + 1) * stride]
        assert row[0] == 0, "exporter icons must use the no-filter PNG encoding"
        pixels = [tuple(row[index : index + 4]) for index in range(1, stride, 4)]
        rows.append(pixels)
    return rows


def _write_fixture_repo(root: Path) -> Path:
    skill = root / "skills" / "fixture-skill"
    (skill / "references" / "deep").mkdir(parents=True)
    (skill / "assets").mkdir()
    (skill / ".private").mkdir()

    (root / "package.json").write_text(
        json.dumps(
            {
                "name": "@example/fixture-skills",
                "version": "1.2.3",
                "description": "Fixture skills for exporter tests.",
                "author": {"name": "Fixture Publisher"},
                "homepage": "https://example.test/skills",
            }
        ),
        encoding="utf-8",
    )
    (skill / "SKILL.md").write_text(
        """---
name: fixture-skill
description: "Use when a test needs a representative linked skill."
allowed-tools: Read
---

# Fixture Skill

The prose describes prompt injection and jailbreak behavior that the Cowork
scanner should receive in neutral terminology. Keep `prompt injection` and
`jailbreak` unchanged in inline code.

```text
prompt injection and jailbreak are literal test input here
```

Read the [fixture guide](references/guide.md).

## When Not to Use

SOURCE-WHEN-NOT-CANARY: Do not use this fixture for production work.

## Safety and Guardrails

SOURCE-SAFETY-CANARY: Never perform an external write from this fixture.

## Failure Handling

SOURCE-FAILURE-CANARY: Report the failed fixture step and stop.
""",
        encoding="utf-8",
    )
    (skill / "references" / "guide.md").write_text(
        """# Fixture Guide

GUIDE-CANARY: This linked Markdown must be consolidated for the Cowork export.
Continue to the [nested topic](deep/topic.md) and use the
[JSON payload](../assets/payload.json).
""",
        encoding="utf-8",
    )
    (skill / "references" / "deep" / "topic.md").write_text(
        """# Nested Topic

NESTED-CANARY: Nested linked Markdown must also be consolidated.
Return to the [fixture guide](../guide.md#fixture-guide).
""",
        encoding="utf-8",
    )
    (skill / "references" / "unlinked.md").write_text(
        "UNLINKED-CANARY: unreachable Markdown should not consume a companion slot.\n",
        encoding="utf-8",
    )
    asset = b'{"fixture": true, "format": "preserve-exact-bytes"}\n'
    (skill / "assets" / "payload.json").write_bytes(asset)
    (skill / ".private" / "hidden.txt").write_text("do not export", encoding="utf-8")
    (skill / ".private" / "hidden.md").write_text(
        "HIDDEN-MARKDOWN-CANARY: maintainer-only content must not be bundled.\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture(scope="module")
def repository_export():
    node = shutil.which("node")
    assert node is not None, "Node.js is required to compose the Cowork flavor"
    result = subprocess.run(
        [
            node,
            str(REPO_ROOT / "scripts" / "compose-skill-flavor.mjs"),
            "--repo-root",
            str(REPO_ROOT),
            "build",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    skills_root = REPO_ROOT / "build" / "skills" / "cowork"
    # Keep both complete builds: deterministic ZIP metadata is part of the
    # distribution contract, and the result is shared by all corpus checks.
    first = export_cowork.build_export(REPO_ROOT, None, skills_root=skills_root)
    second = export_cowork.build_export(REPO_ROOT, None, skills_root=skills_root)
    return first, second


def test_parse_frontmatter_handles_block_description():
    fields, body = export_cowork.parse_frontmatter(
        """---
name: example-skill
description: |
  First description line.
  Second description line.
allowed-tools: Read, Bash
---

# Example
"""
    )

    assert fields["name"] == "example-skill"
    assert fields["description"] == "First description line.\nSecond description line."
    assert fields["allowed-tools"] == "Read, Bash"
    assert body.lstrip().startswith("# Example")


def test_rewrite_scanner_terms_changes_only_prose():
    source = """A prompt injection can be paired with a jailbreak.

Keep `prompt injection` and ``jailbreak`` literal here.

```text
prompt injection
jailbreak
```
"""

    rewritten, count = export_cowork.rewrite_scanner_terms(source)

    assert count == 2
    assert not re.search(
        r"(?i)\b(?:prompt injection|jailbreak)\b",
        _prose_without_code(rewritten),
    )
    assert "`prompt injection`" in rewritten
    assert "``jailbreak``" in rewritten
    assert "```text\nprompt injection\njailbreak\n```" in rewritten
    assert export_cowork.rewrite_scanner_terms(rewritten) == (rewritten, 0)


def test_fixture_export_consolidates_markdown_and_preserves_assets(tmp_path):
    repo = _write_fixture_repo(tmp_path / "repo")

    artifacts = export_cowork.build_export(repo, ["fixture-skill"])

    assert "skills/fixture-skill.skill" in artifacts
    assert "report.json" in artifacts
    assert any(
        path.startswith("plugins/") and path.endswith(".zip") for path in artifacts
    )
    assert isinstance(json.loads(artifacts["report.json"]), dict)

    files = _zip_files(artifacts["skills/fixture-skill.skill"])
    exported = _assert_skill_tree("fixture-skill", files)
    all_markdown = "\n".join(
        payload.decode("utf-8")
        for path, payload in files.items()
        if path.lower().endswith(".md")
    )
    assert "## Cowork Reference Bundles" in exported
    assert "GUIDE-CANARY" in all_markdown
    assert "NESTED-CANARY" in all_markdown
    assert "HIDDEN-MARKDOWN-CANARY" not in all_markdown
    assert "references/guide.md" not in files
    assert "references/deep/topic.md" not in files
    assert (
        files["assets/payload.json"]
        == (repo / "skills" / "fixture-skill" / "assets" / "payload.json").read_bytes()
    )
    assert (
        "](../assets/payload.json)" in all_markdown
        or "](assets/payload.json)" in all_markdown
    )
    assert not any(part.startswith(".") for path in files for part in path.split("/"))

    # Explicitly authored guardrails take precedence over generated defaults.
    for canary in (
        "SOURCE-WHEN-NOT-CANARY",
        "SOURCE-SAFETY-CANARY",
        "SOURCE-FAILURE-CANARY",
    ):
        assert exported.count(canary) == 1


def test_export_uses_an_explicit_composed_skills_root(tmp_path):
    repo = _write_fixture_repo(tmp_path / "repo")
    composed = repo / "build" / "skills" / "cowork"
    composed.parent.mkdir(parents=True)
    (repo / "skills").rename(composed)
    skill_md = composed / "fixture-skill" / "SKILL.md"
    skill_md.write_text(
        skill_md.read_text(encoding="utf-8").replace(
            "# Fixture Skill", "# Composed Cowork Fixture"
        ),
        encoding="utf-8",
    )

    artifacts = export_cowork.build_export(repo, skills_root=composed)
    exported = _zip_files(artifacts["skills/fixture-skill.skill"])["SKILL.md"].decode(
        "utf-8"
    )

    assert "# Composed Cowork Fixture" in exported
    assert json.loads(artifacts["report.json"])["source_package_version"] == "1.2.3"


@pytest.mark.parametrize(
    "relative",
    ["SKILL.md", "references/guide.md", "assets/payload.json"],
)
def test_export_rejects_unresolved_flavor_markers(tmp_path, relative):
    repo = _write_fixture_repo(tmp_path / "repo")
    source = repo / "skills" / "fixture-skill" / relative
    source.write_text(
        source.read_text(encoding="utf-8")
        + "\n<!--skill-flavor:host:start-->\nLeaked override.\n"
        + "<!--skill-flavor:host:end-->\n",
        encoding="utf-8",
    )

    with pytest.raises(
        export_cowork.ExportError, match="unresolved skill flavor marker"
    ):
        export_cowork.build_export(repo)


def test_filtered_plugin_uses_a_distinct_manifest_identity(tmp_path):
    repo = _write_fixture_repo(tmp_path / "repo")
    full = export_cowork.build_export(repo, None)
    filtered = export_cowork.build_export(repo, ["fixture-skill"])

    def manifest_id(artifacts: dict[str, bytes]) -> str:
        plugin = next(
            payload
            for path, payload in artifacts.items()
            if path.startswith("plugins/") and path.endswith(".zip")
        )
        return json.loads(_zip_files(plugin)["manifest.json"])["id"]

    assert manifest_id(full) != manifest_id(filtered)


def test_source_symlink_is_rejected(tmp_path):
    repo = _write_fixture_repo(tmp_path / "repo")
    outside = tmp_path / "outside-secret.txt"
    outside.write_text("must never enter an export", encoding="utf-8")
    link = repo / "skills" / "fixture-skill" / "assets" / "leak.txt"
    try:
        link.symlink_to(outside)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symbolic links are unavailable in this test environment: {exc}")

    with pytest.raises(export_cowork.ExportError, match="symbolic links"):
        export_cowork.build_export(repo, ["fixture-skill"])


def test_linked_skill_directory_is_rejected(tmp_path):
    repo = _write_fixture_repo(tmp_path / "repo")
    outside_skill = tmp_path / "outside-skill"
    outside_skill.mkdir()
    (outside_skill / "SKILL.md").write_text(
        "---\nname: linked-skill\ndescription: External test skill.\n---\n\n# External\n",
        encoding="utf-8",
    )
    link = repo / "skills" / "linked-skill"
    try:
        link.symlink_to(outside_skill, target_is_directory=True)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"directory links are unavailable in this test environment: {exc}")

    with pytest.raises(export_cowork.ExportError, match="skill directory may not"):
        export_cowork.build_export(repo, None)


def test_linked_skills_root_is_rejected(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    outside_skills = tmp_path / "outside-skills"
    _write_fixture_repo(tmp_path / "source")
    (tmp_path / "source" / "skills").rename(outside_skills)
    link = repo / "skills"
    try:
        link.symlink_to(outside_skills, target_is_directory=True)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"directory links are unavailable in this test environment: {exc}")

    with pytest.raises(export_cowork.ExportError, match="skills directory may not"):
        export_cowork.build_export(repo, None)


def test_repository_export_is_deterministic(repository_export):
    first, second = repository_export
    assert first == second


def test_all_repository_skills_are_valid_standalone_archives(repository_export):
    artifacts, _ = repository_export
    expected = {path.name for path in (REPO_ROOT / "skills").iterdir() if path.is_dir()}
    skill_artifacts = {
        PurePosixPath(path).stem: payload
        for path, payload in artifacts.items()
        if path.startswith("skills/") and path.endswith(".skill")
    }

    assert len(expected) == 25, (
        "update Cowork sharding assertions when skills are added"
    )
    assert set(skill_artifacts) == expected
    assert "report.json" in artifacts
    assert isinstance(json.loads(artifacts["report.json"]), dict)
    assert all(
        isinstance(path, str) and isinstance(payload, bytes)
        for path, payload in artifacts.items()
    )

    for skill_name, payload in skill_artifacts.items():
        _assert_skill_tree(skill_name, _zip_files(payload))


def test_cowork_plugin_shards_cover_every_skill_once(repository_export):
    artifacts, _ = repository_export
    expected = {path.name for path in (REPO_ROOT / "skills").iterdir() if path.is_dir()}
    plugin_artifacts = {
        path: payload
        for path, payload in artifacts.items()
        if path.startswith("plugins/") and path.endswith(".zip")
    }
    standalone = {
        PurePosixPath(path).stem: _zip_files(payload)
        for path, payload in artifacts.items()
        if path.startswith("skills/") and path.endswith(".skill")
    }

    assert plugin_artifacts
    covered: list[str] = []
    for artifact_path, payload in sorted(plugin_artifacts.items()):
        _assert_safe_archive_path(artifact_path.removeprefix("plugins/"))
        files = _zip_files(payload)
        for path in files:
            _assert_safe_archive_path(path)
        assert {"manifest.json", "color.png", "outline.png"} <= files.keys()
        assert _png_dimensions(files["color.png"]) == (192, 192)
        assert _png_dimensions(files["outline.png"]) == (32, 32)
        color_rows = _png_rgba_rows(files["color.png"])
        outline_rows = _png_rgba_rows(files["outline.png"])
        assert color_rows[96][96] == (250, 70, 22, 255)
        assert outline_rows[2][16] == (255, 255, 255, 255)
        assert outline_rows[16][16] == (0, 0, 0, 0)

        manifest = json.loads(files["manifest.json"])
        assert set(manifest) == {
            "$schema",
            "manifestVersion",
            "version",
            "id",
            "developer",
            "name",
            "description",
            "icons",
            "accentColor",
            "agentSkills",
        }
        assert manifest["$schema"] == MANIFEST_SCHEMA
        assert manifest["manifestVersion"] == "1.28"
        assert re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"])
        uuid.UUID(manifest["id"])
        assert manifest["icons"] == {"color": "color.png", "outline": "outline.png"}
        assert re.fullmatch(r"#[0-9A-Fa-f]{6}", manifest["accentColor"])
        assert set(manifest["developer"]) == {
            "name",
            "websiteUrl",
            "privacyUrl",
            "termsOfUseUrl",
        }
        assert set(manifest["name"]) == {"short", "full"}
        assert set(manifest["description"]) == {"short", "full"}

        entries = manifest["agentSkills"]
        assert 1 <= len(entries) <= 20
        assert all(set(entry) == {"folder"} for entry in entries)
        folders = [entry["folder"] for entry in entries]
        assert len(folders) == len(set(folders))
        for folder in folders:
            assert len(folder) <= 256
            match = re.fullmatch(r"\./skills/([a-z0-9]+(?:-[a-z0-9]+)*)", folder)
            assert match, f"invalid agentSkills folder: {folder}"
            skill_name = match.group(1)
            tree = _plugin_skill_tree(files, folder)
            _assert_skill_tree(skill_name, tree)
            assert tree == standalone[skill_name]
            covered.append(skill_name)

    assert Counter(covered) == Counter({skill_name: 1 for skill_name in expected})


def test_main_writes_artifacts_and_force_only_replaces_owned_output(tmp_path):
    repo = _write_fixture_repo(tmp_path / "repo")
    output = tmp_path / "cowork"
    argv = [
        "--repo-root",
        str(repo),
        "--output",
        str(output),
        "--skill",
        "fixture-skill",
    ]

    assert export_cowork.main(argv) == 0
    expected = export_cowork.build_export(repo, ["fixture-skill"])
    actual = {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file()
    }
    assert actual == expected

    # Existing output is never replaced implicitly.
    assert export_cowork.main(argv) != 0
    assert export_cowork.main([*argv, "--force"]) == 0

    # Even an exporter-owned directory is rejected after unknown files appear;
    # --force must not delete unrelated content that a user placed there.
    sentinel = output / "sentinel.txt"
    sentinel.write_text("must survive", encoding="utf-8")
    assert export_cowork.main([*argv, "--force"]) != 0
    assert sentinel.read_text(encoding="utf-8") == "must survive"

    # --force is deliberately not a general recursive-delete switch.
    unowned = tmp_path / "unowned"
    unowned.mkdir()
    marker = unowned / "keep.txt"
    marker.write_text("must survive", encoding="utf-8")
    unowned_argv = [*argv]
    unowned_argv[unowned_argv.index(str(output))] = str(unowned)
    assert export_cowork.main([*unowned_argv, "--force"]) != 0
    assert marker.read_text(encoding="utf-8") == "must survive"

    # Output may not contaminate source or target an ancestor of the checkout.
    source_output = repo / "skills" / "generated-cowork"
    source_argv = [*argv]
    source_argv[source_argv.index(str(output))] = str(source_output)
    assert export_cowork.main(source_argv) != 0
    assert not source_output.exists()

    ancestor_argv = [*argv]
    ancestor_argv[ancestor_argv.index(str(output))] = str(repo.parent)
    assert export_cowork.main([*ancestor_argv, "--force"]) != 0


def test_output_symlink_is_rejected_without_touching_its_target(tmp_path):
    repo = _write_fixture_repo(tmp_path / "repo")
    artifacts = export_cowork.build_export(repo)
    target = tmp_path / "real-output"
    export_cowork.write_artifacts(artifacts, target, repo_root=repo)
    before = {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in target.rglob("*")
        if path.is_file()
    }
    link = tmp_path / "linked-output"
    try:
        link.symlink_to(target, target_is_directory=True)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"directory links are unavailable in this test environment: {exc}")

    with pytest.raises(export_cowork.ExportError, match="symbolic link or junction"):
        export_cowork.write_artifacts(
            artifacts,
            link,
            repo_root=repo,
            force=True,
        )
    after = {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in target.rglob("*")
        if path.is_file()
    }
    assert after == before


def test_failed_atomic_install_restores_the_previous_export(tmp_path, monkeypatch):
    repo = _write_fixture_repo(tmp_path / "repo")
    artifacts = export_cowork.build_export(repo)
    output = tmp_path / "cowork"
    export_cowork.write_artifacts(artifacts, output, repo_root=repo)
    before = {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file()
    }
    replacement = dict(artifacts)
    replacement["skills/fixture-skill.skill"] += b"replacement-canary"
    original_rename = Path.rename

    def fail_staging_install(self, target):
        if self.name.startswith(f".{output.name}.cowork-stage-"):
            raise OSError("simulated atomic install failure")
        return original_rename(self, target)

    monkeypatch.setattr(Path, "rename", fail_staging_install)
    with pytest.raises(OSError, match="simulated atomic install failure"):
        export_cowork.write_artifacts(
            replacement,
            output,
            repo_root=repo,
            force=True,
        )

    after = {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file()
    }
    assert after == before
    assert not list(tmp_path.glob(".cowork.cowork-*-*"))


def test_repository_build_directory_is_allowed_for_flavor_packaging(tmp_path):
    repo = _write_fixture_repo(tmp_path / "repo")
    composed = repo / "build" / "skills" / "cowork"
    composed.parent.mkdir(parents=True)
    (repo / "skills").rename(composed)
    output = repo / "build" / "cowork"

    assert (
        export_cowork.main(
            [
                "--repo-root",
                str(repo),
                "--skills-root",
                str(composed),
                "--output",
                str(output),
                "--skill",
                "fixture-skill",
            ]
        )
        == 0
    )
    assert (output / "skills" / "fixture-skill.skill").is_file()
    assert (output / "plugins" / "uipath-skills-cowork.zip").is_file()
    assert (output / "report.json").is_file()

    source_adjacent = repo / "cowork"
    assert (
        export_cowork.main(
            [
                "--repo-root",
                str(repo),
                "--skills-root",
                str(composed),
                "--output",
                str(source_adjacent),
                "--skill",
                "fixture-skill",
            ]
        )
        != 0
    )
    assert not source_adjacent.exists()
