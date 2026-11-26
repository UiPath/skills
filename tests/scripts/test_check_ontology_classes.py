"""Tests for the offline `classes`, `relates`, `depends` and `fieldtype` checks of the ontology task grader (check_ontology.py).

The check reads `<WORKDIR>/<NAME>.ofn` offline: every expected class is
declared, and every declared class has rdfs:label, rdfs:comment and at least
one property whose domain it is.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GRADER = ROOT / "tests/tasks/uipath-ontology/_shared/check_ontology.py"
GOLDEN = ROOT / "tests/tasks/uipath-ontology/_shared/fixtures/orders-golden/orders.ofn"


def run_classes(tmp_path: Path, schema: str | None, *args: str) -> subprocess.CompletedProcess:
    workdir = tmp_path / "orders"
    workdir.mkdir()
    if schema is not None:
        (workdir / "orders.ofn").write_text(schema)
    return subprocess.run([sys.executable, "-I", str(GRADER), "classes", str(workdir), "orders", *args],
                          text=True, capture_output=True)


def golden() -> str:
    return GOLDEN.read_text()


def test_golden_schema_declares_the_expected_classes(tmp_path):
    result = run_classes(tmp_path, golden(), "SalesOrder", "Customer")
    assert result.returncode == 0, result.stdout
    assert "OK: 2 classes" in result.stdout


def test_exact_count_passes_for_the_golden_schema(tmp_path):
    result = run_classes(tmp_path, golden(), "--count", "2")
    assert result.returncode == 0, result.stdout


def test_a_class_only_named_in_text_is_not_declared(tmp_path):
    schema = golden().replace("Declaration(Class(:Customer))\n", "")
    result = run_classes(tmp_path, schema, "SalesOrder", "Customer")
    assert result.returncode == 1
    assert "Customer is not declared" in result.stdout


def test_a_class_without_a_comment_fails(tmp_path):
    schema = "\n".join(line for line in golden().splitlines()
                       if not line.startswith("AnnotationAssertion(rdfs:comment :Customer "))
    result = run_classes(tmp_path, schema, "SalesOrder", "Customer")
    assert result.returncode == 1
    assert "Customer has no rdfs:comment" in result.stdout


def test_a_class_without_a_label_fails(tmp_path):
    schema = "\n".join(line for line in golden().splitlines()
                       if not line.startswith("AnnotationAssertion(rdfs:label :SalesOrder "))
    result = run_classes(tmp_path, schema, "SalesOrder", "Customer")
    assert result.returncode == 1
    assert "SalesOrder has no rdfs:label" in result.stdout


def test_a_class_that_is_no_property_domain_fails(tmp_path):
    schema = golden() + "\nDeclaration(Class(:Invoice))\n" \
        'AnnotationAssertion(rdfs:label :Invoice "Invoice")\n' \
        'AnnotationAssertion(rdfs:comment :Invoice "ONE row per invoice.")\n'
    result = run_classes(tmp_path, schema)
    assert result.returncode == 1
    assert "Invoice is not the domain of any property" in result.stdout


def test_a_wrong_class_count_fails(tmp_path):
    result = run_classes(tmp_path, golden(), "--count", "3")
    assert result.returncode == 1
    assert "expected 3 classes, found 2" in result.stdout


def test_full_iri_declarations_count(tmp_path):
    schema = golden().replace("Declaration(Class(:Customer))",
                              "Declaration( Class( <https://ontology.uipath.com/orders#Customer> ) )")
    result = run_classes(tmp_path, schema, "SalesOrder", "Customer")
    assert result.returncode == 0, result.stdout


def test_a_missing_schema_fails(tmp_path):
    result = run_classes(tmp_path, None, "SalesOrder")
    assert result.returncode == 1
    assert "orders.ofn does not exist" in result.stdout


# --- `relates`: native entity resources and their entity dependencies, read offline --------------------

def write_entity(solution: Path, name: str, *targets: str) -> None:
    folder = solution / "resources/solution_folder/entity/native"
    folder.mkdir(parents=True, exist_ok=True)
    deps = [{"kind": "Entity", "name": t} for t in targets]
    (folder / f"{name}.json").write_text(json.dumps({"resource": {"name": name, "dependencies": deps}}))


def run_relates(solution: Path, *pairs: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-I", str(GRADER), "relates", str(solution), *pairs],
                          text=True, capture_output=True)


def test_relates_passes_when_one_entity_depends_on_another(tmp_path):
    write_entity(tmp_path, "SalesOrder", "Customer")
    write_entity(tmp_path, "Customer")
    result = run_relates(tmp_path)
    assert result.returncode == 0, result.stdout
    assert "SalesOrder->Customer" in result.stdout


def test_relates_fails_when_no_entity_depends_on_another(tmp_path):
    write_entity(tmp_path, "SalesOrder")
    write_entity(tmp_path, "Customer")
    result = run_relates(tmp_path)
    assert result.returncode == 1
    assert "no native entity depends on another" in result.stdout


def test_relates_checks_each_named_pair(tmp_path):
    write_entity(tmp_path, "WorkOrder", "Asset")
    write_entity(tmp_path, "Asset")
    write_entity(tmp_path, "Technician")
    assert run_relates(tmp_path, "WorkOrder:Asset").returncode == 0
    missing = run_relates(tmp_path, "WorkOrder:Asset", "WorkOrder:Technician")
    assert missing.returncode == 1
    assert "WorkOrder does not depend on Technician" in missing.stdout


def test_relates_fails_without_native_entities(tmp_path):
    result = run_relates(tmp_path)
    assert result.returncode == 1
    assert "no local native entity" in result.stdout


# --- `depends` and `fieldtype`: one built native entity, read offline ------------------------------------

def write_built_entity(solution: Path, name: str, deps: list[tuple[str, str]], fields: dict[str, str]) -> None:
    folder = solution / "resources/solution_folder/entity/native"
    folder.mkdir(parents=True, exist_ok=True)
    resource_json = json.dumps({"Fields": [{"Name": n, "FieldDisplayType": t} for n, t in fields.items()]})
    (folder / f"{name}.json").write_text(json.dumps({"resource": {
        "name": name,
        "dependencies": [{"kind": k, "name": n} for k, n in deps],
        "spec": {"resourceJson": resource_json},
    }}))


def run_check(command: str, solution: Path, entity: str, *items: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-I", str(GRADER), command, str(solution), entity, *items],
                          text=True, capture_output=True)


def test_depends_matches_kind_and_name(tmp_path):
    write_built_entity(tmp_path, "WorkOrder", [("ChoiceSet", "WorkOrderPriority"), ("Entity", "Asset")], {})
    assert run_check("depends", tmp_path, "WorkOrder", "ChoiceSet:WorkOrderPriority", "Entity:Asset").returncode == 0
    wrong_kind = run_check("depends", tmp_path, "WorkOrder", "Entity:WorkOrderPriority")
    assert wrong_kind.returncode == 1
    assert "WorkOrder does not depend on Entity:WorkOrderPriority" in wrong_kind.stdout


def test_depends_fails_for_a_missing_entity(tmp_path):
    result = run_check("depends", tmp_path, "WorkOrder", "ChoiceSet:WorkOrderPriority")
    assert result.returncode == 1
    assert "WorkOrder is not a local native entity" in result.stdout


def test_fieldtype_reads_the_built_display_type(tmp_path):
    write_built_entity(tmp_path, "Asset", [], {"manual": "File", "assetTag": "Basic"})
    assert run_check("fieldtype", tmp_path, "Asset", "manual:File").returncode == 0
    wrong = run_check("fieldtype", tmp_path, "Asset", "assetTag:File")
    assert wrong.returncode == 1
    assert "Asset.assetTag has display type Basic, expected File" in wrong.stdout


def test_fieldtype_fails_for_a_missing_field(tmp_path):
    write_built_entity(tmp_path, "Asset", [], {"assetTag": "Basic"})
    result = run_check("fieldtype", tmp_path, "Asset", "manual:File")
    assert result.returncode == 1
    assert "Asset has no field manual" in result.stdout
