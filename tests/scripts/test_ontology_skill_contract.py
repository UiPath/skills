#!/usr/bin/env python3
"""Contract guards for the ontology skill (uipath-ontology)."""

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "skills"
SKILL_DIR = SKILLS / "uipath-ontology"
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
    return list(SKILL_DIR.rglob("*.md"))


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
    in_fence = False
    for line in lines[start:]:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        m = None if in_fence else re.match(r"(#+)\s", line)
        if m and len(m.group(1)) <= level:
            break
        out.append(line)
    return "\n".join(out)


def test_section_ignores_headings_inside_code_fences():
    text = "## A\n\n```bash\n# comment\nrun\n```\n\nafter\n\n## B\n\nother"
    body = section(text, "A")
    assert "# comment" in body and "after" in body and "other" not in body


def test_skill_registered_as_preview():
    status = json.loads(read(ROOT / "assets/skill-status.json"))["skills"]
    assert status["uipath-ontology"]["status"] == "preview"


def test_frontmatter_identity_and_redirects():
    m = frontmatter(read(SKILL_DIR / "SKILL.md"))
    assert m["name"] == "uipath-ontology"
    assert m["description"].startswith("UiPath Ontology") and len(m["description"]) <= 1024
    assert "→uipath-solution" in m["description"] and "TRIGGER" not in m["description"]
    assert m["user-invocable"] is True and m["allowed-tools"]
    assert "→uipath-planner" in m["description"] and "→uipath-platform" in m["description"]
    # one skill takes all three inputs
    assert re.search(r"SDD, PDD or design document", m["description"])
    assert "plain-language domain" in m["description"] and "artifact files" in m["description"]
    assert "SDD" in m["when_to_use"]
    # its own claim, so an ontology request with a PDD/SDD is not left to the planner's "always invoke for PDD/SDD"
    assert "Always invoke to build or update an ontology, even from an SDD or PDD." in m["description"]
    assert len(m["description"]) + len(m["when_to_use"]) + 1 <= 1536


def test_codeowners_cover_ontology_paths():
    owners = read(ROOT / "CODEOWNERS")
    for p in ("/skills/uipath-ontology/", "/skill-flavors/studioweb/uipath-ontology/",
              "/tests/tasks/uipath-ontology/",
              "/tests/scripts/test_ontology_skill_contract.py", "/tests/scripts/test_ontology_solution_golden.py"):
        assert re.search(rf"^{re.escape(p)}\s+@", owners, re.M), p


def test_skills_ship_no_code():
    assert not (SKILL_DIR / "scripts").exists()
    assert [p for p in SKILL_DIR.rglob("*") if p.suffix in {".py", ".js", ".mjs", ".sh", ".ps1"}] == []


def test_no_rest_or_sdk_patterns_in_any_guide():
    for path in guidance_files():
        assert FORBIDDEN_REST.search(read(path)) is None, str(path)


def test_markdown_links_stay_inside_the_skill():
    for skill_dir in (SKILL_DIR,):
        for md in skill_dir.rglob("*.md"):
            for link in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", read(md)):
                if re.match(r"[a-z]+:", link):
                    continue
                target = (md.parent / link).resolve()
                assert target.is_relative_to(skill_dir.resolve()), f"{md.name} -> {link}"
                assert target.exists(), f"{md.name} -> {link}"


def test_activation_rows_route_every_input_to_the_one_skill():
    path = ROOT / "tests/tasks/activation/uipath-ontology.jsonl"
    rows = [json.loads(l) for l in read(path).splitlines() if l.strip()]
    assert {r["expected_skill"] for r in rows} == {"uipath-ontology"}
    prompts = [r["prompt"].lower() for r in rows]
    assert any(re.search(r"\bsdd\b|\bpdd\b|design document|specification", p) for p in prompts)
    assert any(re.search(r"\.ofn|\.ttl|yarrrml", p) for p in prompts)
    assert len({r["id"] for r in rows}) == len(rows)


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
        assert (SKILL_DIR / "references" / g).is_file(), g


def test_example_files_are_folded_into_their_guides():
    assert sorted(p.name for p in (SKILL_DIR / "references").glob("*-example.md")) == []


def test_artifact_guides_never_carry_ids():
    hits = [h for g in ARTIFACT_GUIDES for h in unnegated_lines(SKILL_DIR / "references" / g, ID_TERMS)]
    assert hits == []


def test_no_guid_literals_in_skills():
    assert [str(p) for p in guidance_files() if GUID.search(read(p))] == []


def test_out_of_scope_only_negated():
    assert [h for p in guidance_files() for h in unnegated_lines(p, OUT_OF_SCOPE)] == []


def test_no_retired_rules_or_formats():
    assert [str(p) for p in guidance_files() if RETIRED.search(read(p))] == []


def test_artifacts_guide_matches_zip_contract():
    t = read(SKILL_DIR / "references/artifacts-guide.md")
    for row in ("| `{name}.ofn` | `schema` | `text/owl-functional` | exactly 1 |",
                "| `{name}-constraints[-{area}].ttl` | `constraints` | `text/turtle` | 0+ (optional) |",
                "| `{name}-mapping.yarrrml.yml` | `mapping` | `application/yaml` | exactly 1 |",
                "| `{name}-summary.json` | `summary` | `application/json` | 0..1 |",
                "| `{name}-context.json` | `context` | `application/json` | 0..1 |",
                "operations/", "## Do not"):
        assert row in t, row


def test_mapping_guide_maps_choice_sets_by_name():
    t = read(SKILL_DIR / "references/mapping-yarrrml-guide.md")
    assert "## Choice-set columns" in t and "xsd:string" in t and "CHOICE_SET_MULTIPLE" in t
    assert "table:" in t and "access: datafabric" in t
    assert "equal(str1=$(customer), str2=$(Id))" in t and "## Joins" in t


def test_shacl_guide_lists_value_names():
    t = read(SKILL_DIR / "references/shacl-patterns-guide.md")
    assert "## Value list from a choice set" in t and re.search(r'sh:in\s*\(\s*"Open"', t)


def test_owl_guide_has_inverse_properties_section():
    assert "## Inverse properties" in read(SKILL_DIR / "references/owl-patterns-guide.md")


DF_WRITE = re.compile(r"uip\s+df\s+(entities|choice-sets|choice-set-values)\s+(create|update)\b")


def test_every_df_write_is_local():
    lines = [l for p in guidance_files() for l in read(p).splitlines() if DF_WRITE.search(l)]
    assert lines and all("--local" in l for l in lines), lines


def test_no_tenant_folder_scope_in_skills():
    pat = re.compile(r"--folder-key|(?i:dev[ _-]?folder)")
    assert [h for p in guidance_files() for h in unnegated_lines(p, pat)] == []


def test_entity_guide_type_table_and_sources():
    t = read(SKILL_DIR / "references/entity-guide.md")
    for v in ("`DATETIME_WITH_TZ`", "`RELATIONSHIP`", "`CHOICE_SET_SINGLE`", "`CHOICE_SET_MULTIPLE`",
              "decimalPrecision: 0", "referenceEntityName", "referenceFieldName", "choiceSetName", "connectionName"):
        assert v in t
    for src in ("supplied", "described", "generated"):
        assert f"`{src}`" in t
    assert "`existing`" not in t
    assert "uipath-platform" in t and "](../../uipath-platform" not in t


def test_entity_guide_authors_locally_in_order():
    t = read(SKILL_DIR / "references/entity-guide.md")
    assert re.search(r"uip df choice-sets create [^\n]*--local", t)
    assert re.search(r"uip df choice-set-values create <C> <VALUE> --local", t)
    assert "externalFields" in t and "sourceConnectionName" in t and "uip login" in t
    assert re.search(r"connector source[^\n]*uip login|uip login[^\n]*connector source", t)
    assert re.search(r"uip df entities create [^\n]*--local", t)
    assert t.index("uip df entities list --local") < t.index("uip df entities create")
    assert t.index("choice-sets create") < t.index("entities create") < t.index("<FEDERATED_BODY>")
    assert "entity/federated/" in t and "choiceSet/" in t


def test_entity_guide_reserves_order_and_group():
    t = read(SKILL_DIR / "references/entity-guide.md")
    assert re.search(r"`Order` and `Group` are never entity names", t) and "NAME_RESERVED" in t
    lines = [l for p in guidance_files() for l in read(p).splitlines()
             if re.search(r"entities create (Order|Group)\b|referenceEntityName\": \"(Order|Group)\"|table: (Order|Group)\b", l)]
    assert lines == [], lines


def test_relationship_guide_forbids_second_field():
    t = read(SKILL_DIR / "references/relationships-guide.md")
    assert "InverseObjectProperties" in t and "XF-017" in t
    assert re.search(r"(?i)never add a second RELATIONSHIP field", t)
    assert re.search(r"(?i)federated[^\n]*plain column", t)


def test_entity_guide_spells_out_federated_body():
    t = read(SKILL_DIR / "references/entity-guide.md")
    assert '"joins"' in t and "FEDERATED_SOURCES" not in t
    for k in ("source", "relatedSource", "sourceField", "relatedField", "sourceConnectionName", "relatedConnectionName"):
        assert f'"{k}"' in t, k


def fenced_block_starting(text: str, first_line: str) -> str:
    """Content of the first fenced block whose first line starts with `first_line`."""
    for m in re.finditer(r"^```[^\n]*\n(.*?)^```", text, re.M | re.S):
        if m.group(1).startswith(first_line):
            return m.group(1)
    raise AssertionError(f"no fenced block starts with: {first_line}")


MODEL_FIELDS = ("ONTOLOGY_NAME", "ONTOLOGY_IRI", "DISPLAY_NAME", "DESCRIPTION", "WORKDIR", "SOLUTION_DIR",
                  "CLASS_MAP", "ENTITY_DEFINITIONS", "CHOICE_SETS", "RELATIONSHIPS", "FEDERATED_SOURCES",
                  "MAPPING_STATUS", "DOMAIN_MODEL", "ANNOTATIONS")
REPORT_FIELDS = ("SOLUTION_DIR", "PACKAGE_PATH", "ONTOLOGY_NAME", "ENTITIES", "CHOICE_SETS", "CONNECTIONS",
                 "PACKED_FILES", "VALIDATION", "UNRESOLVED_AMBIGUITIES")
# Source: the CLI plan's per-file ids, cross-file XF ids, service ids and error codes. XF-011 is retired
# (MAP-012 replaces it); XF-016/XF-018 don't exist; the folder-scope and suffixed-name rules have no meaning
# for local entities and are not listed.
PER_FILE_RULES = ("OFN-001", "OFN-002", "OFN-004", "OFN-005", "OFN-009", "SHC-002", "SHC-003", "SHC-004",
    "SHC-006", "SHC-007", "SHC-008", "SHC-009", "SHC-010", "SHC-011", "MAP-002", "MAP-004", "MAP-005", "MAP-006",
    "CTX-001", "CTX-002", "CTX-003", "CTX-005", "CTX-006", "CTX-007", "SUM-001", "SUM-002", "SUM-003")
C1_CODES = ("NoParentSolution", "OntologyNotFound", "OntologyNameTaken", "InvalidOntologyName", "EntityNotFound",
    "LocalFlagRequired", "LocalAndFolderConflict", "FolderKeyAndPathConflict",
    "InvalidFolderKey", "InvalidFolderPath",
    "ConfirmationRequired", "InvalidArtifactFileName", "ArtifactTypeUnresolved", "ArtifactTypeNotSupported",
    "ArtifactTypeAlreadyPresent", "ArtifactCheckFailed", "ArtifactNotFound", "ResourceFileMissing",
    "InvalidResourceArchive", "InvalidAttachedFile", "FileAttachNotSupported", "ResourceNotFound", "PackageNotFound",
    "OntologyNotInPackage", "OntologyManifestNotWritten", "ValidationFailed", "ServiceValidationUnavailable",
    "ServiceValidationFailed")
# local authoring codes of the `uip df … --local` commands the skill can meet
DF_LOCAL_CODES = ("CONNECTION_NOT_FOUND", "REFERENCE_TARGET_NOT_FOUND", "CHOICE_SET_NOT_FOUND", "RELATIONSHIP_TARGET_FEDERATED",
    "FEDERATED_UPDATE_NOT_SUPPORTED", "ENTITY_IN_USE", "CHOICE_SET_IN_USE", "CHOICE_SET_NAME_TAKEN", "CHOICE_SET_VALUE_NAME_TAKEN",
    "NAME_RESERVED", "RELATIONSHIP_CYCLE", "ENTITY_NAME_TAKEN", "INVALID_NAME", "INVALID_FEDERATED_SOURCE", "INVALID_JOIN",
    "UNSUPPORTED_SOURCE_COLUMN")
RECOVERY_IDS = PER_FILE_RULES + ("MAP-012",) + tuple(f"XF-{n:03d}" for n in range(1, 16) if n != 11) + \
    ("ZIP-001", "XF-017", "XF-019", "SVC-001", "ENTITY_ID_IGNORED") + C1_CODES + DF_LOCAL_CODES + \
    ("Not logged in", "Ambiguous match", "Missing in the target folder", "InvalidArguments", "BLOCKED_AMBIGUITY")
# Entities are created before the artifacts are written: ont probe < login < init < connection import
# < choice sets / entities create < artifacts check < ont create < validate < pack.
STAGES = ("uip ont --help", "uip login status", "uip solution init",
          "uip solution resources add --source remote --kind Connection", "uip df entities list --local",
          "uip df choice-sets create", "uip df entities create", "uip df entities validate --local",
          "uip ont artifacts check", "uip ont create", "uip ont files add",
          "uip ont validate --local", "uip solution pack", "uip ont files list", "Stop after pack")
# Order tests read only the `## Workflow` section, so Critical Rules may name commands in any order.
wf = lambda: section(read(SKILL_DIR / "SKILL.md"), "Workflow")


def test_skill_stage_order():
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


def test_skill_checks_duplicates_before_create():
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
    t = read(SKILL_DIR / "SKILL.md")
    assert "Stop after pack" in t
    assert not re.search(r"uip solution (publish|deploy)", t)
    assert "uip ont get" not in wf()  # the post-deploy check belongs to uipath-solution


def test_validation_needs_login_and_no_offline_flag():
    assert [str(p) for p in guidance_files() if "--offline" in read(p)] == []  # the option does not exist
    row = next(l for l in errors_guide().splitlines() if "ServiceValidationUnavailable" in l)
    assert "uip login" in row


def test_saved_model_and_report_blocks_have_exact_fields():
    t = read(SKILL_DIR / "SKILL.md")
    h = fenced_block_starting(section(t, "Saved model"), "ONTOLOGY_NAME: exact slug")
    r = fenced_block_starting(section(t, "Report"), "SOLUTION_DIR: absolute path")
    assert tuple(re.findall(r"^([A-Z_]+):", h, re.M)) == MODEL_FIELDS
    assert tuple(re.findall(r"^([A-Z_]+):", r, re.M)) == REPORT_FIELDS
    assert not ID_TERMS.search(h) and not GUID.search(h)
    assert "domains (groups)" in next(l for l in h.splitlines() if l.startswith("ANNOTATIONS:"))


def errors_guide() -> str:
    return section(read(SKILL_DIR / "references/errors-guide.md"), "Recovery table")


def test_recovery_table_lists_every_id():
    sec = errors_guide()
    assert [i for i in RECOVERY_IDS if not re.search(rf"\b{re.escape(i)}\b", sec)] == []


def test_recovery_rows_are_local_fixes():
    sec = errors_guide()
    row = lambda key: next(l for l in sec.splitlines() if key in l)
    assert "uip df entities update" in row("XF-017") and "--local" in row("XF-017")
    assert "uip df choice-set-values create" in row("XF-019") and "--local" in row("XF-019")
    assert "uip df entities delete" in row("FEDERATED_UPDATE_NOT_SUPPORTED") and "uip login" in row("Not logged in")
    assert "uip df entities create <E> --local" in row("EntityNotFound")
    assert "--kind Connection" in row("Ambiguous match")


def test_deploy_rejections_belong_to_the_solution_skill():
    sec = errors_guide()
    assert not re.search(r"^\| `(TypeIncompatible|EntityConflict)`", sec, re.M)
    s = read(SKILL_DIR / "SKILL.md")
    assert "| `XF-013`" not in s.split("## Errors", 1)[0]  # the full table lives in errors-guide.md
    assert "errors-guide.md" in section(s, "Errors")


def test_skill_links_resolve():
    for p in guidance_files():
        for link in re.findall(r"\]\(([^)#]+\.md)", read(p)):
            assert (p.parent / link).is_file(), f"{p}: {link}"


def test_error_table_codes_exist_in_errors_guide():
    guide = errors_guide()
    rows = [l for l in section(read(SKILL_DIR / "SKILL.md"), "Errors").splitlines()
            if l.startswith("| ") and not l.startswith("| Signal")]
    codes = {c for l in rows for c in re.findall(r"`([A-Za-z]+(?:[-_][A-Z0-9]+)+|[A-Z][a-z]+(?:[A-Z][a-z]+)+)`",
                                                 l.split("|")[1])}
    assert codes and [c for c in codes if not re.search(rf"\b{re.escape(c)}\b", guide)] == []


# --- one skill: document mode and the saved model ---------------------------------------------------------

def document_guide() -> str:
    return read(SKILL_DIR / "references/document-guide.md")


def test_document_mode_runs_the_document_guide():
    t = read(SKILL_DIR / "SKILL.md")
    row = next(l for l in t.splitlines() if l.startswith("| Document |"))
    assert "SDD" in row and "document-guide.md" in row
    assert "document-guide.md" in section(t, "Stage 2")
    assert "document-guide.md" in section(t, "Reference Navigation")


def test_document_guide_confirms_three_tables_in_order():
    g = document_guide()
    marks = ("## Read the document", "## Table 1 — Business concepts", "## Table 2 — Properties and relationships",
             "## Table 3 — Labels, descriptions and synonyms")
    pos = [g.index(m) for m in marks]
    assert pos == sorted(pos)
    assert "| Domain |" in section(g, "Table 1") and "XF-009" in section(g, "Table 1")
    assert "model.md" in g and "one table at a time" in g


def test_document_guide_links_the_rules_instead_of_copying_them():
    g = document_guide()
    assert "entity-guide.md#xsd-to-data-fabric-type" in g and "relationships-guide.md#many-to-many" in g
    assert "| User says |" not in g and "Never use `UUID`" not in g  # the type table lives in entity-guide.md only
    assert "sh:minCount" not in g and "sh:maxCount" not in g  # constraints go into schema comments


def test_document_guide_checks_refused_names_at_approval():
    t1 = section(document_guide(), "Table 1")
    for name in ("Order", "Group", "Case", "Class", "New"):
        assert f"`{name}`" in t1 or f'"{name}"' in t1, name


def test_file_field_upgrade_cost_is_told_before_confirmation():
    for t in (section(document_guide(), "Table 2"), section(read(SKILL_DIR / "SKILL.md"), "Stage 2"),
              read(SKILL_DIR / "references/entity-guide.md")):
        assert "FILE" in t and "not applied" in t


def test_saved_model_is_written_resumed_and_kept_current():
    t = read(SKILL_DIR / "SKILL.md")
    sm = section(t, "Saved model")
    assert "<WORKDIR>/input/model.md" in sm and "CONFIRMED_THROUGH" in sm
    for step in ("concepts", "properties", "labels", "model", "built"):
        assert f"`{step}`" in sm, step
    assert "Resume." in sm and "start over" in sm and "Critical Rule 4" in sm and "files add" in sm
    assert "Every change goes into the file first" in sm and "NAME_RESERVED" in sm
    assert "input/model.md" in section(t, "Critical Rules")
    assert "CONFIRMED_THROUGH: model" in section(t, "Stage 2")
    assert "CONFIRMED_THROUGH: built" in section(t, "Stage 9")
    assert "save the change to `model.md`" in section(t, "Stage 4")


def test_planner_hands_ontology_requests_to_the_skill():
    # The planner claims every PDD/SDD; without this redirect "an ontology from this PDD" never reaches the skill.
    fm = frontmatter(read(SKILLS / "uipath-planner/SKILL.md"))
    assert "ontology, even from a PDD/SDD→uipath-ontology" in fm["description"]
    assert "A PDD always routes here, even for one RPA process, but not an ontology." in fm["when_to_use"]
    # the skill listing keeps only the first 1536 chars of description + when_to_use
    assert len(fm["description"]) <= 1024 and len(fm["description"]) + len(fm["when_to_use"]) + 1 <= 1536


def test_review_does_not_wait_for_login():
    t = read(SKILL_DIR / "SKILL.md")
    s1 = section(t, "Stage 1")
    assert "go on to Stage 2" in s1 and "Before Stage 3" in s1
    assert "never blocks Stage 2" in section(t, "Critical Rules")


def test_a_document_can_ask_for_artifacts_only():
    row = next(l for l in read(SKILL_DIR / "SKILL.md").splitlines() if l.startswith("| Artifacts only |"))
    assert "document" in row and "Document mode" in row


def test_update_keeps_the_saved_model_current():
    t = read(SKILL_DIR / "SKILL.md")
    up = section(t, "Updating an existing solution")
    assert "input/model.md" in up and "save each change" in up and "CONFIRMED_THROUGH: built" in up
    assert "Update, not resume." in section(t, "Saved model")


def test_a_missing_ont_command_stops_the_build():
    t = read(SKILL_DIR / "SKILL.md")
    rule = next(l for l in section(t, "Critical Rules").splitlines() if l.startswith("17."))
    assert "unknown command 'ont'" in rule and "Never pack" in rule
    assert "`unknown command 'ont'`" in section(t, "Errors")
    assert "`unknown command 'ont'`" in errors_guide()


def test_document_evals_live_under_the_one_skill():
    tasks = ROOT / "tests/tasks/uipath-ontology"
    for f in ("smoke_sdd_document/smoke_sdd_document.yaml", "e2e_sdd_to_pack/e2e_sdd_to_pack.yaml"):
        y = yaml.safe_load(read(tasks / f))
        triggered = [c["skill_name"] for c in y["success_criteria"] if c["type"] == "skill_triggered"]
        assert triggered == ["uipath-ontology"], f
        assert any(c.get("path") == "maintenance/input/model.md" for c in y["success_criteria"]), f
    assert "Group" in read(tasks / "_sdd_crews/maintenance-sdd.md") and "| File |" in read(tasks / "_sdd_crews/maintenance-sdd.md")


def solution_ontology_section() -> str:
    return read(SOLUTION_DIR_SKILL / "references/scenarios/ontology-solution.md")


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
    assert "InstallError" in sec
    assert "read only while authoring" in sec and "deployment configuration" in sec
    for l in unnegated_lines_of(sec, re.compile(r"UseExisting|MergeConfiguration|RenameExisting|--all")):
        raise AssertionError(l)
    old = read(SOLUTION_DIR_SKILL / "references/pack-and-deploy.md")
    assert "Ontology names are unique per tenant" not in old


def test_pack_and_deploy_links_the_ontology_scenario():
    t = read(SOLUTION_DIR_SKILL / "references/pack-and-deploy.md")
    assert "scenarios/ontology-solution.md" in t


def unnegated_lines_of(text: str, pattern: re.Pattern) -> list[str]:
    return [l for l in text.splitlines() if pattern.search(l) and not NEGATION.search(l)]


def test_solution_federated_connection_activation():
    t = read(SOLUTION_DIR_SKILL / "references/pack-and-deploy.md")
    assert re.search(r"federated[^\n]*NeedsSetupToActivate|NeedsSetupToActivate[^\n]*federated", solution_ontology_section())
    assert re.search(r"--kind Connection[^\n]*--folder-path",
                     read(SOLUTION_DIR_SKILL / "references/develop-solution.md"))
    assert t.count("CNS1072") == 1  # referenced, not duplicated


def test_develop_solution_never_promises_updated_on_rerun():
    t = read(SOLUTION_DIR_SKILL / "references/develop-solution.md")
    assert not re.search(r"(?i)re-?run[^\n]*\bUpdated\b", t)
    entity = next(l for l in t.splitlines() if l.startswith("**Folder-scoped `Entity`"))
    assert "Unchanged" in entity and "Step 11a" in entity
    # the SDK still reports Updated when a new remote import changes resources already in the solution
    status = next(l for l in t.splitlines() if l.startswith("`Status` is `\"Added\"`"))
    for value in ('"Added"', '"Unchanged"', '"Updated"'):
        assert value in status, value


# --- grouping (ont:domain), source-system icons (mapping `system:`), in-place upgrade -------------------

def test_owl_guide_declares_domain_annotation():
    t = section(read(SKILL_DIR / "references/owl-patterns-guide.md"), "Domain annotation")
    assert "Declaration(AnnotationProperty(:domain))" in t
    assert re.search(r'AnnotationAssertion\(:domain :\w+ "[^"]+"\)', t)
    assert "every class" in t


def test_mapping_guide_names_the_source_system_of_connector_sources():
    t = section(read(SKILL_DIR / "references/mapping-yarrrml-guide.md"), "Source system")
    assert "system: <CONNECTOR_KEY>" in t and "uipath-coupa-coupa" in t
    assert "sourceSystems:" in t and "native" in t


def test_skill_models_domains_and_writes_source_systems():
    t = wf()
    s2 = section(t, "Stage 2")
    assert "domain" in s2
    s5 = section(t, "Stage 5")
    assert ":domain" in s5 and "system:" in s5


def test_skill_update_bumps_version_and_hands_off_an_upgrade():
    t = section(read(SKILL_DIR / "SKILL.md"), "Updating an existing solution")
    assert "--version" in t and "deploy upgrade" in t and "in place" in t and "uipath-solution" in t


def test_solution_owns_the_file_field_upgrade_recovery():
    t = section(read(SKILL_DIR / "SKILL.md"), "Updating an existing solution")
    assert "TypeIncompatible" in t and "uipath-solution" in t
    assert not (SKILL_DIR / "references/upgrade-guide.md").exists()
    g = read(SOLUTION_DIR_SKILL / "references/scenarios/local-entity-file-field.md")
    for s_ in ("conflictFixingAction UseExisting", "config link", "--package-version", "--yes", "deploy status"):
        assert s_ in g, s_
    assert "local-entity-file-field.md" in read(SOLUTION_DIR_SKILL / "references/scenarios.md")


def test_shacl_guide_names_every_property_block_and_spares_multi_select():
    t = read(SKILL_DIR / "references/shacl-patterns-guide.md")
    fences = re.findall(r"```turtle\n(.*?)```", t, re.S)
    for block in fences:
        assert block.count("sh:path") == block.count("sh:name"), block[:80]
    assert "CHOICE_SET_MULTIPLE" in section(t, "Every property block carries")


def test_artifacts_only_mode_needs_no_login():
    s = read(SKILL_DIR / "SKILL.md")
    assert "Artifacts-only mode skips the login check" in section(s, "Stage 1")


def test_stage_1_checks_for_uip_ont_before_the_interview():
    s1 = section(read(SKILL_DIR / "SKILL.md"), "Stage 1")
    assert s1.index("uip ont --help") < s1.index("uip login status")
    assert "In every mode" in s1 and "unknown command 'ont'" in s1 and "stop before asking anything" in s1


def test_artifacts_only_reports_what_it_did_not_check():
    t = read(SKILL_DIR / "SKILL.md")
    s5 = section(t, "Stage 5")
    assert "only the per-file check ran" in s5 and "Artifacts-only [Report]" in s5
    rep = section(t, "Report")
    assert "Artifacts-only mode has no solution or package" in rep and "NOT_CHECKED:" in rep


def test_artifacts_only_has_no_solution():
    t = read(SKILL_DIR / "SKILL.md")
    assert "not in Artifacts-only mode" in section(t, "Stage 2")
    assert "Artifacts-only mode has no `SOLUTION_DIR`" in section(t, "Paths")
    assert "no `SOLUTION_DIR` is Artifacts-only: continuing after `model` re-runs Stage 5 only" in section(t, "Saved model")


def test_handoff_warns_about_same_name_entities():
    s9 = section(read(SKILL_DIR / "SKILL.md"), "Stage 9")
    assert "check the target folder for same-name entities before deploying" in s9 and "EntityConflict" in s9
