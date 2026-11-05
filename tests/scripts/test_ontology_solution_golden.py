#!/usr/bin/env python3
"""Golden path: the uipath-ontology-modeler flow, CLI only, for a SalesOrder/Customer ontology.

Follows skills/uipath-ontology-modeler/SKILL.md stage by stage: login status, solution init, the
local choice set and its values, the native entities (a RELATIONSHIP and a CHOICE_SET_SINGLE field),
a federated entity over a local native entity, entities validate, artifacts check, ont create,
files add, validate (with the XF-019 fix loop), pack, files list --package, then the packed
resources and their dependencies[].

Set UIP_CLI to a uip build that has the local `ont` and `uip df … --local` commands: either an
executable or a JS entry point (run with node).

    UIP_CLI=<cli>/packages/cli/dist/index.js python3 -m pytest tests/scripts/test_ontology_solution_golden.py -q -rs

The CLI runs with the caller's login: validation always calls the ontology service. When the
service cannot validate (ServiceValidationUnavailable or ServiceValidationFailed), the test still
asserts every local result and the packed solution, then reports a skip with the service's answer.

`uip ont create` needs the `ontology` resource kind in the Automation Solutions metadata the CLI
reads from the tenant. Where that tenant does not declare it yet, the test skips at that step;
set UIP_GOLDEN_EMBEDDED_METADATA=1 to make the CLI fall back to the metadata it embeds (the test
blocks only the tenant metadata request; every other call is unchanged).
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "tasks" / "uipath-ontology-modeler" / "_shared" / "fixtures" / "orders-golden"
UIP_CLI = os.environ.get("UIP_CLI")
EMBEDDED_METADATA = os.environ.get("UIP_GOLDEN_EMBEDDED_METADATA") == "1"

NAME = "orders"
CHOICE_SET = "OrderStatus"
CHOICE_SET_DISPLAY_NAME = "Order status"
CHOICE_SET_VALUES = ("Open", "Shipped", "Cancelled")
NATIVE_ENTITIES = ("Customer", "SalesOrder")  # dependency order: the referenced entity first
FEDERATED_ENTITY = "CustomerDirectory"
# file name -> (media type, artifact type)
ARTIFACTS = {
    "orders.ofn": ("text/owl-functional", "schema"),
    "orders-constraints.ttl": ("text/turtle", "constraints"),
    "orders-mapping.yarrrml.yml": ("application/yaml", "mapping"),
    "orders-summary.json": ("application/json", "summary"),
    "orders-context.json": ("application/json", "context"),
}
SERVICE_UNAVAILABLE = ("ServiceValidationUnavailable", "ServiceValidationFailed")
METADATA_BLOCK = """\
const realFetch = globalThis.fetch;
globalThis.fetch = (input, init) => {
  const url = typeof input === "string" ? input : (input && input.url) || String(input);
  if (url.includes("/automationsolutions_/api/metadata")) {
    return Promise.reject(new TypeError("fetch failed: tenant metadata blocked by the golden test"));
  }
  return realFetch(input, init);
};
"""


def cli_command() -> list[str]:
    if not UIP_CLI:
        return []
    path = os.path.expanduser(UIP_CLI)
    return ["node", path] if path.endswith((".js", ".mjs", ".cjs")) else [path]


def cli_env(extra: dict | None = None) -> dict:
    # The daily tool update check would replace (or, for an unpublished tool, refuse) the build under test.
    return {**os.environ, "UIPATH_CLI_DISABLE_VERSION_SYNC": "1", **(extra or {})}


def cli_skip_reason() -> str | None:
    if not UIP_CLI:
        return "UIP_CLI is not set: point it at a uip build that has the local `ont` commands"
    try:
        probe = subprocess.run([*cli_command(), "ont", "create", "--help"], text=True, capture_output=True,
                               timeout=60, env=cli_env())
    except (OSError, subprocess.TimeoutExpired) as error:
        return f"UIP_CLI cannot run: {error}"
    if probe.returncode != 0:
        return f"`$UIP_CLI ont create --help` failed (exit {probe.returncode}): this uip build has no `ont create`"
    return None


SKIP_REASON = cli_skip_reason()


def key(data: dict, name: str):
    """A key of a CLI envelope: success envelopes are PascalCased, a failure's Data keeps lower case."""
    for candidate in (name, name[:1].upper() + name[1:], name[:1].lower() + name[1:]):
        if candidate in data:
            return data[candidate]
    raise KeyError(f"{name} not in {sorted(data)}")


def errors(violations: list[dict]) -> list[dict]:
    return [v for v in violations if key(v, "severity") == "ERROR"]


@unittest.skipIf(SKIP_REASON, SKIP_REASON or "")
class OntologySolutionGoldenTest(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="uip-golden-"))
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)
        self.env = cli_env()
        if EMBEDDED_METADATA:
            hook = self.base / "block-tenant-metadata.cjs"
            hook.write_text(METADATA_BLOCK)
            options = f"{os.environ.get('NODE_OPTIONS', '')} --require {hook}".strip()
            self.env = cli_env({"NODE_OPTIONS": options})

    def invoke(self, *args: str, cwd: Path) -> tuple[dict, str]:
        result = subprocess.run([*cli_command(), *args, "--output", "json"], text=True, capture_output=True,
                                cwd=cwd, env=self.env)
        detail = f"uip {' '.join(args)}\nexit={result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        try:
            return json.loads(result.stdout), detail
        except json.JSONDecodeError:
            self.fail(f"non-JSON output from {detail}")

    def run_cli(self, *args: str, cwd: Path) -> dict:
        payload, detail = self.invoke(*args, cwd=cwd)
        self.assertEqual(payload.get("Result"), "Success", detail)
        return payload

    def fail_cli(self, *args: str, cwd: Path) -> dict:
        payload, detail = self.invoke(*args, cwd=cwd)
        self.assertEqual(payload.get("Result"), "Failure", detail)
        return payload

    def build_solution(self, *, federated_class: bool) -> tuple[Path, Path, list[str]]:
        """Stages 1–6. Returns (solution folder, WORKDIR, the ontology's entities)."""
        workdir = self.base / NAME
        shutil.copytree(FIXTURE, workdir, ignore=shutil.ignore_patterns("federated"))
        if federated_class:
            for file in (FIXTURE / "federated").iterdir():
                shutil.copy(file, workdir / file.name)
        solution = self.base / "OrdersModel"
        resources = solution / "resources" / "solution_folder"

        # Stage 1: sign-in state; only service validation below needs it.
        self.run_cli("login", "status", cwd=self.base)

        # Stage 3: the solution, from its parent folder.
        self.run_cli("solution", "init", solution.name, cwd=self.base)
        self.assertTrue(any(solution.glob("*.uipx")))

        # Stage 4: duplicate check, then the choice set and its values in order, from the solution folder.
        self.assertEqual(self.run_cli("df", "choice-sets", "list", "--local", cwd=solution)["Data"], [])
        self.assertEqual(self.run_cli("df", "entities", "list", "--local", cwd=solution)["Data"], [])
        self.run_cli("df", "choice-sets", "create", CHOICE_SET, "--local", "--display-name", CHOICE_SET_DISPLAY_NAME,
                     cwd=solution)
        for value in CHOICE_SET_VALUES:
            self.run_cli("df", "choice-set-values", "create", CHOICE_SET, value, "--local", cwd=solution)
        self.assertTrue((resources / "choiceSet" / f"{CHOICE_SET}.json").is_file())

        # Stage 4: native entities in dependency order, then the federated entity over the native Customer.
        definitions = workdir / "input" / "entities"
        for entity in NATIVE_ENTITIES:
            body = (definitions / f"{entity}.json").read_text()
            created = self.run_cli("df", "entities", "create", entity, "--local", "--body", body, cwd=solution)
            self.assertEqual(created["Data"]["Entity"], entity)
            self.assertTrue((solution / entity / "project.uiproj").is_file())
            self.assertTrue((solution / entity / f"{entity}.entity").is_file())
            self.assertTrue((resources / "entity" / "native" / f"{entity}.json").is_file())
        body = (definitions / f"{FEDERATED_ENTITY}.json").read_text()
        federated = self.run_cli("df", "entities", "create", FEDERATED_ENTITY, "--local", "--body", body, cwd=solution)
        self.assertIs(federated["Data"]["Federated"], True)
        self.assertTrue((resources / "entity" / "federated" / f"{FEDERATED_ENTITY}.json").is_file())
        self.assertFalse((solution / FEDERATED_ENTITY).exists(), "a federated entity has no Entity project")

        validated = self.run_cli("df", "entities", "validate", "--local", cwd=solution)["Data"]
        self.assertIs(validated["Valid"], True, validated)
        self.assertEqual(sorted(e["Entity"] for e in validated["Entities"]),
                         sorted((*NATIVE_ENTITIES, FEDERATED_ENTITY)))

        # Stage 5: the sh:in list is the choice set's value names, read back from the CLI.
        listed = self.run_cli("df", "choice-sets", "list-values", CHOICE_SET, "--local", cwd=solution)
        self.assertEqual(tuple(v["Name"] for v in listed["Data"]["Values"]), CHOICE_SET_VALUES)
        self.assertIn('sh:in ( "Open" "Shipped" "Cancelled" )', (workdir / "orders-constraints.ttl").read_text())

        # Stage 5: offline per-file check of every artifact; no ERROR and no WARNING.
        for file_name, (media_type, artifact_type) in ARTIFACTS.items():
            checked = self.run_cli("ont", "artifacts", "check", file_name, "--content-type", media_type, "--type",
                                   artifact_type, "--file", str(workdir / file_name), cwd=self.base)
            self.assertEqual(checked["Data"]["Violations"], [], file_name)

        # Stage 6: the ontology resource over its entities, then its files; every file is Added.
        entities = [*NATIVE_ENTITIES, *((FEDERATED_ENTITY,) if federated_class else ())]
        folder = ("--solution-folder", str(solution))
        entity_flags = [flag for entity in entities for flag in ("--entity", entity)]
        created = self.create_ontology(*entity_flags, *folder)
        self.assertEqual(created["Data"]["Entities"], entities)
        added = self.run_cli("ont", "files", "add", NAME, *(str(workdir / name) for name in ARTIFACTS),
                             "--local", *folder, cwd=self.base)
        self.assertEqual({entry["FileName"]: entry["Status"] for entry in added["Data"]["Files"]},
                         {name: "Added" for name in ARTIFACTS})
        return solution, workdir, entities

    def create_ontology(self, *args: str) -> dict:
        payload, detail = self.invoke("ont", "create", NAME, "--local", *args, cwd=self.base)
        if payload.get("Result") != "Success" and "Resource metadata not found for Kind: ontology" in str(
                payload.get("Instructions")):
            self.skipTest("the tenant's Automation Solutions metadata does not declare the `ontology` kind, so "
                          "`uip ont create` cannot run there; set UIP_GOLDEN_EMBEDDED_METADATA=1 to use the CLI's "
                          "embedded metadata")
        self.assertEqual(payload.get("Result"), "Success", detail)
        return payload

    def validate(self, solution: Path) -> tuple[dict, list[dict], str]:
        """Stage 7: the envelope, its entries and the call detail."""
        payload, detail = self.invoke("ont", "validate", "--local", "--solution-folder", str(solution), cwd=self.base)
        entries = payload.get("Data")
        self.assertIsInstance(entries, list, detail)
        self.assertEqual([key(e, "name") for e in entries], [NAME], detail)
        return payload, entries, detail

    def test_sales_order_flow_to_packed_solution(self):
        solution, workdir, entities = self.build_solution(federated_class=False)
        folder = ("--solution-folder", str(solution))

        # Stage 7 fix loop: a sh:in value outside the choice set is XF-019; replacing the file clears it.
        wrong = self.base / "wrong" / "orders-constraints.ttl"
        wrong.parent.mkdir()
        wrong.write_text((workdir / "orders-constraints.ttl").read_text().replace('"Cancelled"', '"Closed"'))
        self.run_cli("ont", "files", "add", NAME, str(wrong), "--local", *folder, cwd=self.base)
        failed = self.fail_cli("ont", "validate", "--local", *folder, cwd=self.base)
        self.assertEqual(failed["Code"], "ValidationFailed")
        rules = [(v["rule"], v.get("file")) for v in errors(failed["Data"][0]["violations"])]
        self.assertEqual(rules, [("XF-019", "orders-constraints.ttl")], failed["Data"])
        self.assertEqual(failed["Data"][0]["ServiceValidation"], "Skipped")  # no service call over a local ERROR
        replaced = self.run_cli("ont", "files", "add", NAME, str(workdir / "orders-constraints.ttl"), "--local",
                                *folder, cwd=self.base)
        self.assertEqual([entry["Status"] for entry in replaced["Data"]["Files"]], ["Replaced"])

        # Stage 7: clean locally (no ERROR, no WARNING); the service's verdict decides the skip at the end.
        payload, entries, detail = self.validate(solution)
        self.assertEqual(key(entries[0], "violations"), [], detail)
        service_unavailable = None
        if payload["Result"] == "Success":
            self.assertIs(key(entries[0], "valid"), True, detail)
            self.assertEqual(key(entries[0], "ServiceValidation"), "Done", detail)
        else:
            self.assertIn(payload.get("Code"), SERVICE_UNAVAILABLE, detail)
            service_unavailable = f"{payload['Code']}: {payload.get('Message')} ({payload.get('Instructions')})"

        # Stage 8: dry run, then pack.
        out = solution / "out"
        self.run_cli("solution", "pack", str(solution), str(out), "--dry-run", cwd=self.base)
        self.run_cli("solution", "pack", str(solution), str(out), cwd=self.base)
        packages = list(out.glob("*.zip"))
        self.assertEqual(len(packages), 1, list(out.iterdir()) if out.exists() else "no out dir")

        # The packed listing is exactly the fixture's artifacts, with their types (never ontology.json).
        listed = self.run_cli("ont", "files", "list", NAME, "--package", str(packages[0]), cwd=self.base)
        packed = {entry["FileName"]: entry["Type"] for entry in listed["Data"]["Artifacts"]}
        self.assertEqual(packed, {name: artifact_type for name, (_, artifact_type) in ARTIFACTS.items()})

        # The package holds the ontology zip, the choice set, both native entities and the federated entity.
        with zipfile.ZipFile(packages[0]) as package:
            names = set(package.namelist())
            resource = lambda path: json.loads(package.read(f"resources/solution_folder/{path}"))["resource"]
            ontology = resource(f"ontology/{NAME}.json")
            choice_set = resource(f"choiceSet/{CHOICE_SET}.json")
            customer = resource("entity/native/Customer.json")
            sales_order = resource("entity/native/SalesOrder.json")
            directory = resource(f"entity/federated/{FEDERATED_ENTITY}.json")
        attached = [f["name"] for f in ontology["files"] if f["kind"] == "ontology"]
        self.assertEqual(len(attached), 1, ontology["files"])
        self.assertTrue(any(n.startswith("files/") and n.endswith(f"/{attached[0]}") for n in names), sorted(names))
        self.assertEqual((choice_set["kind"], customer["type"], sales_order["type"], directory["type"]),
                         ("choiceSet", "native", "native", "federated"))

        # The CLI writes an entity's dependency kinds as Entity/ChoiceSet and the ontology's as entity.
        deps = lambda r: sorted((d["kind"].lower(), d["name"]) for d in r["dependencies"])
        self.assertEqual(deps(sales_order), [("choiceset", CHOICE_SET), ("entity", "Customer")])
        self.assertEqual(deps(directory), [("entity", "Customer")])
        self.assertEqual(deps(customer), [])
        self.assertEqual(deps(choice_set), [])
        self.assertEqual(deps(ontology), sorted(("entity", e) for e in entities))

        if service_unavailable:
            self.skipTest(f"every local stage passed and the solution packed; the ontology service did not "
                          f"validate: {service_unavailable}")

    @unittest.expectedFailure
    def test_ontology_class_maps_a_federated_entity(self):
        # The skill maps a class over a federated entity by name (`table: <Entity>`). The CLI build under test
        # reads only Entity projects as the ontology's local entities, so a federated table fails XF-012. This
        # passes (and the expected failure turns red) once the CLI counts federated entities.
        solution, _, _ = self.build_solution(federated_class=True)
        _, entries, detail = self.validate(solution)
        self.assertEqual(errors(key(entries[0], "violations")), [], detail)


if __name__ == "__main__":
    unittest.main()
