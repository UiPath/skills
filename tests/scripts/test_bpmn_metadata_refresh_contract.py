"""Guard the BPMN source-to-derived metadata refresh contract."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = ROOT / "skills" / "uipath-maestro-bpmn"
SKILL = SKILL_ROOT / "SKILL.md"
METADATA_GUIDE = (
    SKILL_ROOT / "references" / "shared" / "local-metadata-regeneration-guide.md"
)
PROJECT_LAYOUT = SKILL_ROOT / "references" / "shared" / "project-layout.md"
ACTIVITY_GUIDE = (
    SKILL_ROOT / "references" / "integration-service-activity-authoring-guide.md"
)
SHIP = SKILL_ROOT / "references" / "operate" / "references" / "ship.md"

REFRESH = "uip maestro bpmn refresh <project-path> --output json"
VALIDATE = "uip maestro bpmn validate <file.bpmn> --output json"
PACK = "uip maestro bpmn pack <project-path> <OutputDir> --output json"
GENERATED = (
    "entry-points.json",
    "bindings_v2.json",
    "operate.json",
    "package-descriptor.json",
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _prose(text: str) -> str:
    return " ".join(text.split())


def _commands(text: str) -> str:
    return re.sub(r"\\\s*\n\s*", "", text)


def test_skill_orders_validate_before_refresh_and_scopes_it_to_packages() -> None:
    text = _text(SKILL)
    commands = _commands(text)

    assert "Work the five steps" in text
    assert commands.index(VALIDATE) < commands.index(REFRESH)
    section = text.split(
        "5. **Refresh derived metadata when package-ready output is required.**",
        maxsplit=1,
    )[1].split("## Operate and diagnose", maxsplit=1)[0]
    prose = _prose(section)
    assert all(name in section for name in GENERATED)
    assert "offline and provider-neutral" in prose
    assert "does not log in" in prose
    assert "does not expose" in prose
    assert "never repair the four generated JSON files by hand" in prose


def test_metadata_guide_makes_refresh_the_atomic_source_boundary() -> None:
    text = _text(METADATA_GUIDE)
    commands = _commands(text)
    prose = _prose(text)

    assert REFRESH in commands
    assert commands.index("Run local validation") < commands.index(REFRESH)
    assert commands.index(REFRESH) < commands.index(PACK)
    assert all(name in text for name in GENERATED)
    assert "authoritative local" in prose
    assert "offline and provider-neutral" in prose
    assert "atomically regenerates" in prose
    assert "atomic write contract leaves the prior four-file set unchanged" in prose
    assert "deduplicates activities" in prose
    assert "exactly one project-root `.bpmn` file" in prose
    assert "one or more root processes" in prose
    assert "at least one root manual start event" in prose
    assert "exactly one valid GUID `uipath:entryPointId`" in prose
    assert "one `entry-points.json` entry for each such start event" in prose


def test_lifecycle_guides_delegate_generation_to_refresh_not_pack() -> None:
    layout = _text(PROJECT_LAYOUT)
    activity = _text(ACTIVITY_GUIDE)
    ship = _text(SHIP)
    layout_commands = _commands(layout)
    ship_commands = _commands(ship)
    layout_prose = _prose(layout)
    activity_prose = _prose(activity)
    ship_prose = _prose(ship)

    assert REFRESH in layout_commands
    assert "source-to-derived boundary" in layout_prose
    assert "does not discover or import tenant resources" in layout_prose
    assert layout_commands.index(REFRESH) < layout_commands.index(
        "uip maestro bpmn pack <project-path> <OutputDir> --output json"
    )

    assert "the BPMN `refresh` command" in activity
    assert all(name in activity for name in GENERATED)
    assert "never hand-create or edit them" in activity_prose

    assert REFRESH in ship_commands
    assert ship_commands.index(REFRESH) < ship_commands.index(PACK)
    assert "Pack should consume the refreshed files" in ship_prose
