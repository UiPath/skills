"""Contract tests for the repository-local skill-flavor contributor skill."""

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "manage-skill-flavors"
SKILL_FILE = SKILL_DIR / "SKILL.md"
OPENAI_YAML = SKILL_DIR / "agents" / "openai.yaml"


def _skill_frontmatter():
    lines = SKILL_FILE.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "---", "SKILL.md must start with YAML frontmatter"

    try:
        closing_delimiter = lines.index("---", 1)
    except ValueError as error:
        raise AssertionError("SKILL.md frontmatter must have a closing delimiter") from error

    metadata = yaml.safe_load("\n".join(lines[1:closing_delimiter]))
    assert isinstance(metadata, dict)
    return metadata


def test_skill_frontmatter_has_expected_name_and_description():
    metadata = _skill_frontmatter()

    assert set(metadata) == {"name", "description"}
    assert metadata["name"] == "manage-skill-flavors"

    description = metadata["description"]
    assert isinstance(description, str)
    assert description == description.strip()
    assert 1 <= len(description) <= 1024
    assert "skill flavor" in description.lower()
    assert "<" not in description and ">" not in description


def test_all_relative_markdown_links_resolve_inside_the_skill():
    source = SKILL_FILE.read_text(encoding="utf-8")
    relative_targets = []

    for raw_target in re.findall(r"(?<!!)\[[^]]+\]\(([^)]+)\)", source):
        target = raw_target.strip()
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or target.startswith("#"):
            continue

        linked_path = (SKILL_DIR / unquote(parsed.path)).resolve()
        try:
            linked_path.relative_to(SKILL_DIR.resolve())
        except ValueError as error:
            raise AssertionError(
                f"relative skill link escapes the skill directory: {target}"
            ) from error

        relative_targets.append(target)
        assert linked_path.is_file(), f"relative skill link does not exist: {target}"

    assert relative_targets, "SKILL.md should link to its detailed reference material"


def test_openai_agent_metadata_has_expected_interface_shape():
    document = yaml.safe_load(OPENAI_YAML.read_text(encoding="utf-8"))

    assert isinstance(document, dict)
    assert set(document) == {"interface"}

    interface = document["interface"]
    assert isinstance(interface, dict)
    assert set(interface) == {"display_name", "short_description"}
    assert interface["display_name"] == "Manage Skill Flavors"
    assert interface["short_description"] == (
        "Build and review repository skill flavor packages"
    )
    assert 25 <= len(interface["short_description"]) <= 64
