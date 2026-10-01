#!/usr/bin/env python3
"""Grade a live Automation Hub publish by reading the tenant back through `uip ah`.

The agent was given a PDD and a BPMN process map whose names carry this run's
token (seed.json). Each subcommand is one success criterion:

    process        exactly one process on the tenant carries the token
    fields         its record is grounded: token name, real description, category and submitter set
    applications   at least every PDD system the inventory already had is attached
    documents      the PDD is attached as type 1 and its stored bytes equal the staged file
    bpmn-layout    the stored process map renders: a BPMNDiagram with shapes (RPANAV-19062)

Outcome-graded: how the agent shaped the publish is not judged here — only what
ended up on the tenant. Exit 0 = pass; non-zero prints the first failing reason.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_setup"))
from ah_cli import (  # noqa: E402
    describe_failure,
    has_placeholder,
    items,
    load_seed,
    succeeded,
    uip_json,
)

OUTCOME_FILE = "outcome.json"
PDD_TYPE_ID = 1
PROCESS_MAP_TYPE_IDS = {6, 9}  # PM, or MISC when unsure (both allowed by the skill)
PDD_FIXTURE = "pdd-retail-account-onboarding.md"
MAP_FIXTURE = "process-map-retail-account-onboarding.bpmn"
# Systems the fixture PDD names; matched case-insensitively against inventory names.
PDD_SYSTEMS = ("microsoft dynamics 365", "signicat", "trapets", "scrive", "temenos t24")
BPMN_DI = "{http://www.omg.org/spec/BPMN/20100524/DI}"


class CheckFailed(Exception):
    pass


def our_process(seed: dict) -> dict:
    token = seed["run_token"]
    if os.path.exists(OUTCOME_FILE):
        with open(OUTCOME_FILE, encoding="utf-8") as handle:
            cached = json.load(handle)
        if cached.get("run_token") == token:
            return cached["process"]
    listing = uip_json(["ah", "automations", "list", "--search", token, "--limit", "50"])
    if not succeeded(listing):
        raise CheckFailed(f"automations list --search failed: {describe_failure(listing)}")
    ours = [p for p in items(listing) if token in str(p.get("Name", ""))]
    if len(ours) != 1:
        raise CheckFailed(f"expected exactly one process named with {token}, found {len(ours)}: "
                          + ", ".join(f"{p.get('Id')}:{p.get('Name')}" for p in ours))
    with open(OUTCOME_FILE, "w", encoding="utf-8") as handle:
        json.dump({"run_token": token, "process": ours[0]}, handle, indent=1)
    return ours[0]


def all_fields(process_id) -> dict:
    record = uip_json(["ah", "automations", "get", str(process_id), "--all-fields"])
    if not succeeded(record):
        raise CheckFailed(f"automations get --all-fields failed: {describe_failure(record)}")
    return record.get("Data") or {}


def check_process(seed: dict) -> str:
    process = our_process(seed)
    return f"process {process['Id']} '{process.get('Name')}' exists once on the tenant"


def check_fields(seed: dict) -> str:
    process = our_process(seed)
    record = all_fields(process["Id"])
    if seed["run_token"] not in str(record.get("ProcessName", "")):
        raise CheckFailed(f"ProcessName lost the run token: {record.get('ProcessName')!r}")
    description = re.sub(r"<[^>]+>", " ", str(record.get("ProcessDescription") or ""))
    if len(description.strip()) < 20 or has_placeholder(description):
        raise CheckFailed(f"ProcessDescription missing, thin, or a template placeholder: {description[:120]!r}")
    if not any(record.get(k) for k in ("ProcessL1Id", "ProcessL2Id", "ProcessL3Id")):
        raise CheckFailed("no category recorded on the process (ProcessL1Id/L2Id/L3Id all empty)")
    if not record.get("ProcessSubmitterUserId"):
        raise CheckFailed("ProcessSubmitterUserId is empty")
    if record.get("ProcessIsDeleted"):
        raise CheckFailed("process is flagged deleted")
    return "record carries the token, a real description, a category and a submitter"


def check_applications(seed: dict) -> str:
    process = our_process(seed)
    record = all_fields(process["Id"])
    attached = int(record.get("ProcessNumApplications") or 0)
    inventory_names = [str(a.get("Name", "")).lower() for a in seed.get("inventory") or []]
    in_inventory = sum(1 for system in PDD_SYSTEMS if any(system in name for name in inventory_names))
    # With new_applications in the schema every named system can be attached (the
    # submission creates the missing ones); without it only the inventory's can.
    if seed.get("new_applications_offered"):
        expected_min, reason = len(PDD_SYSTEMS), "the schema offers new_applications"
    else:
        expected_min, reason = in_inventory, f"the inventory already held {in_inventory} of them"
    if attached < expected_min:
        raise CheckFailed(f"{attached} application(s) attached, but {reason} — the publish dropped "
                          f"applications it could have attached (PDD names {len(PDD_SYSTEMS)})")
    return f"{attached} application(s) attached; expected at least {expected_min} because {reason}"


def documents_of(process_id) -> list[dict]:
    listing = uip_json(["ah", "documents", "list", str(process_id)])
    if not succeeded(listing):
        raise CheckFailed(f"documents list failed: {describe_failure(listing)}")
    return [d for d in items(listing) if d.get("IsActive", 1)]


def download(file_id) -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        target = os.path.join(tmp, f"{file_id}.bin")
        result = uip_json(["ah", "documents", "download", str(file_id), "--destination", target])
        if not succeeded(result):
            raise CheckFailed(f"documents download {file_id} failed: {describe_failure(result)}")
        with open(target, "rb") as handle:
            return handle.read()


def staged_digest(seed: dict, fixture: str) -> str:
    digest = (seed.get("fixtures") or {}).get(fixture)
    if not digest:
        raise CheckFailed(f"seed.json has no digest for {fixture}; seed_publish.py did not render it")
    return digest


def check_documents(seed: dict) -> str:
    process = our_process(seed)
    pdds = [d for d in documents_of(process["Id"]) if d.get("TypeId") == PDD_TYPE_ID]
    if len(pdds) != 1:
        raise CheckFailed(f"expected exactly one PDD (type {PDD_TYPE_ID}) attached, found {len(pdds)}")
    if not pdds[0].get("FileId"):
        raise CheckFailed("PDD was attached as a link, not uploaded bytes")
    digest = hashlib.sha256(download(pdds[0]["FileId"])).hexdigest()
    if digest != staged_digest(seed, PDD_FIXTURE):
        raise CheckFailed("stored PDD bytes differ from the staged file — the agent rewrote or regenerated it")
    return f"PDD attached once as type {PDD_TYPE_ID}, stored bytes identical to the staged file"


def check_bpmn_layout(seed: dict) -> str:
    process = our_process(seed)
    maps = [d for d in documents_of(process["Id"]) if d.get("TypeId") in PROCESS_MAP_TYPE_IDS and d.get("FileId")]
    if len(maps) != 1:
        raise CheckFailed(f"expected exactly one uploaded process map (type in {sorted(PROCESS_MAP_TYPE_IDS)}), found {len(maps)}")
    xml = download(maps[0]["FileId"])
    # The bytes come from the tenant, i.e. from whatever the agent uploaded. A BPMN
    # file never needs a DTD, so refuse one outright rather than let the stdlib
    # parser expand entities (XXE / billion laughs) — no defusedxml in the sandbox.
    if re.search(rb"<!(?:DOCTYPE|ENTITY)\b", xml):
        raise CheckFailed("stored process map declares a DTD/entities; a BPMN export never does")
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise CheckFailed(f"stored process map is not well-formed XML: {exc}") from exc
    diagrams = root.findall(f".//{BPMN_DI}BPMNDiagram")
    shapes = root.findall(f".//{BPMN_DI}BPMNShape")
    if not diagrams or not shapes:
        raise CheckFailed(f"stored process map has {len(diagrams)} BPMNDiagram and {len(shapes)} BPMNShape elements — "
                          "Automation Hub would render 'No diagrams found in the BPMN file'")
    same_bytes = hashlib.sha256(xml).hexdigest() == staged_digest(seed, MAP_FIXTURE)
    return (f"process map renders: {len(diagrams)} diagram, {len(shapes)} shapes"
            + (" (byte-identical to the staged file)" if same_bytes else " (re-encoded on upload)"))


CHECKS = {
    "process": check_process,
    "fields": check_fields,
    "applications": check_applications,
    "documents": check_documents,
    "bpmn-layout": check_bpmn_layout,
}


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in CHECKS:
        print(f"usage: {argv[0]} {{{'|'.join(CHECKS)}}}", file=sys.stderr)
        return 2
    try:
        print("OK:", CHECKS[argv[1]](load_seed()))
        return 0
    except CheckFailed as failure:
        print("FAIL:", failure)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
