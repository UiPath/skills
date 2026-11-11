"""Tests for the `classes` check of the ontology task grader (check_ontology.py).

The check reads `<WORKDIR>/<NAME>.ofn` offline: every expected class is
declared, and every declared class has rdfs:label, rdfs:comment and at least
one property whose domain it is.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GRADER = ROOT / "tests/tasks/uipath-ontology-modeler/_shared/check_ontology.py"
GOLDEN = ROOT / "tests/tasks/uipath-ontology-modeler/_shared/fixtures/orders-golden/orders.ofn"


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
