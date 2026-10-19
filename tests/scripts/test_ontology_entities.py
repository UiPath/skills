#!/usr/bin/env python3
"""Behavioral tests for the ontology entity-definition generator."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "skills" / "uipath-ontology-modeler" / "scripts" / "ontology_entities.py"

HANDOFF = {
    "CLASS_MAP": {"Order": {"entityName": "Order"}, "Customer": {"entityName": "Customer"}},
    "FIELD_METADATA": {
        "Order": {
            "Id": {"identifier": True},
            "orderNumber": {"type": "xsd:string", "required": True, "displayName": "Order Number"},
            "total": {"type": "xsd:decimal"},
            "placedAt": {"type": "xsd:dateTime"},
            "customer": {"displayName": "Customer"},
        },
        "Customer": {"Id": {"identifier": True}, "customerName": {"type": "xsd:string", "length": 120}},
    },
    "RELATIONSHIPS": [{"from": "Order", "field": "customer", "to": "Customer"}],
}


def invoke(workdir: Path) -> tuple[int, dict]:
    result = subprocess.run([sys.executable, str(TOOL), "--workdir", str(workdir)],
                            cwd=ROOT, text=True, capture_output=True)
    return result.returncode, json.loads(result.stdout)


def run(handoff: dict, workdir: Path | None = None) -> tuple[int, dict, Path]:
    workdir = workdir or Path(tempfile.mkdtemp()) / "demo"
    (workdir / "input").mkdir(parents=True, exist_ok=True)
    (workdir / "input" / "handoff.json").write_text(json.dumps(handoff), encoding="utf-8")
    code, payload = invoke(workdir)
    return code, payload, workdir / "entities"


class OntologyEntitiesTests(unittest.TestCase):
    def test_writes_entity_records_and_patches(self):
        code, payload, out = run(HANDOFF)
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["status"], "PASS")
        order = json.loads((out / "Order.json").read_text())
        self.assertEqual(order["Name"], "Order")
        self.assertEqual(order["DisplayName"], "Order")
        fields = {f["Name"]: f for f in order["Fields"]}
        self.assertEqual(set(fields), {"orderNumber", "total", "placedAt", "customer"})
        self.assertEqual(fields["orderNumber"]["SqlType"], {"Name": "NVARCHAR", "LengthLimit": 200})
        self.assertTrue(fields["orderNumber"]["IsRequired"])
        self.assertEqual(fields["orderNumber"]["DisplayName"], "Order Number")
        self.assertEqual(fields["total"]["SqlType"], {"Name": "DECIMAL"})
        self.assertEqual(fields["placedAt"]["SqlType"], {"Name": "DATETIME2"})
        self.assertEqual(fields["customer"]["FieldDisplayType"], "Relationship")
        self.assertEqual(fields["customer"]["ReferenceEntity"], {"Name": "Customer"})
        self.assertNotIn("FolderId", json.dumps(order))
        customer = json.loads((out / "Customer.json").read_text())
        self.assertEqual(customer["Fields"][0]["SqlType"], {"Name": "NVARCHAR", "LengthLimit": 120})
        patch = json.loads((out / "Order.patch.json").read_text())
        self.assertEqual(json.loads(patch["resourceJson"]), order)

    def test_skips_system_fields(self):
        code, payload, out = run(HANDOFF)
        names = [f["Name"] for f in json.loads((out / "Order.json").read_text())["Fields"]]
        self.assertNotIn("Id", names)

    def test_entity_name_from_class_map_not_class(self):
        handoff = json.loads(json.dumps(HANDOFF))
        handoff["CLASS_MAP"]["Order"]["entityName"] = "Orders"
        code, payload, out = run(handoff)
        self.assertEqual(code, 0, payload)
        self.assertTrue((out / "Orders.json").is_file())

    def test_unknown_type_fails_and_writes_nothing(self):
        handoff = json.loads(json.dumps(HANDOFF))
        handoff["FIELD_METADATA"]["Order"]["total"]["type"] = "xsd:money"
        code, payload, out = run(handoff)
        self.assertEqual(code, 1)
        self.assertIn("Order.total", payload["errors"][0])
        self.assertIn("xsd:money", payload["errors"][0])
        self.assertFalse(out.exists())

    def test_non_string_type_fails_as_unknown_type(self):
        handoff = json.loads(json.dumps(HANDOFF))
        handoff["FIELD_METADATA"]["Order"]["total"]["type"] = ["xsd:decimal"]
        code, payload, out = run(handoff)
        self.assertEqual(code, 1)
        self.assertEqual(payload["status"], "FAIL")
        self.assertIn("Order.total: unknown type", payload["errors"][0])
        self.assertFalse(out.exists())

    def test_system_field_name_in_other_case_fails(self):
        handoff = json.loads(json.dumps(HANDOFF))
        handoff["FIELD_METADATA"]["Order"]["createdAt"] = {"type": "xsd:dateTime"}
        code, payload, _ = run(handoff)
        self.assertEqual(code, 1)
        joined = "\n".join(payload["errors"])
        self.assertIn("Order.createdAt", joined)
        self.assertIn("'CreatedAt'", joined)

    def test_invalid_names_fail(self):
        handoff = json.loads(json.dumps(HANDOFF))
        handoff["CLASS_MAP"]["Order"]["entityName"] = "Or"
        handoff["FIELD_METADATA"]["Customer"]["bad_name"] = {"type": "xsd:string"}
        code, payload, _ = run(handoff)
        self.assertEqual(code, 1)
        joined = "\n".join(payload["errors"])
        self.assertIn("'Or'", joined)
        self.assertIn("bad_name", joined)

    def test_ids_in_class_map_are_rejected(self):
        handoff = json.loads(json.dumps(HANDOFF))
        handoff["CLASS_MAP"]["Order"]["entityId"] = "abc"
        code, payload, _ = run(handoff)
        self.assertEqual(code, 1)
        self.assertIn("entityId", "\n".join(payload["errors"]))

    def test_duplicate_entity_names_fail(self):
        handoff = json.loads(json.dumps(HANDOFF))
        handoff["CLASS_MAP"]["Customer"]["entityName"] = "order"
        code, payload, _ = run(handoff)
        self.assertEqual(code, 1)
        self.assertIn("more than one class", "\n".join(payload["errors"]))

    def test_relationship_to_unknown_class_fails(self):
        handoff = json.loads(json.dumps(HANDOFF))
        handoff["RELATIONSHIPS"] = [{"from": "Order", "field": "customer", "to": "Ghost"}]
        code, payload, _ = run(handoff)
        self.assertEqual(code, 1)
        self.assertIn("Ghost", "\n".join(payload["errors"]))


class EntitiesPathTests(unittest.TestCase):
    def test_missing_workdir_fails(self):
        code, payload = invoke(Path(tempfile.mkdtemp()) / "absent")
        self.assertEqual(code, 1)
        self.assertIn("existing folder", payload["errors"][0])

    def test_missing_handoff_fails(self):
        workdir = Path(tempfile.mkdtemp())
        code, payload = invoke(workdir)
        self.assertEqual(code, 1)
        self.assertIn("handoff.json", payload["errors"][0])

    def test_entities_path_that_is_a_file_fails(self):
        workdir = Path(tempfile.mkdtemp()) / "demo"
        workdir.mkdir()
        (workdir / "entities").write_text("not a folder")
        code, payload, _ = run(HANDOFF, workdir)
        self.assertEqual(code, 1)
        self.assertIn("must be a folder", payload["errors"][0])

    def test_rerun_removes_stale_entity_files(self):
        code, _, out = run(HANDOFF)
        self.assertEqual(code, 0)
        handoff = json.loads(json.dumps(HANDOFF))
        handoff["CLASS_MAP"]["Order"]["entityName"] = "Orders"
        code, payload, _ = run(handoff, out.parent)
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["removed"], ["Order.json", "Order.patch.json"])
        self.assertEqual(sorted(p.name for p in out.iterdir()),
                         ["Customer.json", "Customer.patch.json", "Orders.json", "Orders.patch.json"])


if __name__ == "__main__":
    unittest.main()
