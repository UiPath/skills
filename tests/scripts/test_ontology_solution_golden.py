#!/usr/bin/env python3
"""Golden path: the uipath-ontology-modeler flow, CLI only, for an Order/Customer ontology.

Mirrors skills/uipath-ontology-modeler/SKILL.md: solution init, local entities, artifacts check,
entities, artifacts check, ont create, files add, validate, pack, files list --package. Needs a `uip` build that has the
`ont` local commands (the feat/ontologies-tool branch of ~/code/cli). Set UIP_CLI to that build:
either an executable or a JS entry point (run with node):

    UIP_CLI=~/code/cli/packages/cli/dist/index.js python3 -m unittest tests/scripts/test_ontology_solution_golden.py -v

The test skips when UIP_CLI is unset or the build lacks `ont create`. It validates with
`--offline` because it must not need a login; the skill itself never validates offline.
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "tasks" / "uipath-ontology-modeler" / "_shared" / "fixtures" / "orders-golden"
UIP_CLI = os.environ.get("UIP_CLI")

NAME = "orders"
ONTOLOGY = NAME
ENTITIES = ("Order", "Customer")
# file name -> (media type, artifact type)
ARTIFACTS = {
    "orders.ofn": ("text/owl-functional", "schema"),
    "orders-constraints.ttl": ("text/turtle", "constraints"),
    "orders-mapping.yarrrml.yml": ("application/yaml", "mapping"),
    "orders-summary.json": ("application/json", "summary"),
    "orders-context.json": ("application/json", "context"),
}


def cli_command() -> list[str]:
    if not UIP_CLI:
        return []
    path = os.path.expanduser(UIP_CLI)
    return ["node", path] if path.endswith((".js", ".mjs", ".cjs")) else [path]


def cli_skip_reason() -> str | None:
    if not UIP_CLI:
        return "UIP_CLI is not set: point it at a uip build that has the local `ont` commands"
    try:
        probe = subprocess.run([*cli_command(), "ont", "create", "--help"], text=True, capture_output=True,
                               timeout=60)
    except (OSError, subprocess.TimeoutExpired) as error:
        return f"UIP_CLI cannot run: {error}"
    if probe.returncode != 0:
        return f"`$UIP_CLI ont create --help` failed (exit {probe.returncode}): this uip build has no `ont create`"
    return None


SKIP_REASON = cli_skip_reason()


@unittest.skipIf(SKIP_REASON, SKIP_REASON or "")
class OntologySolutionGoldenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cli_home = Path(tempfile.mkdtemp(prefix="uip-golden-home-"))
        cls.addClassCleanup(shutil.rmtree, cls.cli_home, ignore_errors=True)

    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="uip-golden-"))
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)

    def cli_env(self) -> dict:
        # A throwaway HOME keeps the CLI logged out; the offline validation needs no tenant.
        home = str(self.cli_home)
        return {**os.environ, "HOME": home, "USERPROFILE": home,
                "UIPATH_CLI_ENABLE_ENV_AUTH": "false", "UIPATH_CLI_ENFORCE_ROBOT_AUTH": "false"}

    def run_cli(self, *args: str, cwd: Path) -> dict:
        result = subprocess.run([*cli_command(), *args, "--output", "json"], text=True, capture_output=True,
                                cwd=cwd, env=self.cli_env())
        detail = f"uip {' '.join(args)}\nexit={result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            self.fail(f"non-JSON output from {detail}")
        self.assertEqual(payload.get("Result"), "Success", detail)
        return payload

    def test_order_customer_flow_to_packed_solution(self):
        workdir = self.base / NAME
        shutil.copytree(FIXTURE, workdir)
        solution = self.base / "OrdersModel"

        # Step 4: solution from its parent folder.
        self.run_cli("solution", "init", solution.name, cwd=self.base)
        self.assertTrue(any(solution.glob("*.uipx")))

        # Step 4: local entities, run from the solution folder (no --solution-folder flag).
        for entity in ENTITIES:
            body = (workdir / "input" / "entities" / f"{entity}.json").read_text()
            self.run_cli("df", "entities", "create", entity, "--local", cwd=solution)
            self.run_cli("df", "entities", "update", entity, "--local", "--body", body, cwd=solution)
        self.assertIn("customerId", (workdir / "input" / "entities" / "Order.json").read_text())

        # Step 3: offline convention check of every artifact.
        for file_name, (media_type, artifact_type) in ARTIFACTS.items():
            self.run_cli("ont", "artifacts", "check", file_name, "--content-type", media_type, "--type",
                         artifact_type, "--file", str(workdir / file_name), cwd=self.base)

        # Step 5: ontology resource, then its files; every file is reported as Added.
        folder = ("--solution-folder", str(solution))
        entity_flags = [flag for entity in ENTITIES for flag in ("--entity", entity)]
        self.run_cli("ont", "create", ONTOLOGY, "--local", *entity_flags, *folder, cwd=self.base)
        added = self.run_cli("ont", "files", "add", ONTOLOGY, *(str(workdir / name) for name in ARTIFACTS),
                             "--local", *folder, cwd=self.base)
        self.assertEqual({entry["fileName"]: entry["status"] for entry in added["Data"]["files"]},
                         {name: "Added" for name in ARTIFACTS})

        # Step 6, test only: offline validation (the skill validates with the service).
        validated = self.run_cli("ont", "validate", "--local", "--offline", *folder, cwd=self.base)
        self.assertEqual(len(validated["Data"]), 1, validated["Data"])
        self.assertIs(validated["Data"][0]["valid"], True, validated["Data"])
        self.assertEqual(validated["Data"][0]["ServiceValidation"], "Skipped")

        # Step 7: dry run, then pack.
        out = solution / "out"
        self.run_cli("solution", "pack", str(solution), str(out), "--dry-run", cwd=self.base)
        self.run_cli("solution", "pack", str(solution), str(out), cwd=self.base)
        packages = list(out.glob("*.zip"))
        self.assertEqual(len(packages), 1, list(out.iterdir()) if out.exists() else "no out dir")

        # The packed listing is exactly the fixture's artifacts, with their types (never ontology.json).
        listed = self.run_cli("ont", "files", "list", ONTOLOGY, "--package", str(packages[0]), cwd=self.base)
        packed = {entry["fileName"]: entry["type"] for entry in listed["Data"]["artifacts"]}
        self.assertEqual(packed, {name: artifact_type for name, (_, artifact_type) in ARTIFACTS.items()})


if __name__ == "__main__":
    unittest.main()
