#!/usr/bin/env python3
"""Golden path: handoff + artifacts -> entities -> preflight -> local solution -> pack.

Follows the uipath-ontology-modeler skill's paths and command order exactly.

Build the CLI first (in ~/code/cli, so packages/cli/dist/index.js exists), then run:

    UIP_CLI=~/code/cli/packages/cli/dist/index.js \\
    UIP_SOLUTION_METADATA_OVERLAY=~/code/cli/packages/solution-tool/tests/fixtures/ontology/ontology.metadata.json \\
    python3 -m unittest tests/scripts/test_ontology_solution_golden.py -v
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "uipath-ontology-modeler" / "scripts"
FIXTURE = ROOT / "tests" / "tasks" / "uipath-ontology-modeler" / "_shared" / "fixtures" / "solution-golden"
UIP_CLI = os.environ.get("UIP_CLI")
OVERLAY = os.environ.get("UIP_SOLUTION_METADATA_OVERLAY")


@unittest.skipUnless(UIP_CLI and OVERLAY, "set UIP_CLI and UIP_SOLUTION_METADATA_OVERLAY to run")
class OntologySolutionGoldenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cli_home = Path(tempfile.mkdtemp(prefix="uip-golden-home-"))
        cls.addClassCleanup(shutil.rmtree, cls.cli_home, ignore_errors=True)

    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="uip-golden-"))
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)

    def cli_env(self) -> dict:
        # A throwaway HOME keeps the CLI logged out, so the Data Fabric inline-entity flag
        # check reports "unknown" (a warning) instead of querying a real tenant.
        home = str(self.cli_home)
        return {**os.environ, "HOME": home, "USERPROFILE": home,
                "UIPATH_CLI_ENABLE_ENV_AUTH": "false", "UIPATH_CLI_ENFORCE_ROBOT_AUTH": "false"}

    def run_cli(self, *args: str, cwd: Path, stdin: str | None = None) -> dict:
        result = subprocess.run(["node", UIP_CLI, *args, "--output", "json"], text=True, capture_output=True,
                                input=stdin, cwd=cwd, env=self.cli_env())
        detail = f"uip {' '.join(args)}\nexit={result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            self.fail(f"non-JSON output from {detail}")
        self.assertEqual(payload.get("Result"), "Success", detail)
        return payload

    def run_tool(self, tool: str, *args: str) -> dict:
        result = subprocess.run([sys.executable, str(SCRIPTS / tool), *args], text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0, payload)
        return payload

    def test_handoff_to_packed_solution(self):
        workdir = self.base / "sales"
        shutil.copytree(FIXTURE, workdir)
        entities = workdir / "entities"
        solution = self.base / "SalesModel"

        # Step 3: entity definitions.
        self.run_tool("ontology_entities.py", "--workdir", str(workdir))

        # Step 4: preflight gates, including WORKDIR/SOLUTION_DIR path validation.
        report = self.run_tool("ontology_preflight.py", "--workdir", str(workdir), "--ontology-name", "sales",
                               "--mapping-mode", "auto", "--solution-dir", str(solution))
        self.assertEqual(report["status"], "PASS", report["errors"])
        self.assertEqual(report["paths"]["solution_state"], "new")

        # Step 5.1: init from dirname(SOLUTION_DIR) with basename(SOLUTION_DIR).
        self.run_cli("solution", "init", solution.name, cwd=solution.parent)
        self.assertTrue(any(solution.glob("*.uipx")))
        folder = ("--solution-folder", str(solution))

        # Step 5.2: entities; keys come from Data.Key.
        entity_keys = {}
        for patch in sorted(entities.glob("*.patch.json")):
            name = patch.name[: -len(".patch.json")]
            entity_keys[name] = self.run_cli("solution", "resources", "add", "--source", "local", "--kind", "Entity",
                                             "--name", name, *folder, cwd=self.base)["Data"]["Key"]
            self.run_cli("solution", "resources", "edit", entity_keys[name], "--patch", "-", *folder,
                         cwd=self.base, stdin=patch.read_text())
        self.assertEqual(set(entity_keys), {"Order", "Customer"})

        # Steps 5.3 and 5.4: add the ontology, then link the entities before any file is attached.
        ontology = self.run_cli("solution", "resources", "add", "--source", "local", "--kind", "Ontology",
                                "--name", "sales", *folder, cwd=self.base)["Data"]["Key"]
        links = [arg for name in sorted(entity_keys) for arg in ("--add-entity", name)]
        self.run_cli("solution", "resources", "edit", ontology, *links, *folder, cwd=self.base)

        # Step 5.5: attach every file in artifact_inventory with its type.
        attached = 0
        for kind, names in report["artifact_inventory"].items():
            for name in names:
                self.run_cli("solution", "resources", "files", "add", ontology, "--file", str(workdir / name),
                             "--file-type", kind, *folder, cwd=self.base)
                attached += 1
        self.assertEqual(attached, 3)

        # Step 5.6: files list is clean.
        listed = self.run_cli("solution", "resources", "files", "list", ontology, *folder, cwd=self.base)
        self.assertEqual(listed["Data"]["Warnings"], [])

        # Step 6: pack into {SOLUTION_DIR}/out.
        out = solution / "out"
        self.run_cli("solution", "pack", str(solution), str(out), cwd=self.base)
        package = next(out.glob("*.zip"))
        with zipfile.ZipFile(package) as archive:
            names = archive.namelist()
            inner = [n for n in names if n.startswith("files/") and n.endswith(f"{ontology}.zip")]
            self.assertEqual(len(inner), 1, names)
            self.assertTrue(any(n.endswith("/entity/Order.json") for n in names), names)
            ontology_json = json.loads(archive.read(next(n for n in names if n.endswith("/ontology/sales.json"))))
            deps = {(d["kind"].lower(), d["name"]) for d in ontology_json["resource"]["dependencies"]}
            self.assertTrue({("entity", "Order"), ("entity", "Customer")} <= deps, deps)
            with zipfile.ZipFile(archive.open(inner[0])) as bundle:
                mapping = bundle.read("sales-mapping.yarrrml.yml").decode()
                self.assertIn("table: Order", mapping)
                self.assertNotIn("entityId", mapping)


if __name__ == "__main__":
    unittest.main()
