"""Every fixture this suite stages is a readable BusinessRules project.

No test touched the two fixtures that nothing else reads, and that is exactly
where the defect was: `graph_extend_brownfield`'s `entry-points.json` carried
its `input` and `output` as JSON *strings* rather than objects, so both shared
contract parsers raised on it and `uip rules validate` reported
`RULES_ENTRY_POINTS_STALE` — in a file the task hands the agent as the starting
point (MST-18847).

These are the checks that need no tenant, so they run in this suite's own job. The CLI's own
verdict on each fixture needs `uip`, so it lives in `validate_fixtures.py` beside this file and is
run by hand; no CI job calls it yet.
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rules_check as rc  # noqa: E402
from fixture_inventory import (  # noqa: E402
    DELIBERATELY_BROKEN,
    SUITE,
    projects as _projects,
    rel as _rel,
)

PROJECTS = _projects()
IDS = [_rel(p) for p in PROJECTS]


def test_the_suite_ships_fixtures_to_check():
    # Guards the glob: a layout change that stops finding projects would make every
    # parametrised test below vacuous and this file would pass while checking nothing.
    assert len(PROJECTS) >= 5, f"found only {IDS}"


def test_every_deliberately_broken_fixture_exists():
    # An entry left behind after its fixture is deleted or repaired silently exempts nothing,
    # but it does lie about the suite. A typo in one exempts a fixture that is not broken.
    missing = sorted(name for name in DELIBERATELY_BROKEN if not (SUITE / name).is_dir())
    assert not missing, f"DELIBERATELY_BROKEN names fixtures that are not there: {missing}"


@pytest.mark.parametrize("project", PROJECTS, ids=IDS)
def test_the_manifest_declares_a_named_business_rules_project(project):
    manifest = json.loads((project / "project.uiproj").read_text(encoding="utf-8"))
    assert manifest.get("ProjectType") == "BusinessRules"
    # `find_project` matches on Name, so a fixture whose Name is not its folder's is a fixture
    # the graders cannot find — which reads as "the agent never made the project".
    assert manifest.get("Name") == project.name


@pytest.mark.parametrize("project", PROJECTS, ids=IDS)
def test_the_project_holds_exactly_one_parseable_dmn(project):
    dmn_files = list(project.glob("*.dmn"))
    assert len(dmn_files) == 1, f"{[f.name for f in dmn_files]}"
    root = ET.fromstring(dmn_files[0].read_text(encoding="utf-8"))
    # Any DMN MODEL namespace here; the version is asserted below, because one fixture is
    # deliberately DMN 1.3 and moving it to 1.5 is the repair the task grades.
    assert root.tag.endswith("}definitions"), root.tag
    assert "/spec/DMN/" in root.tag and "/MODEL/" in root.tag, root.tag


@pytest.mark.parametrize(
    "project", [p for p in PROJECTS if _rel(p) not in DELIBERATELY_BROKEN],
    ids=[i for i in IDS if i not in DELIBERATELY_BROKEN])
def test_a_sound_fixture_is_dmn_1_5(project):
    root = ET.fromstring(next(project.glob("*.dmn")).read_text(encoding="utf-8"))
    assert root.tag == f"{{{rc.DMN_NS}}}definitions"


@pytest.mark.parametrize("project", PROJECTS, ids=IDS)
def test_the_entry_points_are_objects_the_shared_parsers_can_read(project):
    # The defect: `"input": "{\\"type\\": \\"object\\", ...}"` parses as JSON and reads as a
    # string, so `(entry.get("input") or {}).get("properties")` raises AttributeError in every
    # grader that touches the contract. Regenerate with `uip rules refresh`, never by hand.
    document = json.loads((project / "entry-points.json").read_text(encoding="utf-8"))
    entries = document["entryPoints"]
    assert isinstance(entries, list) and entries
    for entry in entries:
        assert entry.get("filePath"), entry
        assert entry.get("uniqueId"), entry
        for side in ("input", "output"):
            schema = entry.get(side)
            assert isinstance(schema, dict), (
                f"{_rel(project)} entry {entry.get('filePath')!r} carries {side} as "
                f"{type(schema).__name__}, not an object")
            # Exercised through the parser the graders use, not only by shape.
            assert isinstance(rc.output_properties(schema), dict)


@pytest.mark.parametrize(
    "project", [p for p in PROJECTS if _rel(p) not in DELIBERATELY_BROKEN],
    ids=[i for i in IDS if i not in DELIBERATELY_BROKEN])
def test_the_authoring_surface_matches_what_the_fixture_holds(project):
    # A fixture is what an agent copies. One staged on the wrong surface teaches the wrong
    # surface, and the suite graded that nowhere until `check_authoring_surface`.
    #
    # Sound fixtures only: repair_invalid's is DMN 1.3, so its `extensionElements` are not in the
    # 1.5 namespace this reads. Moving it there is part of the repair the task grades.
    dmn_file = next(project.glob("*.dmn"))
    rc.check_authoring_surface(dmn_file, ET.fromstring(dmn_file.read_text(encoding="utf-8")))


@pytest.mark.parametrize("project", PROJECTS, ids=IDS)
def test_the_bindings_file_parses(project):
    assert isinstance(json.loads((project / "bindings_v2.json").read_text(encoding="utf-8")), dict)


@pytest.mark.parametrize(
    "project", [p for p in PROJECTS if _rel(p) not in DELIBERATELY_BROKEN],
    ids=[i for i in IDS if i not in DELIBERATELY_BROKEN])
def test_a_sound_fixture_passes_the_profile_the_graders_load(project, monkeypatch, tmp_path):
    # `load_graph` is the gate every grader goes through. A fixture it refuses fails its task
    # before the agent's edit is looked at.
    monkeypatch.chdir(tmp_path)
    rc.load_graph(project)


@pytest.mark.parametrize(
    "project", sorted(SUITE / name for name in DELIBERATELY_BROKEN),
    ids=sorted(DELIBERATELY_BROKEN))
def test_a_broken_fixture_is_still_a_readable_project(project):
    # Broken for the agent to repair, not broken as a file: the task stages it, so it still has
    # to parse. A fixture that does not is a task that cannot start.
    assert (project / "project.uiproj").is_file()
    ET.fromstring(next(project.glob("*.dmn")).read_text(encoding="utf-8"))
