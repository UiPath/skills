#!/usr/bin/env python3
"""Static contract tests for the delegated ontology skill family."""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "skills"
ONTOLOGY_SKILLS = sorted(SKILLS.glob("uipath-ontolog*"))


def _body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "\n---\n" in text[4:]
    return text


class OntologySkillStructureTests(unittest.TestCase):
    def test_modeler_is_compact_and_has_standalone_and_delegated_modes(self):
        path = SKILLS / "uipath-ontology-modeler" / "SKILL.md"
        text = _body(path)
        self.assertLess(len(text.splitlines()), 500)
        self.assertIn("Standalone", text)
        self.assertIn("Delegated", text)
        for field in ("ONTOLOGY_NAME", "ONTOLOGY_IRI", "WORKDIR", "CLASS_MAP", "MAPPING_STATUS", "DOMAIN_MODEL", "ANNOTATIONS", "OPERATIONS", "DEPLOYMENT_MODE"):
            self.assertIn(field, text)


    def test_routing_descriptions_are_explicit(self):
        expected = {
            "uipath-ontologies": ("Use when", "Do not use"),
            "uipath-ontology-authoring": ("Use when", "Do not use"),
            "uipath-ontology-modeler": ("Use when", "Do not use"),
        }
        for name, markers in expected.items():
            text = _body(SKILLS / name / "SKILL.md")
            frontmatter = text.split("\n---\n", 1)[0]
            for marker in markers:
                self.assertIn(marker, frontmatter)


    def test_authoring_owns_setup_and_delegates_without_structural_file_links(self):
        text = _body(SKILLS / "uipath-ontology-authoring" / "SKILL.md")
        self.assertIn("Delegated modeler contract", text)
        self.assertIn("If the `uipath-ontology-modeler` skill is not available", text)
        self.assertIn("Do not read or import the modeler's files", text)
        self.assertNotIn("../uipath-ontology-modeler", text)
        self.assertFalse(list((SKILLS / "uipath-ontology-authoring" / "references").glob("*.md")))


    def test_modeler_reference_links_resolve_and_no_old_root_paths_remain(self):
        modeler = SKILLS / "uipath-ontology-modeler"
        text = _body(modeler / "SKILL.md")
        for name in (
            "owl-patterns-guide.md",
            "shacl-patterns-guide.md",
            "mapping-yarrrml-guide.md",
            "functions-patterns-guide.md",
            "action-table-contract-guide.md",
        ):
            self.assertTrue((modeler / "references" / name).is_file())
            self.assertIn(f"references/{name}", text)
        for old in ("owl-patterns.md", "shacl-patterns.md", "mapping-yarrrml.md", "functions-patterns.md", "action-table-contract.md"):
            self.assertFalse((modeler / old).exists())


    def test_delegation_fallback_prevents_partial_deployment(self):
        authoring = _body(SKILLS / "uipath-ontology-authoring" / "SKILL.md")
        modeler = _body(SKILLS / "uipath-ontology-modeler" / "SKILL.md")
        self.assertIn("before deployment", authoring)
        self.assertIn("actionable", authoring)
        self.assertIn("partial ontology", modeler)
        self.assertIn("actionable", modeler)
        self.assertIn("Never upload the mapping", modeler)

    def test_artifact_gates_and_upload_sequence_are_explicit(self):
        authoring = _body(SKILLS / "uipath-ontology-authoring" / "SKILL.md")
        modeler = _body(SKILLS / "uipath-ontology-modeler" / "SKILL.md")
        for marker in ("QL gate", "Cross-file gate", "Class deployability gate", "Relationship gate", "Semantic gate"):
            self.assertIn(marker, modeler)
        self.assertLess(modeler.index("1. schema"), modeler.index("3. mapping last"))
        self.assertIn("Upload mapping last", authoring)
        self.assertIn("mapping as deploy trigger", authoring)

    def test_preflight_mapping_contract_and_deployment_gates_are_explicit(self):
        modeler = _body(SKILLS / "uipath-ontology-modeler" / "SKILL.md")
        authoring = _body(SKILLS / "uipath-ontology-authoring" / "SKILL.md")
        for text in (modeler, authoring):
            # <TOOLS_DIR> is the shared tools/ tree; the bare relative form does not
            # resolve from the {workdir} these steps run in. ShippedPathTests enforces that.
            self.assertIn("<TOOLS_DIR>/ontology_preflight.py", text)
            self.assertIn("--mapping-mode auto", text)
            self.assertIn("PRESENT_VALID", text)
            self.assertIn("BLOCKED_AMBIGUITY", text)
            self.assertIn("Data.Valid: true", text)
            self.assertIn("artifact list", text)
            self.assertIn("artifact_inventory", text)
            self.assertIn("--handoff", text)
            self.assertNotIn("GENERATED_VALID", text)
            self.assertIn("RELATIONSHIPS", text)
        self.assertLess(authoring.index("schema first"), authoring.index("mapping last"))
        self.assertLess(authoring.index("mapping last"), authoring.index("Final inventory gate"))

    def test_authoring_does_not_reference_a_phase_two_stub_or_duplicate_step_number(self):
        authoring = _body(SKILLS / "uipath-ontology-authoring" / "SKILL.md")
        self.assertNotIn("Phase 2's `uip ont create`", authoring)
        self.assertEqual(authoring.count("### 3c —"), 1)

    def test_authoring_defers_stub_and_backend_work_until_mapping_and_local_preflight(self):
        authoring = _body(SKILLS / "uipath-ontology-authoring" / "SKILL.md")
        modeler = _body(SKILLS / "uipath-ontology-modeler" / "SKILL.md")
        self.assertIn("Do not create the ontology stub", authoring)
        self.assertIn("Do not create the ontology stub", modeler)
        self.assertLess(authoring.index("First validate the provided mapping"), authoring.index("local preflight"))
        self.assertLess(authoring.index("local preflight"), authoring.index("uip ont create"))
        self.assertLess(modeler.index("local preflight"), modeler.index("uip ont create"))

    def test_delegated_modeler_returns_local_artifacts_while_authoring_owns_backend_tiers(self):
        authoring = _body(SKILLS / "uipath-ontology-authoring" / "SKILL.md")
        modeler = _body(SKILLS / "uipath-ontology-modeler" / "SKILL.md")
        self.assertIn("DEPLOYMENT_MODE: delegated; generate artifacts and run local preflight only", modeler)
        self.assertIn("Never make backend calls or upload artifacts in delegated mode", modeler)
        self.assertIn("Authoring backend-validates every artifact in `artifact_inventory`", authoring)
        self.assertIn("requires `Data.Valid: true`", authoring)
        self.assertIn("Tier 2 — constraints, functions, and actions", authoring)
        self.assertIn("Tier 3 — mapping only, last", authoring)
        self.assertLess(authoring.index("uip ont create {name}"), authoring.index("uip ont artifact validate {name}"))
        self.assertLess(authoring.index("uip ont artifact validate {name}"), authoring.index("Tier 1 — schema"))
        self.assertLess(authoring.index("Tier 1 — schema"), authoring.index("Tier 3 — mapping only, last"))

    def test_gate_and_mapping_upload_ownership_are_mode_qualified(self):
        authoring = _body(SKILLS / "uipath-ontology-authoring" / "SKILL.md")
        modeler = _body(SKILLS / "uipath-ontology-modeler" / "SKILL.md")
        mapping_guide = (SKILLS / "uipath-ontology-modeler" / "references" / "mapping-yarrrml-guide.md").read_text(encoding="utf-8")
        self.assertIn("Modeler — local QL/naming/cross-file/annotation/semantic/preflight gates", authoring)
        self.assertIn("Authoring — backend validation and tiered upsert", authoring)
        self.assertIn("mapping is held until authoring uploads it last", authoring)
        self.assertNotIn("All six gates the modeler runs", authoring)
        gate_table = authoring.split("Gate ownership and execution:", 1)[1].split("**Do not proceed", 1)[0]
        self.assertNotIn("Step 3c", gate_table)
        self.assertNotIn("Step 5c", gate_table)
        for text in (authoring, modeler):
            self.assertIn("`MAPPING_STATUS: supplied`", text)
            self.assertIn("validate the provided mapping", text)
            self.assertIn("`MAPPING_STATUS: generate`", text)
            self.assertIn("generate it from handoff metadata", text)
            self.assertNotIn("generates the mapping in either mode", text)
        self.assertGreaterEqual(mapping_guide.count("standalone modeler"), 2)
        self.assertGreaterEqual(mapping_guide.count("delegated modeler"), 2)
        self.assertIn("authoring uploads it last", mapping_guide)

    def test_authoring_owns_draft_and_backend_validation_recovery(self):
        authoring = _body(SKILLS / "uipath-ontology-authoring" / "SKILL.md")
        modeler = _body(SKILLS / "uipath-ontology-modeler" / "SKILL.md")
        self.assertIn("Follow this skill's recovery sequence", authoring)
        self.assertIn("backend-validate the exact preflight inventory again (3b)", authoring)
        self.assertIn("including a `422`", authoring)
        self.assertIn("authoring owns the recovery", authoring)
        self.assertIn("may re-delegate only local artifact regeneration", authoring)
        self.assertIn("makes no backend calls", authoring)
        self.assertNotIn("Steps 3e and 4e in the modeler", authoring)
        self.assertIn("Never make backend calls or upload artifacts in delegated mode", modeler)

    def test_activation_fixtures_cover_generated_mapping_and_ambiguity(self):
        for skill, prompts in {
            "uipath-ontology-modeler": ("no mapping file", "BLOCKED_AMBIGUITY"),
            "uipath-ontology-authoring": ("mapping is missing", "unresolved"),
        }.items():
            path = ROOT / "tests" / "tasks" / "activation" / f"{skill}.jsonl"
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            joined = "\n".join(row["prompt"] for row in rows).lower()
            for marker in prompts:
                self.assertIn(marker.lower(), joined)



class ShippedPathTests(unittest.TestCase):
    """Every path the ontology skills invoke must exist AND be published.

    `package.json:files` is an allowlist. A path that resolves in the git checkout but sits under a
    directory not on that list is absent on every installed machine, and this family invokes Python
    from `tools/` that the deploy skill's own `_staging.py` hard-requires -- so omitting it did not
    degrade the skill, it stopped Phase 2 at its first script with `cannot find tools/entry_points.py`.
    Nothing else in the suite would have noticed: the tests run from the checkout, where it is there.

    `tools/` cannot move under `skills/` to dodge this. CLAUDE.md rule 5 forbids a skill reading
    another skill's files, and `entry_points.py` is read by both the deploy skill's staging step and
    the modeler validator's contract gate, so shared code has to live outside `skills/` and ship.
    """

    def published_roots(self):
        return set(json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["files"])

    def invoked_paths(self):
        """Every Python path a shipped ontology file names, placeholders resolved.

        `<SKILL_DIR>` is the skill's own folder and `<TOOLS_DIR>` the shared `tools/` tree, both
        defined in the SKILL.md that uses them. A bare `tools/x.py` or `scripts/x.py` counts too --
        it is the form that does not resolve from `{workdir}`, so it must not creep back in.
        """
        pattern = re.compile(
            r"(?:<SKILL_DIR>/|<TOOLS_DIR>/|(?<![\w./-]))((?:tools/|scripts/)?[\w/]+\.py)")
        for skill in ONTOLOGY_SKILLS:
            for path in sorted(skill.rglob("*")):
                if path.suffix not in (".md", ".py") or not path.is_file():
                    continue
                text = path.read_text(encoding="utf-8")
                for line in text.splitlines():
                    for match in pattern.finditer(line):
                        named = match.group(1)
                        prefix = match.group(0)[: -len(named)]
                        if prefix == "<TOOLS_DIR>/":
                            yield path, "tools/" + named, line
                        elif prefix == "<SKILL_DIR>/":
                            yield path, named, line
                        elif named.startswith(("tools/", "scripts/")):
                            yield path, named, line

    def test_every_invoked_path_exists_and_is_published(self):
        published = self.published_roots()
        seen = 0
        for source, invoked, line in self.invoked_paths():
            seen += 1
            with self.subTest(source=str(source.relative_to(ROOT)), invoked=invoked):
                # A skill-relative `scripts/...` resolves inside its own skill; `tools/...` at root.
                candidates = [ROOT / invoked]
                skill = next(s for s in ONTOLOGY_SKILLS if s in source.parents or s == source.parent)
                candidates.append(skill / invoked)
                resolved = next((c for c in candidates if c.is_file()), None)
                self.assertIsNotNone(
                    resolved, "%s names %s, which is not a file at %s" % (
                        source.relative_to(ROOT), invoked,
                        " or ".join(str(c.relative_to(ROOT)) for c in candidates)))
                if invoked.startswith(("tools/", "scripts/")) and "python3 " in line \
                        and "<SKILL_DIR>/" not in line and "<TOOLS_DIR>/" not in line:
                    self.fail(
                        "%s invokes a bare %s. Steps run from {workdir}, where that path does not "
                        "exist, and the file is not executable. Use python3 <SKILL_DIR>/scripts/... "
                        "or python3 <TOOLS_DIR>/... instead.\n    %s"
                        % (source.relative_to(ROOT), invoked, line.strip()))
                root_dir = resolved.relative_to(ROOT).parts[0]
                self.assertIn(root_dir, published,
                              "%s invokes %s, but %r is absent from package.json:files, so the file "
                              "does not exist on an installed machine"
                              % (source.relative_to(ROOT), invoked, root_dir))
        self.assertGreater(seen, 5, "found almost no invocations -- the regex probably stopped matching")


if __name__ == "__main__":
    unittest.main()
