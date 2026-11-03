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


ARTIFACT_GUIDES = ("artifacts-guide.md", "owl-patterns-guide.md", "shacl-patterns-guide.md",
                   "mapping-yarrrml-guide.md", "summary-context-guide.md")
ID_TERMS = re.compile(
    r"\b(entityId|folderId|choiceSetId|connectionId|referenceEntityId|referenceFieldId|referenceFolderKey)\b")
GUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
# lowercase only (a table header "Action" is fine); `function:` is the YARRRML join key, not the concept
OUT_OF_SCOPE = re.compile(r"(?i:business[- ]rules?)\b|\bfunctions?\b(?!:)|\bactions?\b")
RETIRED = re.compile(r"\b(OFN-00[3678]|SHC-00[15]|MAP-00[1378]|FNO-\d+|BRU-\d+)\b|summary\.txt|manifest\.json")


def test_artifact_guides_exist():
    for g in ARTIFACT_GUIDES:
        assert (MODELER_DIR / "references" / g).is_file(), g


def test_example_files_are_folded_into_their_guides():
    assert sorted(p.name for p in (MODELER_DIR / "references").glob("*-example.md")) == []


def test_artifact_guides_never_carry_ids():
    hits = [h for g in ARTIFACT_GUIDES for h in unnegated_lines(MODELER_DIR / "references" / g, ID_TERMS)]
    assert hits == []


def test_no_guid_literals_in_skills():
    assert [str(p) for p in guidance_files() if GUID.search(read(p))] == []


def test_out_of_scope_only_negated():
    assert [h for p in guidance_files() for h in unnegated_lines(p, OUT_OF_SCOPE)] == []


def test_no_retired_rules_or_formats():
    assert [str(p) for p in guidance_files() if RETIRED.search(read(p))] == []


def test_artifacts_guide_matches_zip_contract():
    t = read(MODELER_DIR / "references/artifacts-guide.md")
    for row in ("| `{name}.ofn` | `schema` | `text/owl-functional` | exactly 1 |",
                "| `{name}-constraints[-{area}].ttl` | `constraints` | `text/turtle` | 1+ |",
                "| `{name}-mapping.yarrrml.yml` | `mapping` | `application/yaml` | exactly 1 |",
                "| `{name}-summary.json` | `summary` | `application/json` | 0..1 |",
                "| `{name}-context.json` | `context` | `application/json` | 0..1 |",
                "operations/", "## Do not"):
        assert row in t, row


def test_mapping_guide_maps_choice_sets_by_name():
    t = read(MODELER_DIR / "references/mapping-yarrrml-guide.md")
    assert "## Choice-set columns" in t and "xsd:string" in t and "CHOICE_SET_MULTIPLE" in t
    assert "table:" in t and "access: datafabric" in t
    assert "equal(str1=$(customer), str2=$(Id))" in t and "## Joins" in t


def test_shacl_guide_lists_value_names():
    t = read(MODELER_DIR / "references/shacl-patterns-guide.md")
    assert "## Value list from a choice set" in t and re.search(r'sh:in\s*\(\s*"Open"', t)


def test_owl_guide_has_inverse_properties_section():
    assert "## Inverse properties" in read(MODELER_DIR / "references/owl-patterns-guide.md")


DF_WRITE = re.compile(r"uip\s+df\s+(entities|choice-sets|choice-set-values)\s+(create|update)\b")


def test_every_df_write_is_local():
    lines = [l for p in guidance_files() for l in read(p).splitlines() if DF_WRITE.search(l)]
    assert lines and all("--local" in l for l in lines), lines


def test_no_tenant_folder_scope_in_skills():
    pat = re.compile(r"--folder-key|(?i:dev[ _-]?folder)")
    assert [h for p in guidance_files() for h in unnegated_lines(p, pat)] == []


def test_entity_guide_type_table_and_sources():
    t = read(MODELER_DIR / "references/entity-guide.md")
    for v in ("`DATETIME_WITH_TZ`", "`RELATIONSHIP`", "`CHOICE_SET_SINGLE`", "`CHOICE_SET_MULTIPLE`",
              "decimalPrecision: 0", "referenceEntityName", "referenceFieldName", "choiceSetName", "connectionName"):
        assert v in t
    for src in ("supplied", "described", "generated"):
        assert f"`{src}`" in t
    assert "`existing`" not in t
    assert "uipath-platform" in t and "](../../uipath-platform" not in t


def test_entity_guide_authors_locally_in_order():
    t = read(MODELER_DIR / "references/entity-guide.md")
    assert re.search(r"uip df choice-sets create [^\n]*--local", t)
    assert re.search(r"uip df choice-set-values create <C> <VALUE> --local", t)
    assert "externalFields" in t and "sourceConnectionName" in t and "uip login" in t
    assert re.search(r"connector source[^\n]*uip login|uip login[^\n]*connector source", t)
    assert re.search(r"uip df entities create [^\n]*--local", t)
    assert t.index("uip df entities list --local") < t.index("uip df entities create")
    assert t.index("choice-sets create") < t.index("entities create") < t.index("<FEDERATED_BODY>")
    assert "entity/federated/" in t and "choiceSet/" in t


def test_relationship_guide_forbids_second_field():
    t = read(MODELER_DIR / "references/relationships-guide.md")
    assert "InverseObjectProperties" in t and "XF-017" in t
    assert re.search(r"(?i)never add a second RELATIONSHIP field", t)
    assert re.search(r"(?i)federated[^\n]*plain column", t)
