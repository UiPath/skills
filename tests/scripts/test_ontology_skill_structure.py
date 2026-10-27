#!/usr/bin/env python3
"""Static contract tests for the ontology skills (CLI-driven local-solution flow)."""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "skills"
MODELER_DIR = SKILLS / "uipath-ontology-modeler"
AUTHORING_DIR = SKILLS / "uipath-ontology-authoring"
MODELER = (MODELER_DIR / "SKILL.md").read_text(encoding="utf-8")
AUTHORING = (AUTHORING_DIR / "SKILL.md").read_text(encoding="utf-8")

# Source: the CLI detail page, sections "Design" (rule tables) and "Edge cases and errors"
# (error-code table). To be checked against ~/code/cli/docs/tools/ontologies.md when it exists.
PER_FILE_RULES = (
    "OFN-001", "OFN-002", "OFN-004", "OFN-005", "OFN-009",
    "SHC-002", "SHC-003", "SHC-004", "SHC-006", "SHC-007", "SHC-008", "SHC-009", "SHC-010",
    "MAP-002", "MAP-004", "MAP-005", "MAP-006",
    "CTX-001", "CTX-002", "CTX-003", "CTX-005", "CTX-006", "CTX-007",
    "SUM-001", "SUM-002",
)
CROSS_FILE_RULES = tuple(f"XF-{n:03d}" for n in range(1, 16))
SERVICE_RULES = ("SVC-001", "SVC-002")
ERROR_CODES = (
    "NoParentSolution", "OntologyNotFound", "OntologyNameTaken", "InvalidOntologyName",
    "EntityNotFound", "LocalFlagRequired", "ConfirmationRequired", "InvalidArtifactFileName",
    "ArtifactTypeUnresolved", "ArtifactTypeNotSupported", "FolderNotSupported",
    "ArtifactTypeAlreadyPresent", "ArtifactCheckFailed", "ArtifactNotFound", "ResourceFileMissing",
    "InvalidResourceArchive", "InvalidAttachedFile", "FileAttachNotSupported", "ResourceNotFound",
    "PackageNotFound", "OntologyNotInPackage", "ValidationFailed",
    "ServiceValidationUnavailable", "ServiceValidationFailed",
)
RECOVERY_IDS = PER_FILE_RULES + CROSS_FILE_RULES + SERVICE_RULES + ERROR_CODES

STAGE_COMMANDS = (
    "uip ont artifacts check", "uip df entities create", "uip ont create", "uip ont files add",
    "uip ont validate --local", "uip df entities validate --local", "uip solution pack",
    "uip ont files list",
)
REFERENCE_GUIDES = ("entity-format-guide.md", "relationships-guide.md", "summary-context-guide.md")
# Things the old flow taught that the CLI replaces.
BANNED_IN_MODELER = (
    ("business-rules", re.compile(r"business-rules")),
    ("summary.txt", re.compile(r"summary\.txt")),
    ("manifest.json", re.compile(r"manifest\.json")),
    ("uip solution resources ... --kind Ontology",
     re.compile(r"uip\s+solution\s+resources\b[^\n]*--kind\s+Ontology")),
    ("files add under uip solution", re.compile(r"uip\s+solution\s+resources\s+files\s+add|uip\s+solution\s+files\s+add")),
)


def contract_block(text: str) -> str:
    start = text.index("ONTOLOGY_NAME: exact slug")
    return text[start:text.index("```", start)]


def frontmatter(text: str) -> str:
    assert text.startswith("---\n")
    return text.split("\n---\n", 1)[0]


class OntologySkillContractTests(unittest.TestCase):
    def test_management_skill_is_removed_and_unreferenced(self):
        self.assertFalse((SKILLS / "uipath-ontologies").exists())
        for path in [*SKILLS.rglob("*.md"), ROOT / "skills.sh.json", ROOT / "assets" / "skill-status.json",
                     ROOT / "CODEOWNERS", ROOT / "tests" / "tasks" / "activation" / "activation.yaml"]:
            self.assertNotRegex(path.read_text(encoding="utf-8"), r"uipath-ontologies\b", str(path))

    def test_skills_are_registered_in_development(self):
        status = json.loads((ROOT / "assets" / "skill-status.json").read_text(encoding="utf-8"))
        skills = status.get("skills", status)
        for name in ("uipath-ontology-modeler", "uipath-ontology-authoring"):
            self.assertIn(name, skills)

    def test_skills_have_no_scripts_folder(self):
        for skill_dir in (MODELER_DIR, AUTHORING_DIR):
            self.assertFalse((skill_dir / "scripts").exists(), str(skill_dir))
        for text in (MODELER, AUTHORING):
            self.assertNotIn("scripts/ontology_", text)
            self.assertNotIn("<SKILL_DIR>/scripts", text)

    def test_modeler_names_the_cli_stage_commands_in_order(self):
        for command in STAGE_COMMANDS:
            self.assertIn(command, MODELER)
        order = ("uip ont artifacts check", "uip df entities create", "uip ont create", "uip ont files add",
                 "uip ont validate --local", "uip solution pack", "uip ont files list")
        positions = [MODELER.index(command) for command in order]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("uip df entities validate --local", MODELER)

    def test_modeler_hands_deploy_to_solution_skill_and_confirms(self):
        self.assertIn("uipath-solution", MODELER)
        self.assertIn("uip ont get", MODELER)
        self.assertLess(MODELER.index("uip solution pack"), MODELER.index("uip ont get"))
        self.assertIn("Stop after pack", MODELER)

    def test_modeler_never_uses_offline(self):
        self.assertNotIn("--offline", MODELER)
        self.assertNotIn("--offline", AUTHORING)

    def test_modeler_drops_the_old_flow(self):
        for label, pattern in BANNED_IN_MODELER:
            self.assertIsNone(pattern.search(MODELER), label)

    def test_reference_guides_exist(self):
        for guide in REFERENCE_GUIDES:
            self.assertTrue((MODELER_DIR / "references" / guide).is_file(), guide)

    def test_markdown_links_resolve(self):
        for skill_dir, text in ((MODELER_DIR, MODELER), (AUTHORING_DIR, AUTHORING)):
            for link in re.findall(r"\]\(([^)#]+\.md)\)", text):
                self.assertTrue((skill_dir / link).is_file(), link)
        for ref in (MODELER_DIR / "references").glob("*.md"):
            for link in re.findall(r"\]\(([^)#]+\.md)\)", ref.read_text(encoding="utf-8")):
                self.assertTrue((ref.parent / link).is_file(), f"{ref.name} -> {link}")

    def test_recovery_table_lists_every_rule_id_and_error_code(self):
        self.assertRegex(MODELER, r"(?im)^#+ .*recovery")
        section = re.split(r"(?im)^#+ .*recovery.*$", MODELER, maxsplit=1)[1]
        section = re.split(r"(?m)^#{1,2} ", section, maxsplit=1)[0]
        missing = [i for i in RECOVERY_IDS if not re.search(rf"\b{re.escape(i)}\b", section)]
        self.assertEqual(missing, [], f"recovery table is missing: {missing}")

    def test_handoff_contract_is_identical_in_both_skills(self):
        self.assertEqual(contract_block(MODELER), contract_block(AUTHORING))
        for field in ("SOLUTION_DIR", "PACKAGE_PATH", "UNRESOLVED_AMBIGUITIES", "ENTITY_SOURCE",
                      "ENTITY_DEFINITIONS", "RELATIONSHIPS", "DISPLAY_NAME", "DESCRIPTION",
                      "PACKED_FILES", "VALIDATION"):
            self.assertIn(field, MODELER)
            self.assertIn(field, AUTHORING)

    def test_handoff_drops_the_script_era_fields(self):
        dropped = ("ONTOLOGY_KEY", "ENTITY_KEYS", "ARTIFACT_INVENTORY", "GATES", "ONTOLOGY_ARCHIVE",
                   "PREFLIGHT_HANDOFF_JSON", "OPERATIONS")
        for text in (MODELER, AUTHORING):
            blocks = [contract_block(text)]
            ret = text.find("SOLUTION_DIR: absolute path\n")
            if ret != -1:
                blocks.append(text[ret:text.index("```", ret)])
            for block in blocks:
                for field in dropped:
                    self.assertNotRegex(block, rf"\b{field}\b", field)

    def test_authoring_delegates_and_stops_after_pack(self):
        for marker in ("Phase 3 — Define business concepts", "Phase 4 — Define properties and relationships",
                       "Phase 5 — Define labels, descriptions, and synonyms", "Step 2 — Build the local solution"):
            self.assertIn(marker, AUTHORING)
        self.assertLess(AUTHORING.index("Phase 3 —"), AUTHORING.index("Step 2 — Build"))
        self.assertIn("If `uipath-ontology-modeler` is not available", AUTHORING)
        self.assertIn("Stop after pack", AUTHORING)
        self.assertNotIn("../uipath-ontology-modeler", AUTHORING)
        self.assertNotRegex(AUTHORING, r"\buip\s+(ont|df)\b[^\n]*(create|--local)")

    def test_routing_descriptions_do_not_overlap(self):
        modeler, authoring = frontmatter(MODELER), frontmatter(AUTHORING)
        self.assertIn("→uipath-ontology-authoring", modeler)
        self.assertIn("→uipath-ontology-modeler", authoring)
        self.assertIn("existing ontology files→uipath-ontology-modeler", authoring)
        for text in (modeler, authoring):
            self.assertIn("→uipath-solution", text)
            self.assertTrue(re.search(r'description: "UiPath Ontology', text))


class ActivationFixtureTests(unittest.TestCase):
    def test_activation_rows_route_files_to_the_modeler(self):
        rows = {}
        for skill in ("uipath-ontology-modeler", "uipath-ontology-authoring"):
            path = ROOT / "tests" / "tasks" / "activation" / f"{skill}.jsonl"
            rows[skill] = [json.loads(line)["prompt"].lower() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertTrue(all(re.search(r"sdd|pdd|design document|specification", p) for p in rows["uipath-ontology-authoring"]))
        self.assertFalse(any(re.search(r"\bsdd\b|\bpdd\b", p) for p in rows["uipath-ontology-modeler"]))


if __name__ == "__main__":
    unittest.main()
