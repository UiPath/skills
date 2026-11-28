"""Unit tests for skills/uipath-rules/scripts/check-uipdm.mjs. Run with ``pytest`` from any directory.

The checker implements the part of XML Schema that uipdm.xsd uses. Where xmllint is installed, every case
is also validated with xmllint against the same schema, so the two must agree.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
SKILL = REPO / "skills" / "uipath-rules"
SCRIPT = SKILL / "scripts" / "check-uipdm.mjs"
XSD = SKILL / "scripts" / "uipdm.xsd"
NS = "http://uipath.com/schema/1.0/dmn-ext/decision-model"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")

# (name, one uipdm element, valid?)
CASES = [
    ("page-only sourceRef", '<uipdm:sourceRefs><uipdm:sourceRef page="2"/></uipdm:sourceRefs>', True),
    ("boxed sourceRef", '<uipdm:sourceRefs><uipdm:sourceRef page="2" blockId="7" box="10,20.5,300,40"/></uipdm:sourceRefs>', True),
    ("two sourceRefs", '<uipdm:sourceRefs><uipdm:sourceRef page="1"/><uipdm:sourceRef page="2"/></uipdm:sourceRefs>', True),
    ("inputVariable with constraints",
     '<uipdm:inputVariable source="claim" sourceType="document" dataType="categorical">'
     "<uipdm:constraint>Laptop</uipdm:constraint><uipdm:constraint>Phone</uipdm:constraint></uipdm:inputVariable>", True),
    ("bare inputVariable", '<uipdm:inputVariable sourceType="system"/>', True),
    ("qualityWarning", '<uipdm:qualityWarning field="amount">More than 500 read as exclusive &amp; noted.</uipdm:qualityWarning>', True),
    ("empty qualityWarning", "<uipdm:qualityWarning/>", True),
    ("sourceRef without page", '<uipdm:sourceRefs><uipdm:sourceRef box="1,2,3,4"/></uipdm:sourceRefs>', False),
    ("three-number box", '<uipdm:sourceRefs><uipdm:sourceRef page="1" box="1,2,3"/></uipdm:sourceRefs>', False),
    ("non-integer page", '<uipdm:sourceRefs><uipdm:sourceRef page="one"/></uipdm:sourceRefs>', False),
    ("empty sourceRefs", "<uipdm:sourceRefs/>", False),
    ("DMN type name as dataType", '<uipdm:inputVariable sourceType="document" dataType="number"/>', False),
    ("unknown sourceType", '<uipdm:inputVariable sourceType="database"/>', False),
    ("unknown attribute", '<uipdm:inputVariable sourceType="document" origin="x"/>', False),
    ("unknown child", '<uipdm:inputVariable sourceType="document"><uipdm:value>1</uipdm:value></uipdm:inputVariable>', False),
    ("element the schema does not declare", '<uipdm:citation page="1"/>', False),
    ("child of qualityWarning", "<uipdm:qualityWarning><uipdm:constraint>x</uipdm:constraint></uipdm:qualityWarning>", False),
    ("review needs confirmed", "<uipdm:review/>", False),
    ("review with a boolean", '<uipdm:review confirmed="true"/>', True),
]


def dmn(*elements: str) -> str:
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<definitions xmlns="https://www.omg.org/spec/DMN/20230324/MODEL/" '
            f'xmlns:uipdm="{NS}" id="d" name="d" namespace="urn:x"><extensionElements>'
            + "".join(elements) + "</extensionElements></definitions>")


def run(text: str, *extra: str) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "rule.dmn"
        path.write_text(text, encoding="utf-8")
        return subprocess.run(["node", str(SCRIPT), str(path), *extra], capture_output=True, text=True)


@pytest.mark.parametrize("name, element, valid", CASES, ids=[c[0] for c in CASES])
def test_each_element_is_accepted_or_rejected(name, element, valid):
    result = run(dmn(element))
    assert result.returncode == (0 if valid else 1), result.stdout
    assert f"1 uipdm elements checked, {0 if valid else 1} invalid" in result.stdout


@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is not installed")
@pytest.mark.parametrize("name, element, valid", CASES, ids=[c[0] for c in CASES])
def test_the_verdict_matches_xmllint(name, element, valid):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "element.xml"
        path.write_text(element.replace(">", f' xmlns:uipdm="{NS}">', 1) if "/>" not in element.split(">")[0] + ">"
                        else element.replace("/>", f' xmlns:uipdm="{NS}"/>', 1), encoding="utf-8")
        lint = subprocess.run(["xmllint", "--noout", "--schema", str(XSD), str(path)], capture_output=True, text=True)
    assert (lint.returncode == 0) == valid, lint.stderr


def test_a_file_without_uipdm_elements_passes():
    result = run(dmn())
    assert result.returncode == 0 and "0 uipdm elements checked, 0 invalid" in result.stdout


def test_several_elements_are_counted_and_each_invalid_one_is_named():
    result = run(dmn(CASES[0][1], CASES[3][1], CASES[8][1], CASES[11][1]))
    assert result.returncode == 1
    assert "4 uipdm elements checked, 2 invalid" in result.stdout
    assert "box" in result.stdout and "dataType" in result.stdout


def test_usage_and_unreadable_files_exit_2():
    assert subprocess.run(["node", str(SCRIPT)], capture_output=True, text=True).returncode == 2
    assert subprocess.run(["node", str(SCRIPT), "/nonexistent.dmn"], capture_output=True, text=True).returncode == 2
    assert run("<definitions><unclosed></definitions>").returncode == 2


def test_an_unsupported_schema_construct_stops_instead_of_passing():
    with tempfile.TemporaryDirectory() as tmp:
        xsd = Path(tmp) / "other.xsd"
        xsd.write_text(XSD.read_text(encoding="utf-8").replace("</xsd:schema>",
                       '<xsd:complexType name="tX"><xsd:choice/></xsd:complexType></xsd:schema>'), encoding="utf-8")
        result = run(dmn(CASES[0][1]), str(xsd))
    assert result.returncode == 2 and "choice" in result.stdout


def test_the_schema_is_found_next_to_a_copied_script():
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(SCRIPT, Path(tmp) / "check-uipdm.mjs")
        shutil.copy(XSD, Path(tmp) / "uipdm.xsd")
        rule = Path(tmp) / "rule.dmn"
        rule.write_text(dmn(CASES[0][1]), encoding="utf-8")
        result = subprocess.run(["node", str(Path(tmp) / "check-uipdm.mjs"), str(rule)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout
