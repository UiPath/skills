#!/usr/bin/env python3
"""Static contract tests for the ontology skills (local-solution flow)."""

import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "skills"
MODELER_DIR = SKILLS / "uipath-ontology-modeler"
MODELER = (MODELER_DIR / "SKILL.md").read_text(encoding="utf-8")
AUTHORING = (SKILLS / "uipath-ontology-authoring" / "SKILL.md").read_text(encoding="utf-8")

# Direct ontology-service deployment paths that the skills must never teach.
FORBIDDEN = (
    re.compile(r"\buip\s+ont\b"),
    re.compile(r"ontology_/api", re.I),
    re.compile(r"datafabric_/api/ontology", re.I),
    re.compile(r"\b(upsertArtifact|uploadArtifacts|OntologyService|bulk-upload)\b"),
    re.compile(r"\buip\s+df\b"),
)
ID_KEYS = re.compile(r"\b(entityId|folderId)\b")


def load_preflight():
    spec = importlib.util.spec_from_file_location("ontology_preflight", MODELER_DIR / "scripts" / "ontology_preflight.py")
    module = importlib.util.module_from_spec(spec)
    # Never leave __pycache__ inside the shipped skill folder.
    previous, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


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

    def test_no_direct_ontology_service_traces(self):
        files = [p for skill in ("uipath-ontology-modeler", "uipath-ontology-authoring")
                 for p in (SKILLS / skill).rglob("*") if p.suffix in {".md", ".py"}]
        for path in files:
            text = path.read_text(encoding="utf-8")
            for pattern in (*FORBIDDEN, ID_KEYS) if path.suffix == ".md" else FORBIDDEN:
                for match in pattern.finditer(text):
                    line = text[: match.start()].count("\n") + 1
                    context = text.splitlines()[line - 1]
                    # Allowed: rules and validators that forbid IDs or direct service calls.
                    if re.search(r"(?i)never|must not|remove any|no `|reject|no direct", context):
                        continue
                    self.fail(f"{path.relative_to(ROOT)}:{line}: {context.strip()}")

    def test_handoff_contract_is_identical_in_both_skills(self):
        self.assertEqual(contract_block(MODELER), contract_block(AUTHORING))
        for field in ("SOLUTION_DIR", "PACKAGE_PATH", "ONTOLOGY_KEY", "ENTITY_KEYS", "ARTIFACT_INVENTORY",
                      "GATES", "UNRESOLVED_AMBIGUITIES"):
            self.assertIn(field, MODELER)
            self.assertIn(field, AUTHORING)

    def test_gate_ids_match_preflight(self):
        gates = load_preflight().GATES
        listed = re.search(r"^Gates: (.+)$", MODELER, re.M).group(1)
        self.assertEqual(re.findall(r"`([A-Z_0-9]+)`", listed), list(gates))

    def test_artifact_types_and_suffixes_match_preflight(self):
        preflight = load_preflight()
        types = re.findall(r"^\| `\{name\}[^|]*\| `([a-z-]+)` \|", MODELER, re.M)
        self.assertIn('files add "<ONTOLOGY_KEY>" --file "<WORKDIR>/<FILE>" --file-type <TYPE>', MODELER)
        self.assertEqual(sorted(types), sorted(preflight.ARTIFACT_KINDS))
        self.assertIn("{name}-mapping.yarrrml.yml", MODELER)
        self.assertIn(".yarrrml.yml", preflight.ARTIFACT_SUFFIXES)
        self.assertIn(preflight.ONTOLOGY_NAME_RE.pattern, MODELER)
        self.assertIn(preflight.ONTOLOGY_NAME_RE.pattern, AUTHORING)

    def test_scripts_and_references_exist(self):
        for script in re.findall(r"<SKILL_DIR>/(scripts/[\w.]+)", MODELER):
            self.assertTrue((MODELER_DIR / script).is_file(), script)
        for skill_dir, text in ((MODELER_DIR, MODELER), (SKILLS / "uipath-ontology-authoring", AUTHORING)):
            for link in re.findall(r"\]\(([^)#]+\.md)\)", text):
                self.assertTrue((skill_dir / link).is_file(), link)
        for ref in (MODELER_DIR / "references").glob("*.md"):
            for link in re.findall(r"\]\(([^)#]+\.md)\)", ref.read_text(encoding="utf-8")):
                self.assertTrue((ref.parent / link).is_file(), f"{ref.name} -> {link}")

    def test_modeler_command_order(self):
        order = ('ontology_entities.py" --workdir', 'ontology_preflight.py" --workdir', 'uip solution init "',
                 "--kind Entity --name", "--kind Ontology --name", "--add-entity <ENTITY_NAME> <",
                 'uip solution resources files add "', 'uip solution pack "')
        positions = [MODELER.index(marker) for marker in order]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("<WORKDIR>/input/handoff.json", MODELER)
        self.assertIn("Stop after pack", MODELER)

    def test_authoring_delegates_and_stops_after_pack(self):
        for marker in ("Phase 3 — Define business concepts", "Phase 4 — Define properties and relationships",
                       "Phase 5 — Define labels, descriptions, and synonyms", "Step 2 — Build the local solution"):
            self.assertIn(marker, AUTHORING)
        self.assertLess(AUTHORING.index("Phase 3 —"), AUTHORING.index("Step 2 — Build"))
        self.assertIn("If `uipath-ontology-modeler` is not available", AUTHORING)
        self.assertIn("Stop after pack", AUTHORING)
        self.assertNotIn("../uipath-ontology-modeler", AUTHORING)
        self.assertNotIn("scripts/ontology_", AUTHORING)

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
