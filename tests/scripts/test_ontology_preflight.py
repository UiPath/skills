#!/usr/bin/env python3
"""Behavioral tests for the neutral ontology preflight CLI."""

# `X | None` in a signature is evaluated at def time, so without this the suite cannot even
# import on Python < 3.10. CI runs 3.13, which hid it; the tool itself already does this.
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "ontology_preflight.py"
FIXTURES = ROOT / "tests" / "tasks" / "uipath-ontology-modeler" / "_shared" / "fixtures" / "preflight"


COMPLETE_HANDOFF = {
    "CLASS_MAP": {"Order": {"entityName": "Orders", "entityId": "order-id", "folderId": "folder-id"}},
    "FIELD_METADATA": {"Order": {"id": {"identifier": True}, "status": {}}},
    "RELATIONSHIPS": [],
}


def run_preflight_at(workdir: Path, mapping_mode: str = "auto", handoff: dict | None = None) -> tuple[int, dict]:
    """run_preflight against an arbitrary directory, for tests that mutate a copied fixture."""
    command = [sys.executable, str(TOOL), "--workdir", str(workdir),
               "--ontology-name", "demo", "--mapping-mode", mapping_mode]
    if handoff is not None:
        command.extend(("--handoff", json.dumps(handoff)))
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"status": "TOOL_MISSING", "gate_results": [], "mapping_status": None, "errors": {}}
    return result.returncode, payload


def run_preflight(case: str, mapping_mode: str = "auto", handoff: dict | None = None) -> tuple[int, dict]:
    command = [sys.executable, str(TOOL), "--workdir", str(FIXTURES / case),
               "--ontology-name", "demo", "--mapping-mode", mapping_mode]
    if handoff is not None:
        command.extend(("--handoff", json.dumps(handoff)))
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"status": "TOOL_MISSING", "gate_results": [], "mapping_status": None, "errors": {}}
    return result.returncode, payload


class OntologyPreflightTests(unittest.TestCase):
    def copy_fixture(self, case: str) -> Path:
        """A writable copy of a fixture, for tests that need to mutate one."""
        temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp, True)
        workdir = temp / case
        shutil.copytree(FIXTURES / case, workdir)
        return workdir

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
            "CLASS_MAP": {"Order": {"entityId": "order-id", "folderId": "folder-id"}},
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
            {"schema": ["demo.ofn"], "constraints": ["demo-constraints.ttl"], "functions": [], "actions": [], "mapping": ["demo-mapping.yarrrml.yml"]},
        )

    def test_duplicate_schema_is_rejected_by_artifact_inventory_gate(self):
        self.assert_gate_fails("duplicate-schema", "ARTIFACT_INVENTORY")

    def test_duplicate_mapping_is_rejected_by_artifact_inventory_gate(self):
        self.assert_gate_fails("duplicate-mapping", "ARTIFACT_INVENTORY")

    def test_missing_constraints_is_rejected_by_artifact_inventory_gate(self):
        self.assert_gate_fails("missing-constraints", "ARTIFACT_INVENTORY")

    def test_duplicate_constraints_is_rejected_by_artifact_inventory_gate(self):
        self.assert_gate_fails("duplicate-constraints", "ARTIFACT_INVENTORY")

    def test_unclassified_artifact_file_is_rejected_by_artifact_inventory_gate(self):
        self.assert_gate_fails("unclassified-artifact", "ARTIFACT_INVENTORY")

    def test_supported_function_action_and_platform_namespaces_pass_iri_gate(self):
        code, payload = run_preflight("support-namespaces", "auto", COMPLETE_HANDOFF)
        self.assertEqual(code, 0, payload)
        iri_gate = next(item for item in payload["gate_results"] if item["id"] == "IRI_CONSISTENCY")
        self.assertTrue(iri_gate["passed"], payload)


    def test_supplied_mapping_agreeing_with_the_handoff_stays_valid(self):
        """The happy path: the mapping's ids are the ones the handoff declares."""
        code, payload = run_preflight("supplied-mapping", "auto", COMPLETE_HANDOFF)
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["mapping_status"], "PRESENT_VALID")

    def test_mapping_binding_an_undeclared_entity_id_is_invalid(self):
        """A mapping generated before its entities existed carries ids nothing declares.

        This is the state the coded-action path used to force: entity creation waits for the
        deployment to make the folder, so a mapping written at generation time can only hold
        placeholders. The terms gate passes them -- the `ont:` names are all declared -- so
        without this check preflight reported PRESENT_VALID over bindings that resolve to
        nothing, and the first symptom was a deployed ontology with dead bindings.
        """
        handoff = json.loads(json.dumps(COMPLETE_HANDOFF))
        handoff["CLASS_MAP"]["Order"]["entityId"] = "00000000-0000-0000-0000-00000000e001"
        code, payload = run_preflight("supplied-mapping", "auto", handoff)
        self.assertNotEqual(code, 0, payload)
        self.assertEqual(payload["mapping_status"], "PRESENT_INVALID")
        detail = payload["errors"]["MAPPING_TERMS"][0]
        self.assertIn("order-id", detail)
        self.assertIn("entityId", detail)

    def test_mapping_bindings_are_unchecked_without_a_handoff(self):
        """No handoff means no declared ids to compare against, so the gate holds no opinion --
        a missing handoff is already the generation branch's error to report, not this one's."""
        code, payload = run_preflight("supplied-mapping", "auto")
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["mapping_status"], "PRESENT_VALID")

    def test_a_term_iri_under_the_right_base_is_consistent(self):
        """The OWL guide's section-header comments write terms as full IRIs, e.g.
        `# Data Property: <https://ontology.uipath.com/demo#Order.status> (...)`. Terms are
        normally prefixed, so a full one only appears in such a comment, and the gate used to
        reject it as "old or inconsistent" when it was neither -- a false positive on the form
        the guide itself prescribes."""
        workdir = self.copy_fixture("supplied-mapping")
        schema = workdir / "demo.ofn"
        schema.write_text(schema.read_text()
                          + "\n# Data Property: <https://ontology.uipath.com/demo#Order.status> (Status)\n")
        code, payload = run_preflight_at(workdir, handoff=COMPLETE_HANDOFF)
        self.assertEqual(code, 0, payload)

    def test_a_term_iri_under_the_wrong_base_still_fails(self):
        """The other half: judging by base must not become judging by nothing."""
        workdir = self.copy_fixture("supplied-mapping")
        schema = workdir / "demo.ofn"
        schema.write_text(schema.read_text()
                          + "\n# Data Property: <https://ontology.uipath.com/oldname#Order.status> (stale)\n")
        code, payload = run_preflight_at(workdir, handoff=COMPLETE_HANDOFF)
        self.assertNotEqual(code, 0, payload)
        self.assertIn("oldname", payload["errors"]["IRI_CONSISTENCY"][0])

if __name__ == "__main__":
    unittest.main()
