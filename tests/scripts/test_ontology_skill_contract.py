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


def test_entity_guide_spells_out_federated_body():
    t = read(MODELER_DIR / "references/entity-guide.md")
    assert '"joins"' in t and "FEDERATED_SOURCES" not in t
    for k in ("source", "relatedSource", "sourceField", "relatedField", "sourceConnectionName", "relatedConnectionName"):
        assert f'"{k}"' in t, k


def fenced_block_starting(text: str, first_line: str) -> str:
    """Content of the first fenced block whose first line starts with `first_line`."""
    for m in re.finditer(r"^```[^\n]*\n(.*?)^```", text, re.M | re.S):
        if m.group(1).startswith(first_line):
            return m.group(1)
    raise AssertionError(f"no fenced block starts with: {first_line}")


HANDOFF_FIELDS = ("ONTOLOGY_NAME", "ONTOLOGY_IRI", "DISPLAY_NAME", "DESCRIPTION", "WORKDIR", "SOLUTION_DIR",
                  "CLASS_MAP", "ENTITY_DEFINITIONS", "CHOICE_SETS", "RELATIONSHIPS", "FEDERATED_SOURCES",
                  "MAPPING_STATUS", "DOMAIN_MODEL", "ANNOTATIONS")
RETURN_FIELDS = ("SOLUTION_DIR", "PACKAGE_PATH", "ONTOLOGY_NAME", "ENTITIES", "CHOICE_SETS", "CONNECTIONS",
                 "PACKED_FILES", "VALIDATION", "UNRESOLVED_AMBIGUITIES")
# Source: the CLI plan's per-file ids, cross-file XF ids, service ids and error codes. XF-011 is retired
# (MAP-012 replaces it); XF-016/XF-018 don't exist; the folder-scope and suffixed-name rules have no meaning
# for local entities and are not listed.
PER_FILE_RULES = ("OFN-001", "OFN-002", "OFN-004", "OFN-005", "OFN-009", "SHC-002", "SHC-003", "SHC-004",
    "SHC-006", "SHC-007", "SHC-008", "SHC-009", "SHC-010", "MAP-002", "MAP-004", "MAP-005", "MAP-006",
    "CTX-001", "CTX-002", "CTX-003", "CTX-005", "CTX-006", "CTX-007", "SUM-001", "SUM-002")
C1_CODES = ("NoParentSolution", "OntologyNotFound", "OntologyNameTaken", "InvalidOntologyName", "EntityNotFound",
    "LocalFlagRequired", "LocalAndFolderKeyConflict", "LocalAndPackageConflict", "InvalidFolderKey",
    "ConfirmationRequired", "InvalidArtifactFileName", "ArtifactTypeUnresolved", "ArtifactTypeNotSupported",
    "ArtifactTypeAlreadyPresent", "ArtifactCheckFailed", "ArtifactNotFound", "ResourceFileMissing",
    "InvalidResourceArchive", "InvalidAttachedFile", "FileAttachNotSupported", "ResourceNotFound", "PackageNotFound",
    "OntologyNotInPackage", "OntologyManifestNotWritten", "ValidationFailed", "ServiceValidationUnavailable",
    "ServiceValidationFailed")
# local authoring codes of the `uip df … --local` commands the modeler can meet
DF_LOCAL_CODES = ("CONNECTION_NOT_FOUND", "REFERENCE_TARGET_NOT_FOUND", "CHOICE_SET_NOT_FOUND", "RELATIONSHIP_TARGET_FEDERATED",
    "FEDERATED_UPDATE_NOT_SUPPORTED", "ENTITY_IN_USE", "CHOICE_SET_IN_USE", "CHOICE_SET_NAME_TAKEN", "CHOICE_SET_VALUE_NAME_TAKEN")
RECOVERY_IDS = PER_FILE_RULES + ("MAP-012",) + tuple(f"XF-{n:03d}" for n in range(1, 16) if n != 11) + \
    ("ZIP-001", "XF-017", "XF-019", "SVC-001", "ENTITY_ID_IGNORED") + C1_CODES + DF_LOCAL_CODES + \
    ("Not logged in", "Ambiguous match", "EntityConflict", "Missing in the target folder",
     "a rename onto a name another ontology holds", "BLOCKED_AMBIGUITY")
# Entities are created before the artifacts are written: login < init < connection import
# < choice sets / entities create < artifacts check < ont create < validate < pack.
STAGES = ("uip login status", "uip solution init",
          "uip solution resources add --source remote --kind Connection", "uip df entities list --local",
          "uip df choice-sets create", "uip df entities create", "uip df entities validate --local",
          "uip ont artifacts check", "uip ont create", "uip ont files add",
          "uip ont validate --local", "uip solution pack", "uip ont files list", "Stop after pack")
# Order tests read only the `## Workflow` section, so Critical Rules may name commands in any order.
wf = lambda: section(read(MODELER_DIR / "SKILL.md"), "Workflow")


def test_modeler_stage_order():
    t = wf(); pos = [t.index(s) for s in STAGES]
    assert pos == sorted(pos)


def test_artifacts_follow_created_entities():
    t = wf()
    assert t.index("<WORKDIR>/input/entities/<Entity>.json") < t.index("uip solution init")  # definitions in Stage 2
    assert t.index("<FEDERATED_BODY>") < t.index("uip ont artifacts check") < t.index("uip ont create")
    s3 = t[t.index("Init the solution and import connections"):t.index("uip solution init")]
    assert "Artifacts-only mode skips Stages 3–4" in s3
    s5 = t[t.index("uip df entities validate --local"):t.index("uip ont create")]
    assert "created entity and field names exactly" in s5 and "Artifacts-only mode stops here" in s5


def test_modeler_checks_duplicates_before_create():
    t = wf()
    assert t.index("uip df choice-sets list --local") < t.index("uip df choice-sets create")
    assert t.index("uip df entities list --local") < t.index("uip df entities create")


def test_federated_entities_follow_their_connection():
    t = wf()
    assert t.index("--kind Connection") < t.index("<FEDERATED_BODY>")
    assert t.index("uip df entities create <E> --local") < t.index("<FEDERATED_BODY>")


def test_only_remote_import_is_a_folder_scoped_connection():
    lines = [l for p in guidance_files() for l in read(p).splitlines() if "--source remote" in l]
    assert lines and all("--kind Connection" in l and "--folder-path" in l for l in lines), lines


def test_no_entity_import_or_refresh():
    pat = re.compile(r"resources\s+(refresh|edit)\b|--kind\s+(Entity|ChoiceSet)\b")
    assert [h for p in guidance_files() for h in unnegated_lines(p, pat)] == []


def test_entity_change_is_a_local_edit():
    t = wf()
    assert "uip df entities update <E> --local" in t
    assert t.index("uip ont validate --local") < t.rindex("uip df entities update <E> --local")  # the fix loop sits in Validate


def test_no_retired_rule_ids():
    assert [str(p) for p in guidance_files() if re.search(r"\bXF-(01[168]|02[01])\b", read(p))] == []


def test_stop_after_pack_and_no_lifecycle_commands():
    t = read(MODELER_DIR / "SKILL.md")
    assert "Stop after pack" in t
    assert not re.search(r"uip solution (publish|deploy)", t)
    assert "uip ont get" not in wf()  # the post-deploy check belongs to uipath-solution


def test_validation_needs_login_and_no_offline_flag():
    assert [str(p) for p in guidance_files() if "--offline" in read(p)] == []  # the option does not exist
    sec = section(read(MODELER_DIR / "SKILL.md"), "Recovery table")
    assert "uip login" in next(l for l in sec.splitlines() if "ServiceValidationUnavailable" in l and "validation needs" in l)


def test_handoff_and_return_blocks_have_exact_fields():
    t = read(MODELER_DIR / "SKILL.md")
    h = fenced_block_starting(t, "ONTOLOGY_NAME: exact slug"); r = fenced_block_starting(t, "SOLUTION_DIR: absolute path")
    assert tuple(re.findall(r"^([A-Z_]+):", h, re.M)) == HANDOFF_FIELDS
    assert tuple(re.findall(r"^([A-Z_]+):", r, re.M)) == RETURN_FIELDS
    assert not ID_TERMS.search(h) and not GUID.search(h)


def test_recovery_table_lists_every_id():
    sec = section(read(MODELER_DIR / "SKILL.md"), "Recovery table")
    assert [i for i in RECOVERY_IDS if not re.search(rf"\b{re.escape(i)}\b", sec)] == []


def test_recovery_rows_are_local_fixes():
    sec = section(read(MODELER_DIR / "SKILL.md"), "Recovery table")
    row = lambda key: next(l for l in sec.splitlines() if key in l)
    assert "uip df entities update" in row("XF-017") and "--local" in row("XF-017")
    assert "uip df choice-set-values create" in row("XF-019") and "--local" in row("XF-019")
    assert "uip df entities delete" in row("FEDERATED_UPDATE_NOT_SUPPORTED") and "uip login" in row("Not logged in")
    assert "connector source" in row("Not logged in")
    assert "uip df entities create <E> --local" in row("EntityNotFound")
    assert "--kind Connection" in row("Ambiguous match")
    assert "redeploy" in row("Missing in the target folder")
    assert "another name" in row("a rename onto a name another ontology holds") and "deployment configuration" in row("a rename onto a name another ontology holds")


def test_skill_links_resolve():
    for p in guidance_files():
        for link in re.findall(r"\]\(([^)#]+\.md)", read(p)):
            assert (p.parent / link).is_file(), f"{p}: {link}"


def test_handoff_and_return_blocks_identical_in_both_skills():
    m, a = read(MODELER_DIR / "SKILL.md"), read(AUTHORING_DIR / "SKILL.md")
    for first in ("ONTOLOGY_NAME: exact slug", "SOLUTION_DIR: absolute path"):
        assert fenced_block_starting(m, first) == fenced_block_starting(a, first)


def test_authoring_phases_then_delegation():
    t = read(AUTHORING_DIR / "SKILL.md")
    marks = ("Step 1 — Collect", "Phase 3 — Define business concepts", "Phase 4 — Define properties and relationships",
             "Phase 5 — Define labels, descriptions, and synonyms", "Step 2 — Build the solution")
    pos = [t.index(x) for x in marks]
    assert pos == sorted(pos)
    assert "If `uipath-ontology-modeler` is not available" in t and "Stop after pack" in t


def test_authoring_runs_no_cli_writes_and_reads_no_sibling_files():
    t = read(AUTHORING_DIR / "SKILL.md")
    assert not re.search(r"uip\s+(df|ont)\s+\S+\s+(create|update|add)", t)
    assert not re.search(r"uip solution (init|pack|publish|deploy)", t)
    assert "../uipath-ontology-modeler" not in t
    assert "SOLUTION_DIR" in section(t, "Step 1")


def test_authoring_phase_4_covers_df_types_choice_sets_and_connections():
    sec = section(read(AUTHORING_DIR / "SKILL.md"), "Phase 4")
    for term in ("Data Fabric type", "choice set", "relationshipField", "connectionName", "federated"):
        assert term in sec, term


def test_authoring_has_no_stale_claims():
    t = read(AUTHORING_DIR / "SKILL.md")
    for stale in ("SVC-002", "XF-011", "--offline", "not supported", "in the tenant", "in the deployment folder",
                  "UseExisting", "RenameExisting", "MergeConfiguration"):
        assert stale not in t, stale
    assert "unique per folder" in t and "Replace" in t and "RenameInSolution" in t
    assert not ID_TERMS.search(t) and not GUID.search(t)


def solution_ontology_section() -> str:
    return section(read(SOLUTION_DIR_SKILL / "references/pack-and-deploy.md"), "Solutions that carry an ontology")


def test_solution_ontology_post_deploy_check_and_install_errors():
    sec = solution_ontology_section()
    for s in ("local resources", "uip ont get", "uip df entities list", "read-only",
              "EntityConflict", "Missing in the target folder", "redeploy"):
        assert s in sec, s
    for line in sec.splitlines():
        if "--folder-key" in line:
            assert re.search(r"uip (ont get|df entities list)", line), line
    assert not re.search(r"(?i)dev[ _-]?folder", sec)


def test_solution_ontology_conflict_is_replace_or_rename():
    sec = solution_ontology_section()
    assert "unique per folder" in sec and "per tenant" not in sec
    assert "same resource key" in sec and "upgrade" in sec
    assert "allowedActions" in sec and "Replace" in sec and "RenameInSolution" in sec
    assert "upgraded in place" not in sec
    assert re.search(r"uip solution deploy config set <config\.json> <Ontology> conflictFixingAction Replace", sec)
    assert re.search(r"uip solution deploy config set <config\.json> <Ontology> conflictFixingAction RenameInSolution", sec)
    assert re.search(r"uip solution deploy config set <config\.json> <Ontology> name <NewName>", sec)
    assert "InstallError" in sec and "read only while authoring" not in sec
    for l in unnegated_lines_of(sec, re.compile(r"UseExisting|MergeConfiguration|RenameExisting|--all")):
        raise AssertionError(l)
    old = read(SOLUTION_DIR_SKILL / "references/pack-and-deploy.md")
    assert "Ontology names are unique per tenant" not in old


def unnegated_lines_of(text: str, pattern: re.Pattern) -> list[str]:
    return [l for l in text.splitlines() if pattern.search(l) and not NEGATION.search(l)]


def test_solution_federated_connection_activation():
    t = read(SOLUTION_DIR_SKILL / "references/pack-and-deploy.md")
    assert re.search(r"federated[^\n]*NeedsSetupToActivate|NeedsSetupToActivate[^\n]*federated", t)
    assert re.search(r"--kind Connection[^\n]*--folder-path",
                     read(SOLUTION_DIR_SKILL / "references/develop-solution.md"))
    assert t.count("CNS1072") == 1  # referenced, not duplicated


def test_develop_solution_never_promises_updated_on_rerun():
    t = read(SOLUTION_DIR_SKILL / "references/develop-solution.md")
    assert not re.search(r"(?i)re-?run[^\n]*\bUpdated\b", t)
    entity = next(l for l in t.splitlines() if l.startswith("**Folder-scoped `Entity`"))
    assert "Unchanged" in entity and "Step 11a" in entity
