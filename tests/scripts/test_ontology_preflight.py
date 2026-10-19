#!/usr/bin/env python3
"""Behavioral tests for the neutral ontology preflight CLI."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "skills" / "uipath-ontology-modeler" / "scripts" / "ontology_preflight.py"
FIXTURES = ROOT / "tests" / "tasks" / "uipath-ontology-modeler" / "_shared" / "fixtures" / "preflight"


COMPLETE_HANDOFF = {
    "CLASS_MAP": {"Order": {"entityName": "Orders"}},
    "FIELD_METADATA": {"Order": {"id": {"identifier": True}, "status": {}}},
    "RELATIONSHIPS": [],
}


def stage(case: str, name: str = "demo") -> Path:
    """Copy a fixture into a fresh <tmp>/<name>/ WORKDIR, the layout the skill uses."""
    base = Path(tempfile.mkdtemp(prefix="ontology-preflight-"))
    workdir = base / name
    shutil.copytree(FIXTURES / case, workdir)
    return workdir


def invoke(workdir: Path, *extra: str, name: str = "demo", mapping_mode: str = "auto") -> tuple[int, dict]:
    command = [sys.executable, str(TOOL), "--workdir", str(workdir), "--ontology-name", name,
               "--mapping-mode", mapping_mode, *extra]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"status": "TOOL_MISSING", "gate_results": [], "mapping_status": None, "errors": {}}
    return result.returncode, payload


def run_preflight(case: str, mapping_mode: str = "auto", handoff: dict | None = None,
                  entities_dir: str | None = None) -> tuple[int, dict]:
    workdir = stage(case)
    if entities_dir is None:
        shutil.rmtree(workdir / "entities", ignore_errors=True)
    if handoff is not None:
        (workdir / "input").mkdir(exist_ok=True)
        (workdir / "input" / "handoff.json").write_text(json.dumps(handoff), encoding="utf-8")
    return invoke(workdir, mapping_mode=mapping_mode)


class OntologyPreflightTests(unittest.TestCase):
    def assert_gate_fails(self, case: str, gate_id: str) -> dict:
        code, payload = run_preflight(case)
        self.assertNotEqual(code, 0)
        failed = {gate["id"] for gate in payload["gate_results"] if not gate["passed"]}
        self.assertIn(gate_id, failed)
        self.assertIn(gate_id, payload["errors"])
        return payload

    def test_old_iri_fails_iri_gate(self):
        self.assert_gate_fails("old-iri", "IRI_CONSISTENCY")

    def test_owl_2_ql_forbidden_construct_fails_ql_gate(self):
        self.assert_gate_fails("ql-forbidden", "OWL_2_QL")

    def test_has_prefixed_data_property_fails_naming_gate(self):
        self.assert_gate_fails("has-data-property", "DATA_PROPERTY_NAMING")

    def test_class_without_label_and_comment_fails_annotation_gate(self):
        self.assert_gate_fails("missing-class-annotations", "CLASS_ANNOTATIONS")

    def test_class_without_mapping_instantiation_fails_deployability_gate(self):
        self.assert_gate_fails("class-not-mapped", "CLASS_DEPLOYABILITY")

    def test_unmapped_schema_property_fails_deterministic_semantic_gate(self):
        self.assert_gate_fails("semantic-mapping-gap", "SEMANTIC_CONSISTENCY")

    def test_unknown_mapping_term_fails_mapping_term_gate(self):
        self.assert_gate_fails("mapping-term-absent", "MAPPING_TERMS")

    def test_fk_join_without_object_property_fails_relationship_gate(self):
        self.assert_gate_fails("fk-without-object-property", "RELATIONSHIP")

    def test_action_without_returns_fails_action_contract_gate(self):
        self.assert_gate_fails("action-without-returns", "ACTION_CONTRACT")

    def test_non_global_shapes_prefix_fails_namespace_gate(self):
        self.assert_gate_fails("non-global-shape", "NAMESPACE")

    def test_missing_mapping_without_machine_readable_handoff_is_blocked(self):
        code, payload = run_preflight("missing-mapping", "auto")
        self.assertNotEqual(code, 0)
        self.assertEqual(payload["mapping_status"], "BLOCKED_AMBIGUITY")
        self.assertIn("MAPPING_TERMS", payload["errors"])

    def test_missing_mapping_with_complete_machine_readable_handoff_is_generatable(self):
        code, payload = run_preflight("missing-mapping", "auto", COMPLETE_HANDOFF)
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["mapping_status"], "GENERATE_MAPPING")

    def test_missing_mapping_in_required_mode_reports_required_mapping(self):
        code, payload = run_preflight("missing-mapping", "required")
        self.assertNotEqual(code, 0)
        self.assertEqual(payload["mapping_status"], "BLOCKED_AMBIGUITY")
        self.assertEqual(payload["errors"]["MAPPING_TERMS"], ["Mapping is required but missing."])

    def test_supplied_mapping_does_not_require_generation_handoff(self):
        code, payload = run_preflight("supplied-mapping", "auto")
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["mapping_status"], "PRESENT_VALID")

    def test_incomplete_handoff_is_blocked_even_when_schema_has_a_class(self):
        code, payload = run_preflight("missing-mapping", "auto", {"CLASS_MAP": COMPLETE_HANDOFF["CLASS_MAP"]})
        self.assertNotEqual(code, 0)
        self.assertEqual(payload["mapping_status"], "BLOCKED_AMBIGUITY")
        self.assertIn("FIELD_METADATA", payload["errors"]["MAPPING_TERMS"][0])

    def test_handoff_without_entity_name_is_blocked(self):
        handoff = {
            "CLASS_MAP": {"Order": {"displayName": "Order"}},
            "FIELD_METADATA": COMPLETE_HANDOFF["FIELD_METADATA"],
            "RELATIONSHIPS": [],
        }
        code, payload = run_preflight("missing-mapping", "auto", handoff)
        self.assertNotEqual(code, 0)
        self.assertEqual(payload["mapping_status"], "BLOCKED_AMBIGUITY")
        self.assertIn("entityName", payload["errors"]["MAPPING_TERMS"][0])

    def test_handoff_without_explicit_empty_relationships_is_blocked(self):
        handoff = {
            "CLASS_MAP": COMPLETE_HANDOFF["CLASS_MAP"],
            "FIELD_METADATA": COMPLETE_HANDOFF["FIELD_METADATA"],
        }
        code, payload = run_preflight("missing-mapping", "auto", handoff)
        self.assertNotEqual(code, 0)
        self.assertEqual(payload["mapping_status"], "BLOCKED_AMBIGUITY")
        self.assertIn("RELATIONSHIPS", payload["errors"]["MAPPING_TERMS"][0])

    def test_handoff_with_two_identifier_fields_is_blocked(self):
        handoff = {
            "CLASS_MAP": COMPLETE_HANDOFF["CLASS_MAP"],
            "FIELD_METADATA": {"Order": {"id": {"identifier": True}, "status": {"identifier": True}}},
        }
        code, payload = run_preflight("missing-mapping", "auto", handoff)
        self.assertNotEqual(code, 0)
        self.assertEqual(payload["mapping_status"], "BLOCKED_AMBIGUITY")
        self.assertIn("exactly one identifier", payload["errors"]["MAPPING_TERMS"][0])

    def test_data_property_mapping_is_not_treated_as_a_relationship_join(self):
        code, payload = run_preflight("data-property-with-exempt", "auto")
        self.assertEqual(code, 0, payload)
        relationship = next(item for item in payload["gate_results"] if item["id"] == "RELATIONSHIP")
        self.assertTrue(relationship["passed"], payload)

    def test_unrelated_exempt_marker_does_not_disable_an_actual_join_check(self):
        self.assert_gate_fails("join-with-unrelated-exempt", "RELATIONSHIP")

    def test_cross_file_gate_scans_inline_function_and_action_sql_bodies(self):
        payload = self.assert_gate_fails("inline-and-action-statements", "CROSS_FILE_TERMS")
        diagnostics = payload["errors"]["CROSS_FILE_TERMS"]
        self.assertTrue(any("demo-functions.ttl" in item for item in diagnostics), diagnostics)
        self.assertTrue(any("demo-action.ttl" in item for item in diagnostics), diagnostics)

    def test_action_contract_checks_each_action_resource_independently(self):
        payload = self.assert_gate_fails("mixed-action-contracts", "ACTION_CONTRACT")
        self.assertTrue(any("secondAction" in item for item in payload["errors"]["ACTION_CONTRACT"]))

    def test_artifact_inventory_is_exact_for_a_valid_workdir(self):
        code, payload = run_preflight("supplied-mapping", "auto")
        self.assertEqual(code, 0, payload)
        self.assertEqual(
            payload["artifact_inventory"],
            {"schema": ["demo.ofn"], "constraints": ["demo-constraints.ttl"], "functions": [], "actions": [],
             "mapping": ["demo-mapping.yarrrml.yml"], "business-rules": [], "summary": [], "context": []},
        )

    def test_duplicate_schema_is_rejected_by_artifact_inventory_gate(self):
        self.assert_gate_fails("duplicate-schema", "ARTIFACT_INVENTORY")

    def test_duplicate_mapping_is_rejected_by_artifact_inventory_gate(self):
        self.assert_gate_fails("duplicate-mapping", "ARTIFACT_INVENTORY")

    def test_missing_constraints_is_rejected_by_artifact_inventory_gate(self):
        self.assert_gate_fails("missing-constraints", "ARTIFACT_INVENTORY")

    def test_multiple_constraints_files_are_allowed(self):
        _, payload = run_preflight("duplicate-constraints")
        gates = {gate["id"]: gate["passed"] for gate in payload["gate_results"]}
        self.assertTrue(gates["ARTIFACT_INVENTORY"], payload["errors"])

    def test_unclassified_artifact_file_is_rejected_by_artifact_inventory_gate(self):
        self.assert_gate_fails("unclassified-artifact", "ARTIFACT_INVENTORY")

    def test_optional_business_rules_summary_and_context_pass(self):
        code, payload = run_preflight("optional-artifacts", entities_dir="entities")
        self.assertEqual(code, 0, payload["errors"])
        inventory = payload["artifact_inventory"]
        self.assertEqual(inventory["business-rules"], ["demo-business-rules.ttl"])
        self.assertEqual(inventory["summary"], ["demo-summary.txt"])
        self.assertEqual(inventory["context"], ["demo-context.json"])
        self.assertEqual(inventory["constraints"], ["demo-constraints.ttl"])

    def test_two_summary_files_fail_artifact_inventory(self):
        code, payload = run_preflight("duplicate-summary", entities_dir="entities")
        self.assertNotEqual(code, 0)
        self.assertIn("summary", "\n".join(payload["errors"]["ARTIFACT_INVENTORY"]))

    def test_supported_function_action_and_platform_namespaces_pass_iri_gate(self):
        code, payload = run_preflight("support-namespaces", "auto", COMPLETE_HANDOFF)
        self.assertEqual(code, 0, payload)
        iri_gate = next(item for item in payload["gate_results"] if item["id"] == "IRI_CONSISTENCY")
        self.assertTrue(iri_gate["passed"], payload)

    def test_handoff_with_entity_ids_is_blocked(self):
        handoff = dict(COMPLETE_HANDOFF, CLASS_MAP={"Order": {"entityName": "Orders", "entityId": "x"}})
        code, payload = run_preflight("missing-mapping", "auto", handoff)
        self.assertNotEqual(code, 0)
        self.assertIn("entityId", payload["errors"]["MAPPING_TERMS"][0])

    def test_missing_constraints_fails_inventory(self):
        self.assert_gate_fails("missing-constraints", "ARTIFACT_INVENTORY")

    def test_local_entities_pass(self):
        code, payload = run_preflight("local-entities", entities_dir="entities")
        self.assertEqual(code, 0, payload["errors"])

    def test_unknown_table_fails_local_entities(self):
        code, payload = run_preflight("local-entities-unknown-table", entities_dir="entities")
        self.assertNotEqual(code, 0)
        joined = "\n".join(payload["errors"]["LOCAL_ENTITIES"])
        self.assertIn("Orders", joined)
        self.assertIn("Sales is not used", joined)

    def test_column_case_mismatch_fails_local_entities(self):
        code, payload = run_preflight("local-entities-bad-column", entities_dir="entities")
        self.assertNotEqual(code, 0)
        self.assertIn("$(Status)", "\n".join(payload["errors"]["LOCAL_ENTITIES"]))

    def test_mapping_with_ids_fails_even_without_entities_dir(self):
        code, payload = run_preflight("mapping-with-ids")
        self.assertNotEqual(code, 0)
        self.assertIn("table:", "\n".join(payload["errors"]["LOCAL_ENTITIES"]))

    def test_join_target_columns_are_allowed(self):
        code, payload = run_preflight("join-target-column", entities_dir="entities")
        self.assertNotIn("LOCAL_ENTITIES", payload["errors"], payload["errors"])

    def test_without_entities_dir_warns(self):
        _, payload = run_preflight("supplied-mapping")
        self.assertIn("entities/", "\n".join(payload["warnings"]))


class PathValidationTests(unittest.TestCase):
    def paths_errors(self, payload: dict) -> str:
        return "\n".join(payload["errors"].get("PATHS", []))

    def test_missing_workdir_fails_paths_gate_without_crashing(self):
        code, payload = invoke(Path(tempfile.mkdtemp()) / "demo")
        self.assertEqual(code, 1)
        self.assertEqual([g["id"] for g in payload["gate_results"]], ["PATHS"])

    def test_workdir_must_be_named_after_ontology(self):
        code, payload = invoke(stage("supplied-mapping", name="other"))
        self.assertEqual(code, 1)
        self.assertIn("named after the ontology", self.paths_errors(payload))

    def test_invalid_ontology_name_fails(self):
        workdir = stage("supplied-mapping", name="bad.name")
        code, payload = invoke(workdir, name="bad.name")
        self.assertEqual(code, 1)
        self.assertIn("--ontology-name", self.paths_errors(payload))

    def test_unexpected_subfolder_fails(self):
        workdir = stage("supplied-mapping")
        (workdir / "drafts").mkdir()
        code, payload = invoke(workdir)
        self.assertEqual(code, 1)
        self.assertIn("drafts/", self.paths_errors(payload))

    def test_symlinked_artifact_fails(self):
        workdir = stage("supplied-mapping")
        outside = workdir.parent / "outside-constraints.ttl"
        (workdir / "demo-constraints.ttl").rename(outside)
        os.symlink(outside, workdir / "demo-constraints.ttl")
        code, payload = invoke(workdir)
        self.assertEqual(code, 1)
        self.assertIn("symlink", "\n".join(payload["errors"]["ARTIFACT_INVENTORY"]))

    def test_mapping_must_use_yarrrml_extension(self):
        workdir = stage("supplied-mapping")
        (workdir / "demo-mapping.yarrrml.yml").rename(workdir / "demo-mapping.yml")
        code, payload = invoke(workdir)
        self.assertEqual(code, 1)
        self.assertIn(".yarrrml.yml", "\n".join(payload["errors"]["ARTIFACT_INVENTORY"]))

    def test_artifact_names_must_carry_the_ontology_prefix(self):
        workdir = stage("supplied-mapping")
        (workdir / "demo-constraints.ttl").rename(workdir / "rules-constraints.ttl")
        code, payload = invoke(workdir)
        self.assertEqual(code, 1)
        self.assertIn("must start with 'demo", "\n".join(payload["errors"]["ARTIFACT_INVENTORY"]))

    def test_function_file_named_after_a_class_containing_action_is_not_an_action(self):
        workdir = stage("support-namespaces")
        (workdir / "demo-functions.ttl").rename(workdir / "demo-functions-Transaction.ttl")
        _, payload = invoke(workdir)
        self.assertEqual(payload["artifact_inventory"]["functions"], ["demo-functions-Transaction.ttl"])
        self.assertEqual(payload["artifact_inventory"]["actions"], [])

    def test_non_utf8_artifact_fails_inventory(self):
        workdir = stage("supplied-mapping")
        (workdir / "demo-summary.txt").write_bytes(b"\xff\xfe\x00bad")
        code, payload = invoke(workdir)
        self.assertEqual(code, 1)
        self.assertIn("UTF-8", "\n".join(payload["errors"]["ARTIFACT_INVENTORY"]))

    def test_new_solution_dir_is_accepted(self):
        workdir = stage("local-entities")
        code, payload = invoke(workdir, "--solution-dir", str(workdir.parent / "DemoSolution"))
        self.assertEqual(code, 0, payload["errors"])
        self.assertEqual(payload["paths"]["solution_state"], "new")

    def test_existing_solution_dir_requires_one_uipx(self):
        workdir = stage("local-entities")
        solution = workdir.parent / "DemoSolution"
        solution.mkdir()
        (solution / "notes.txt").write_text("x")
        code, payload = invoke(workdir, "--solution-dir", str(solution))
        self.assertEqual(code, 1)
        self.assertIn(".uipx", self.paths_errors(payload))
        (solution / "DemoSolution.uipx").write_text("{}")
        code, payload = invoke(workdir, "--solution-dir", str(solution))
        self.assertEqual(code, 0, payload["errors"])
        self.assertEqual(payload["paths"]["solution_state"], "existing")

    def test_solution_dir_must_not_overlap_workdir(self):
        workdir = stage("local-entities")
        for solution in (workdir, workdir / "entities" / "Sol", workdir.parent):
            code, payload = invoke(workdir, "--solution-dir", str(solution))
            self.assertEqual(code, 1, solution)
            self.assertIn("separate folders", self.paths_errors(payload))

    def test_solution_dir_requires_entities(self):
        workdir = stage("supplied-mapping")
        code, payload = invoke(workdir, "--solution-dir", str(workdir.parent / "DemoSolution"))
        self.assertEqual(code, 1)
        self.assertIn("ontology_entities.py", self.paths_errors(payload))

    def test_solution_dir_with_missing_parent_fails(self):
        workdir = stage("local-entities")
        code, payload = invoke(workdir, "--solution-dir", str(workdir.parent / "missing" / "Sol"))
        self.assertEqual(code, 1)
        self.assertIn("parent", self.paths_errors(payload))

    def test_entity_file_must_match_entity_name_and_have_patch(self):
        workdir = stage("local-entities")
        (workdir / "entities" / "Orders.json").rename(workdir / "entities" / "Sales.json")
        code, payload = invoke(workdir)
        self.assertEqual(code, 1)
        joined = "\n".join(payload["errors"]["LOCAL_ENTITIES"])
        self.assertIn("must match its entity Name", joined)
        self.assertIn("Sales.patch.json is missing", joined)

    def test_unexpected_file_in_entities_fails(self):
        workdir = stage("local-entities")
        (workdir / "entities" / "x y.json").write_text("{}")
        code, payload = invoke(workdir)
        self.assertEqual(code, 1)
        self.assertIn("x y.json", "\n".join(payload["errors"]["LOCAL_ENTITIES"]))


if __name__ == "__main__":
    unittest.main()
