#!/usr/bin/env python3
"""Verify the inspect-only deliverables for the three complex imported fixtures.

Inspect-only: the agent must (1) leave fixtures unmodified, and (2) produce an
inspection report that names content only knowable by reading each fixture
(process ids, distinctive element ids/tokens). This guards against agents that
ship a stub report containing only the fixture folder names.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import NS  # noqa: E402

EXPECTED_SIGNATURES = {
    "fixtures/validation/gateway-boundary-error/gateway-boundary-error.bpmn": {
        "process_id": "Process_GatewayBoundary",
        "elements": ("exclusiveGateway", "boundaryEvent", "serviceTask"),
        "uipath_tokens": ("Orchestrator.StartJob",),
        "report_tokens": ("Process_GatewayBoundary", "Error_ServiceUnavailable"),
    },
    "fixtures/validation/integration-service-enriched/integration-service-enriched.bpmn": {
        "process_id": "Process_IntegrationService",
        "elements": ("startEvent", "serviceTask"),
        "uipath_tokens": ("Intsvc.EventTrigger", "Intsvc.ActivityExecution"),
        "report_tokens": ("Process_IntegrationService", "Intsvc."),
    },
    "fixtures/validation/subprocess-multi-instance/subprocess-multi-instance.bpmn": {
        "process_id": "Process_SubprocessMultiInstance",
        "elements": ("subProcess", "scriptTask", "intermediateCatchEvent"),
        "uipath_tokens": ("Maestro.ReceiveMessageEvent", "BPMN.Variables"),
        "report_tokens": ("Process_SubprocessMultiInstance", "multiInstance"),
    },
}


def main() -> None:
    failures: list[str] = []
    for rel, signature in EXPECTED_SIGNATURES.items():
        path = Path(rel)
        if not path.exists():
            failures.append(f"{rel}: fixture missing")
            continue
        try:
            tree = ET.parse(path)
        except ET.ParseError as exc:
            failures.append(f"{rel}: not well-formed XML ({exc})")
            continue
        root = tree.getroot()
        process = root.find("bpmn:process", NS)
        if process is None or process.attrib.get("id") != signature["process_id"]:
            failures.append(f"{rel}: process id changed; expected {signature['process_id']!r}")
            continue
        for kind in signature["elements"]:
            if not root.findall(f".//bpmn:{kind}", NS):
                failures.append(f"{rel}: expected bpmn:{kind} no longer present")
        body = ET.tostring(root, encoding="unicode")
        for token in signature["uipath_tokens"]:
            if token not in body:
                failures.append(f"{rel}: expected uipath token {token!r} no longer present")

    report = Path("inspection-report.md")
    if not report.exists():
        failures.append("inspection-report.md missing")
    else:
        report_text = report.read_text(encoding="utf-8", errors="ignore")
        for rel, signature in EXPECTED_SIGNATURES.items():
            for token in signature["report_tokens"]:
                if token not in report_text:
                    failures.append(
                        f"inspection-report.md missing fixture-specific token {token!r} "
                        f"from {Path(rel).name}"
                    )

    if failures:
        sys.exit(
            "FAIL: imported fixture inspection drift detected:\n  - " + "\n  - ".join(failures)
        )
    print(
        f"OK: {len(EXPECTED_SIGNATURES)} imported fixtures intact and inspection report covers each"
    )


if __name__ == "__main__":
    main()
