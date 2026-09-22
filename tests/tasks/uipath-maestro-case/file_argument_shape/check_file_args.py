#!/usr/bin/env python3
"""SupplierIntake: are the file arguments' trigger entries still argument-shaped?

An In argument's entry on the trigger holds id, name, type and elementId. The formal
slot in `variables.inputs[]` carries its default, and `custom` marks case-root state,
so neither key belongs on the trigger entry. The one case-root file Variable is the
control: it must keep its string default, `custom: true` and `elementId: "root"`, so a
build that strips every file entry bare does not pass either.

Read-only. Exit 0 clean, 1 on findings.
"""

from __future__ import annotations

import json
import sys

PLAN = "SupplierIntake/SupplierIntake/caseplan.json"
ARGUMENTS = ("registrationCertificate", "insuranceDocument", "taxFormsDocument")
ROOT_VARIABLE = "signedContract"


def main() -> int:
    try:
        with open(PLAN, encoding="utf-8") as handle:
            plan = json.load(handle)
    except (OSError, ValueError) as exc:
        print(f"FAIL: cannot read {PLAN}: {exc}", file=sys.stderr)
        return 1

    entries = (plan.get("variables") or {}).get("inputOutputs") or []
    by_name: dict[str, list[dict]] = {}
    for entry in entries:
        if isinstance(entry, dict):
            by_name.setdefault(str(entry.get("name")), []).append(entry)

    findings: list[str] = []
    for name in ARGUMENTS:
        on_trigger = [e for e in by_name.get(name, []) if e.get("elementId") != "root"]
        if not on_trigger:
            findings.append(f"'{name}' has no entry on the trigger; the argument lost its trigger half")
        for entry in on_trigger:
            for key in ("default", "custom"):
                if key in entry:
                    findings.append(f"'{name}' on {entry.get('elementId')!r} carries {key}={entry[key]!r}")

    roots = [e for e in by_name.get(ROOT_VARIABLE, []) if e.get("elementId") == "root"]
    if len(roots) != 1:
        findings.append(f"'{ROOT_VARIABLE}' should be one case-root entry, found {len(roots)}")
    else:
        root = roots[0]
        if not isinstance(root.get("default"), str):
            findings.append(f"'{ROOT_VARIABLE}' default is {root.get('default')!r}, not a string")
        if root.get("custom") is not True:
            findings.append(f"'{ROOT_VARIABLE}' custom is {root.get('custom')!r}, not true")

    print(f"checked {PLAN}")
    if findings:
        print(f"FAIL: {len(findings)} finding(s):", file=sys.stderr)
        for line in findings:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print("OK: three trigger entries carry neither default nor custom; the root Variable keeps both")
    return 0


if __name__ == "__main__":
    sys.exit(main())
