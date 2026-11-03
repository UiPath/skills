#!/usr/bin/env python3
"""Contract guards for the ontology skills (modeler and authoring)."""

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "skills"
MODELER_DIR = SKILLS / "uipath-ontology-modeler"
AUTHORING_DIR = SKILLS / "uipath-ontology-authoring"
SOLUTION_DIR_SKILL = SKILLS / "uipath-solution"

NEGATION = re.compile(r"\b(never|not|no|don't|do not|without|instead of|refuse|reject|stop)\b", re.I)
NEGATED_HEADING = re.compile(r"do not|don't|never|avoid|anti-pattern", re.I)
FORBIDDEN_REST = re.compile(
    r"ontology_/api|datafabric_/api/ontology|OntologyService|bulk-upload|upsertArtifact|uploadArtifacts")


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def frontmatter(text: str) -> dict:
    assert text.startswith("---\n"), "missing leading frontmatter block"
    return yaml.safe_load(text.split("\n---\n", 1)[0][4:])


def body(text: str) -> str:
    assert text.startswith("---\n"), "missing leading frontmatter block"
    return text.split("\n---\n", 1)[1]


def guidance_files() -> list[Path]:
    return [*MODELER_DIR.rglob("*.md"), *AUTHORING_DIR.rglob("*.md")]


def unnegated_lines(path: Path, pattern: re.Pattern) -> list[str]:
    """Lines matching pattern that are not negated on the line or by a 'Do not' heading."""
    hits = []
    negated_section = False
    for number, line in enumerate(read(path).splitlines(), 1):
        if line.startswith("#"):
            negated_section = bool(NEGATED_HEADING.search(line))
        if pattern.search(line) and not negated_section and not NEGATION.search(line):
            hits.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")
    return hits


def section(text: str, heading: str) -> str:
    """Body from the first heading containing `heading` to the next heading of the same or higher level."""
    lines = text.splitlines()
    start = level = None
    for i, line in enumerate(lines):
        m = re.match(r"(#+)\s", line)
        if m and heading in line:
            start, level = i + 1, len(m.group(1))
            break
    assert start is not None, f"heading not found: {heading}"
    out = []
    for line in lines[start:]:
        m = re.match(r"(#+)\s", line)
        if m and len(m.group(1)) <= level:
            break
        out.append(line)
    return "\n".join(out)


def test_skills_registered_in_development():
    status = json.loads(read(ROOT / "assets/skill-status.json"))["skills"]
    for name in ("uipath-ontology-modeler", "uipath-ontology-authoring"):
        assert status[name]["status"] == "in-development"


def test_frontmatter_identity_and_redirects():
    m = frontmatter(read(MODELER_DIR / "SKILL.md"))
    a = frontmatter(read(AUTHORING_DIR / "SKILL.md"))
    assert m["name"] == "uipath-ontology-modeler" and a["name"] == "uipath-ontology-authoring"
    for fm in (m, a):
        assert fm["description"].startswith("UiPath Ontology") and len(fm["description"]) <= 1024
        assert "→uipath-solution" in fm["description"] and "TRIGGER" not in fm["description"]
        assert fm["user-invocable"] is True and fm["allowed-tools"]
    assert "→uipath-ontology-authoring" in m["description"]
    assert "→uipath-ontology-modeler" in a["description"] and "→uipath-planner" in a["description"]
    assert "→uipath-platform" in m["description"]


def test_codeowners_cover_ontology_paths():
    owners = read(ROOT / "CODEOWNERS")
    for p in ("/skills/uipath-ontology-modeler/", "/skills/uipath-ontology-authoring/",
              "/skill-flavors/studioweb/uipath-ontology-modeler/", "/skill-flavors/studioweb/uipath-ontology-authoring/",
              "/tests/tasks/uipath-ontology-modeler/", "/tests/tasks/uipath-ontology-authoring/",
              "/tests/scripts/test_ontology_skill_contract.py", "/tests/scripts/test_ontology_solution_golden.py"):
        assert re.search(rf"^{re.escape(p)}\s+@", owners, re.M), p


def test_skills_ship_no_code():
    for d in (MODELER_DIR, AUTHORING_DIR):
        assert not (d / "scripts").exists()
        assert [p for p in d.rglob("*") if p.suffix in {".py", ".js", ".mjs", ".sh", ".ps1"}] == []


def test_no_rest_or_sdk_patterns_in_any_guide():
    for path in guidance_files():
        assert FORBIDDEN_REST.search(read(path)) is None, str(path)


def test_markdown_links_stay_inside_the_skill():
    for skill_dir in (MODELER_DIR, AUTHORING_DIR):
        for md in skill_dir.rglob("*.md"):
            for link in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", read(md)):
                if re.match(r"[a-z]+:", link):
                    continue
                target = (md.parent / link).resolve()
                assert target.is_relative_to(skill_dir.resolve()), f"{md.name} -> {link}"
                assert target.exists(), f"{md.name} -> {link}"


def test_activation_rows_route_files_to_the_modeler():
    rows = {}
    for skill in ("uipath-ontology-modeler", "uipath-ontology-authoring"):
        path = ROOT / "tests/tasks/activation" / f"{skill}.jsonl"
        rows[skill] = [json.loads(l)["prompt"].lower() for l in read(path).splitlines() if l.strip()]
    assert all(re.search(r"sdd|pdd|design document|specification", p) for p in rows["uipath-ontology-authoring"])
    assert not any(re.search(r"\bsdd\b|\bpdd\b", p) for p in rows["uipath-ontology-modeler"])
