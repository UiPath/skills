#!/usr/bin/env python3
"""Offline tests for skills/uipath-maestro-case/scripts/audit_bindings.py.

Each case builds a minimal solution tree in a tempdir, so the audit is exercised
against the real file layout it reads in a build. Covers the three sidecar
shapes seen in live runs — correct, caseplan-`bindings[]`-dumped-verbatim, and
invented field names — plus the resourceKey forms.

Every assertion pins a FINDING string, not just the exit code: asserting only on
the code lets a whole check be deleted while the suite stays green.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
_SPEC = importlib.util.spec_from_file_location(
    "audit_bindings",
    ROOT / "skills" / "uipath-maestro-case" / "scripts" / "audit_bindings.py",
)
audit_bindings = importlib.util.module_from_spec(_SPEC)
sys.modules["audit_bindings"] = audit_bindings
_SPEC.loader.exec_module(audit_bindings)

FOLDER = "Shared/uipath-maestro-case/OpsSolution"
KEY = f"{FOLDER}.OpsApi"
CONN = "6a817d24-cbbd-4389-b10d-4329214ffb8d"

def binding(attr, default, key=KEY, resource="process"):
    return {
        "id": f"b{attr}",
        "name": attr,
        "type": "string",
        "resource": resource,
        "resourceKey": key,
        "default": default,
        "propertyAttribute": attr,
    }

def caseplan(*, bindings=None, connector_key="uipath-http-webhook", connector=True):
    tasks = [[{
        "id": "t1", "type": "api-workflow", "displayName": "Call Ops",
        "data": {"name": "=bindings.bname", "folderPath": "=bindings.bfolderPath"},
        "entryConditions": [], "exitConditions": [],
    }]]
    if connector:
        ctx = [{"name": "connectorKey", "value": connector_key}] if connector_key else []
        tasks.append([{
            "id": "t2", "type": "wait-for-connector", "displayName": "Wait Event",
            "data": {"serviceType": "Intsvc.WaitForEvent", "context": ctx},
            "entryConditions": [], "exitConditions": [],
        }])
    return {
        "metadata": {"caseExitRules": []},
        "bindings": bindings if bindings is not None else [
            binding("name", "OpsApi"),
            binding("folderPath", FOLDER),
            {"id": "bc1", "name": "conn", "resource": "Connection",
             "resourceKey": CONN, "default": CONN, "propertyAttribute": "ConnectionId"},
        ],
        "nodes": [{
            "id": "s1", "type": "case-management:Stage",
            "data": {"label": "Stage 1", "tasks": tasks,
                     "entryConditions": [], "exitConditions": []},
        }],
    }

CORRECT_SIDECAR = [
    {"resource": "process", "key": KEY,
     "value": {"name": {"defaultValue": "OpsApi"},
               "folderPath": {"defaultValue": FOLDER}},
     "metadata": {"subType": "Api"}},
    {"resource": "Connection", "key": CONN,
     "value": {"connectionId": {"defaultValue": CONN},
               "folderKey": {"defaultValue": "f-1"}},
     "metadata": {"connector": "uipath-http-webhook"}},
]

def build(tmp, plan, sidecar, *, emit_connection=True):
    sol = pathlib.Path(tmp) / "OpsCase"
    proj = sol / "OpsCase"
    proj.mkdir(parents=True)
    (proj / "caseplan.json").write_text(json.dumps(plan))
    (proj / "bindings_v2.json").write_text(json.dumps({"version": "2.0", "resources": sidecar}))
    if emit_connection:
        d = sol / "resources" / "myfolder" / "connection" / "uipath-http-webhook"
        d.mkdir(parents=True)
        (d / "conn.json").write_text("{}")
    return sol

def run(plan, sidecar, *, emit_connection=True):
    """Return (exit_code, stdout). Asserting only on the code lets a check be
    deleted while the suite stays green - findings must be asserted by text."""
    with tempfile.TemporaryDirectory() as tmp:
        sol = build(tmp, plan, sidecar, emit_connection=emit_connection)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = audit_bindings.check(sol, quiet=True)
        return code, buf.getvalue()

class AuditBindingsTests(unittest.TestCase):
    def test_accepts_correct_solution(self):
        self.assertEqual(run(caseplan(), CORRECT_SIDECAR)[0], 0)

    def test_rejects_caseplan_bindings_dumped_verbatim(self):
        """The dominant live failure: sidecar == caseplan bindings[] 1:1."""
        plan = caseplan()
        code, out = run(plan, plan["bindings"])
        self.assertEqual(code, 1)
        self.assertIn("instead of `key` + nested", out)

    def test_rejects_invented_field_names(self):
        sidecar = [{"id": "r1", "externalId": KEY, "kind": "process",
                    "name": "OpsApi", "properties": {}}]
        code, out = run(caseplan(), sidecar)
        self.assertEqual(code, 1)
        self.assertIn("instead of `key` + nested", out)

    def test_rejects_missing_resource_key(self):
        code, out = run(caseplan(), [CORRECT_SIDECAR[1]])
        self.assertEqual(code, 1)
        self.assertIn("missing resource key(s)", out)

    def test_rejects_tenant_uuid_as_resource_key(self):
        uuid = "70c4fa91-5aa7-47b0-8bfa-bb550fbeee6c"
        plan = caseplan(bindings=[
            binding("name", "OpsApi", key=uuid),
            binding("folderPath", FOLDER, key=uuid),
        ])
        sidecar = [{"resource": "process", "key": uuid,
                    "value": {"name": {"defaultValue": "OpsApi"},
                              "folderPath": {"defaultValue": FOLDER}}}]
        code, out = run(plan, sidecar)
        self.assertEqual(code, 1)
        self.assertIn("not self-consistent", out)

    def test_accepts_inline_sibling_solution_folder_key(self):
        key = "solution_folder.OpsApi"
        plan = caseplan(bindings=[
            binding("name", "OpsApi", key=key),
            binding("folderPath", "", key=key),
        ], connector=False)
        sidecar = [{"resource": "process", "key": key,
                    "value": {"name": {"defaultValue": "OpsApi"},
                              "folderPath": {"defaultValue": "solution_folder"}}}]
        self.assertEqual(run(plan, sidecar, emit_connection=False)[0], 0)

    # -- the D-detection hole this change closes --------------------------------

    # -- what the repointed connection_parity e2e now additionally catches ------

    def test_accepts_general_empty_folderpath_form(self):
        """`folderPath: ""` -> `.{name}` is the GENERAL rule; solution_folder is the
        inline-sibling exception. Both are legal."""
        for key in (".ReviewHITL", "solution_folder.ReviewHITL"):
            plan = caseplan(bindings=[
                binding("name", "ReviewHITL", key=key, resource="app"),
                binding("folderPath", "", key=key, resource="app"),
            ], connector=False)
            sidecar = [{"resource": "app", "key": key, "value": {
                "name": {"defaultValue": "ReviewHITL"},
                "folderPath": {"defaultValue": ""}}}]
            self.assertEqual(run(plan, sidecar, emit_connection=False)[0], 0, key)

    def test_rejects_solution_folder_as_folderpath_default(self):
        """`folderPath: "solution_folder"` passes validate and fails at invocation
        with 'folder not exist' (bindings-v2-sync.md)."""
        key = "solution_folder.Ops"
        plan = caseplan(bindings=[
            binding("name", "Ops", key=key), binding("folderPath", "solution_folder", key=key),
        ], connector=False)
        sidecar = [{"resource": "process", "key": key, "value": {
            "name": {"defaultValue": "Ops"},
            "folderPath": {"defaultValue": "solution_folder"}}}]
        code, out = run(plan, sidecar, emit_connection=False)
        self.assertEqual(code, 1)
        self.assertIn("folder not exist", out)

    def test_rejects_mismatched_resource_key_pair(self):
        """A pair whose two bindings carry different resourceKeys is the exact
        Check 11 failure, and split into two half-keys it was invisible."""
        plan = caseplan(bindings=[
            binding("name", "Ops", key="Shared.Ops"),
            binding("folderPath", "Shared", key="Shared/Other.Ops"),
        ], connector=False)
        sidecar = [{"resource": "process", "key": k, "value": {
            "name": {"defaultValue": "Ops"}, "folderPath": {"defaultValue": "Shared"}}}
            for k in ("Shared.Ops", "Shared/Other.Ops")]
        code, out = run(plan, sidecar, emit_connection=False)
        self.assertEqual(code, 1)
        self.assertIn("has no", out)

    def test_malformed_caseplan_does_not_crash(self):
        for bad in ("[]", "null", '"x"'):
            with tempfile.TemporaryDirectory() as tmp:
                proj = pathlib.Path(tmp) / "Sol" / "Proj"
                proj.mkdir(parents=True)
                (proj / "caseplan.json").write_text(bad)
                (proj / "bindings_v2.json").write_text('{"version":"2.0","resources":[]}')
                with self.assertRaises(SystemExit) as ctx:
                    audit_bindings.check(pathlib.Path(tmp) / "Sol", quiet=True)
                self.assertIn("not a JSON object", str(ctx.exception))

    def test_pins_folder_key_required_only_when_declared(self):
        """folderKey is omitted by contract when the connection has no folder, so
        require it only when the caseplan declared one."""
        plan = caseplan(bindings=[
            {"id": "c", "resource": "Connection", "resourceKey": CONN,
             "default": CONN, "propertyAttribute": "ConnectionId"},
            {"id": "f", "resource": "Connection", "resourceKey": CONN,
             "default": "FK", "propertyAttribute": "folderKey"},
        ], connector=False)
        sidecar = [{"resource": "Connection", "key": CONN,
                    "value": {"connectionId": {"defaultValue": CONN}}}]
        code, out = run(plan, sidecar, emit_connection=False)
        self.assertEqual(code, 1)
        self.assertIn("value.folderKey.defaultValue", out)

    def test_pins_uppercase_connectionid_casing_bug(self):
        plan = caseplan(bindings=[
            {"id": "c", "resource": "Connection", "resourceKey": CONN,
             "default": CONN, "propertyAttribute": "ConnectionId"}], connector=False)
        sidecar = [{"resource": "Connection", "key": CONN,
                    "value": {"ConnectionId": {"defaultValue": CONN}}}]
        code, out = run(plan, sidecar, emit_connection=False)
        self.assertEqual(code, 1)
        self.assertIn("uppercase C", out)

    def test_pins_absent_sidecar(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = pathlib.Path(tmp) / "Sol" / "Proj"
            proj.mkdir(parents=True)
            (proj / "caseplan.json").write_text(json.dumps(caseplan()))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = audit_bindings.check(pathlib.Path(tmp) / "Sol", quiet=True)
            self.assertEqual(code, 1)
            self.assertIn("bindings_v2.json is absent", buf.getvalue())

    def test_pins_stale_sidecar_entry(self):
        plan = caseplan(bindings=[binding("name", "OpsApi"), binding("folderPath", FOLDER)],
                        connector=False)
        sidecar = [CORRECT_SIDECAR[0], {"resource": "process", "key": "Ghost.Thing",
                   "value": {"name": {"defaultValue": "Thing"},
                             "folderPath": {"defaultValue": "Ghost"}}}]
        code, out = run(plan, sidecar, emit_connection=False)
        self.assertEqual(code, 1)
        self.assertIn("stale sidecar entries", out)

    def test_property_attribute_casing_does_not_evade(self):
        """A `Name`/`FolderPath` casing typo must not slip past Check 11."""
        plan = caseplan(bindings=[
            {"id": "a", "resource": "process", "resourceKey": "WRONG",
             "default": "OpsApi", "propertyAttribute": "Name"},
            {"id": "b", "resource": "process", "resourceKey": "WRONG",
             "default": FOLDER, "propertyAttribute": "FolderPath"},
        ], connector=False)
        sidecar = [{"resource": "process", "key": "WRONG", "value": {
            "name": {"defaultValue": "OpsApi"}, "folderPath": {"defaultValue": FOLDER}}}]
        code, out = run(plan, sidecar, emit_connection=False)
        self.assertEqual(code, 1)
        self.assertIn("not self-consistent", out)

    def test_skips_non_case_solution(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(audit_bindings.check(tmp, quiet=True), 2)

if __name__ == "__main__":
    unittest.main()
