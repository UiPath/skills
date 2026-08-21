#!/usr/bin/env python3
"""Run the diagnostic ladder for a failed run in one call and emit one correlated report.

Order: job status (resolve instance id + folder key) -> instance incidents -> incident get ->
instance variables -> correlate the faulting element to a node in the local .flow. Traces and the
deployed asset are opt-in, last-resort steps. Read-only: it never runs `flow debug`.
Requires `uip login`. Exit 0 report produced, 4 a CLI call failed, 5 no incident found.
"""
import argparse
import json
import shlex
import subprocess
import sys

from _flow import lib as fl

INSTANCE_KEYS = ("instanceid", "instancekey", "processinstanceid")
FOLDER_KEYS = ("folderkey", "folderid")
INCIDENT_ID_KEYS = ("incidentid", "id", "key")
ELEMENT_KEYS = ("elementid", "faultingelementid", "activityid", "elementname")


def _find(obj, names):
    """First value whose key case-insensitively matches one of `names`, breadth-first."""
    queue = [obj]
    while queue:
        cur = queue.pop(0)
        if isinstance(cur, dict):
            for k in cur:
                if k.lower() in names and cur[k] not in (None, "", []):
                    return cur[k]
            queue.extend(cur[k] for k in cur)
        elif isinstance(cur, list):
            queue.extend(cur)
    return None


def _data(payload):
    if isinstance(payload, dict) and "Data" in payload:
        return payload["Data"]
    return payload


class Cli:
    def __init__(self, cli, dry_run=False):
        self.base = shlex.split(cli)
        self.dry_run = dry_run
        self.calls = []

    def run(self, *args):
        cmd = self.base + list(args) + ["--output", "json"]
        self.calls.append(" ".join(cmd))
        if self.dry_run:
            return {}, 0
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            sys.stderr.write("CLI call failed (%d): %s\n%s\n" % (proc.returncode, " ".join(cmd), proc.stderr.strip()))
            return None, proc.returncode
        try:
            return json.loads(proc.stdout or "{}"), 0
        except json.JSONDecodeError:
            sys.stderr.write("could not parse JSON from: %s\n" % " ".join(cmd))
            return None, 4


def correlate(flow_path, element_id):
    if not flow_path or not element_id:
        return None
    flow = fl.load(flow_path)
    nodes = fl.node_map(flow)
    match = None
    if element_id in nodes:
        match = element_id
    else:
        for nid in sorted(nodes):
            if element_id.endswith(nid) or nid in element_id:
                match = nid
                break
    if match is None:
        return {"elementId": element_id, "node": None,
                "note": "no node id in %s matches the faulting element; the deployed BPMN may differ "
                        "(fetch it with --asset)" % flow_path}
    node = nodes[match]
    return {
        "elementId": element_id,
        "node": match,
        "type": node.get("type"),
        "inputs": node.get("inputs", {}),
        "upstreamEdges": [
            {"from": e.get("sourceNodeId"), "sourcePort": e.get("sourcePort"), "targetPort": e.get("targetPort")}
            for e in sorted(fl.in_edges(flow, match), key=lambda e: str(e.get("id")))
        ],
        "errorHandlingEnabled": (node.get("inputs") or {}).get("errorHandlingEnabled"),
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--job-key", help="job key from `flow debug` / `process run`")
    p.add_argument("--instance-id", help="skip step 1 when you already have the instance id")
    p.add_argument("--folder-key", help="required by instance/incident calls; resolved from job status when omitted")
    p.add_argument("--flow", help="local .flow file used for the correlation step")
    p.add_argument("--cli", default="uip maestro flow", help='CLI prefix (default "uip maestro flow"; use "uip flow" on CLI < 0.3.4)')
    p.add_argument("--out", help="write the full JSON report here")
    p.add_argument("--max-incidents", type=int, default=3)
    p.add_argument("--traces", action="store_true", help="also pull job traces (verbose, last resort)")
    p.add_argument("--asset", action="store_true", help="also fetch the deployed BPMN definition")
    p.add_argument("--dry-run", action="store_true", help="print the ladder without calling the CLI")
    args = p.parse_args(argv)
    if not args.job_key and not args.instance_id:
        fl.die("pass --job-key or --instance-id")

    cli = Cli(args.cli, args.dry_run)
    report = {"steps": [], "incidents": [], "correlation": None}
    instance_id, folder_key = args.instance_id, args.folder_key

    if args.job_key:
        payload, rc = cli.run("job", "status", args.job_key)
        if payload is None:
            return 4
        data = _data(payload)
        report["steps"].append("job status")
        report["jobStatus"] = data
        instance_id = instance_id or _find(data, INSTANCE_KEYS)
        folder_key = folder_key or _find(data, FOLDER_KEYS)
    if args.dry_run:
        instance_id = instance_id or "<INSTANCE_ID>"
        folder_key = folder_key or "<FOLDER_KEY>"
    if not instance_id:
        fl.die("could not resolve an instance id; pass --instance-id", 4)
    if not folder_key:
        fl.die("could not resolve a folder key; pass --folder-key (see `uip or folders list`)", 4)
    report["instanceId"] = instance_id
    report["folderKey"] = folder_key

    payload, rc = cli.run("instance", "incidents", instance_id, "--folder-key", folder_key)
    if payload is None:
        return 4
    incidents = _data(payload)
    report["steps"].append("instance incidents")
    if isinstance(incidents, dict):
        incidents = incidents.get("Incidents") or incidents.get("items") or [incidents]
    incidents = [i for i in (incidents or []) if isinstance(i, dict)]
    for incident in incidents[: args.max_incidents]:
        iid = _find(incident, INCIDENT_ID_KEYS)
        detail = incident
        if iid:
            payload, rc = cli.run("incident", "get", str(iid), "--folder-key", folder_key)
            if payload is None:
                return 4
            detail = _data(payload) or incident
            report["steps"].append("incident get %s" % iid)
        report["incidents"].append(detail)

    payload, rc = cli.run("instance", "variables", instance_id, "--folder-key", folder_key)
    if payload is None:
        return 4
    report["variables"] = _data(payload)
    report["steps"].append("instance variables")

    if args.asset:
        payload, rc = cli.run("instance", "asset", instance_id, "--folder-key", folder_key)
        if payload is None:
            return 4
        report["deployedAsset"] = _data(payload)
        report["steps"].append("instance asset")
    if args.traces and args.job_key:
        payload, rc = cli.run("job", "traces", args.job_key)
        if payload is None:
            return 4
        report["traces"] = _data(payload)
        report["steps"].append("job traces")

    element = _find(report["incidents"], ELEMENT_KEYS) if report["incidents"] else None
    report["faultingElement"] = element
    report["correlation"] = correlate(args.flow, element)
    report["cliCalls"] = cli.calls

    if args.dry_run:
        for call in cli.calls:
            print(call)
        return 0
    if args.out:
        with open(args.out, "w") as fh:
            json.dump(report, fh, indent=2)
            fh.write("\n")
    first = report["incidents"][0] if report["incidents"] else {}
    print("instance: %s" % instance_id)
    print("folder:   %s" % folder_key)
    print("incidents: %d" % len(report["incidents"]))
    if first:
        for label, keys in (("category", ("category", "errorCategory", "Category")),
                            ("message", ("message", "errorMessage", "Message"))):
            value = _find(first, tuple(k.lower() for k in keys))
            if value:
                print("%-9s %s" % (label + ":", str(value)[:300]))
    print("element:  %s" % (element or "<none reported>"))
    corr = report["correlation"]
    if corr:
        if corr.get("node"):
            print("node:     %s (%s); upstream: %s" % (
                corr["node"], corr.get("type"),
                ", ".join("%s:%s" % (e["from"], e["sourcePort"]) for e in corr["upstreamEdges"]) or "none"))
        else:
            print("node:     %s" % corr.get("note"))
    if args.out:
        print("report:   %s" % args.out)
    return 0 if report["incidents"] else 5


if __name__ == "__main__":
    sys.exit(main())
