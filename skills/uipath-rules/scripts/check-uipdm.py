#!/usr/bin/env python3
"""Check every uipdm element of a .dmn against uipdm.xsd with xmllint.

Usage: check-uipdm.py <DMN_FILE> [<XSD_FILE>]
Exit 0: all elements valid (or none present). Exit 1: at least one invalid element. Exit 2: usage error,
unreadable file, or xmllint not installed.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = "http://uipath.com/schema/1.0/dmn-ext/decision-model"
# Children are checked through their parent element.
CHILDREN = {"sourceRef", "constraint", "member", "annotation"}


def main(argv):
    if len(argv) not in (2, 3):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    dmn = Path(argv[1])
    xsd = Path(argv[2]) if len(argv) == 3 else Path(__file__).resolve().parent.parent / "references" / "uipdm.xsd"
    if not dmn.is_file() or not xsd.is_file():
        print(f"error: cannot read {dmn if not dmn.is_file() else xsd}", file=sys.stderr)
        return 2
    if shutil.which("xmllint") is None:
        print("error: xmllint is not installed", file=sys.stderr)
        return 2
    try:
        root = ET.parse(dmn).getroot()
    except ET.ParseError as err:
        print(f"error: {dmn} is not well-formed XML: {err}", file=sys.stderr)
        return 2
    checked = bad = 0
    for el in root.iter():
        if not el.tag.startswith("{%s}" % NS) or el.tag.split("}")[1] in CHILDREN:
            continue
        with tempfile.NamedTemporaryFile("wb", suffix=".xml", delete=False) as handle:
            handle.write(ET.tostring(el))
        result = subprocess.run(["xmllint", "--noout", "--schema", str(xsd), handle.name], capture_output=True, text=True)
        os.unlink(handle.name)
        checked += 1
        if result.returncode:
            bad += 1
            print(f"{el.tag.split('}')[1]}: {result.stderr.strip()}")
    print(f"{checked} uipdm elements checked, {bad} invalid")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
