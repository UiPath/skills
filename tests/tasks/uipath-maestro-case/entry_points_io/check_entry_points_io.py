#!/usr/bin/env python3
"""Assert entry-points.json input/output were back-filled from the case In/Out args (Step 6.3).

Verifies the FE-ported projection (see uipath-maestro-case/references/entry-points-sync.md):
- input.properties populated (not the empty `{}` bug shape)
- type/format mapping: string, datetime->date-time, float->number/float
- file -> {"$ref": "#/definitions/job-attachment"} + an input-level definitions block
- title == var name; float default emitted verbatim as a string
- output.properties carries the Out-arg with its companion-sourced default
- input.required is a present array (no Required column in the SDD -> [])
"""
import glob
import json
import os
import sys


def fail(msg):
    sys.exit(f"FAIL: {msg}")


def find_entry_points():
    # Prefer the explicit path; fall back to a recursive search for a populated one.
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        return sys.argv[1]
    candidates = sorted(glob.glob("**/entry-points.json", recursive=True))
    for path in candidates:
        try:
            data = json.load(open(path))
        except (OSError, json.JSONDecodeError):
            continue
        eps = data.get("entryPoints") or []
        if eps and eps[0].get("input", {}).get("properties"):
            return path
    if candidates:
        return candidates[0]
    fail(f"no entry-points.json found (argv={sys.argv[1:]}, cwd={os.getcwd()})")


def main():
    path = find_entry_points()
    try:
        data = json.load(open(path))
    except (OSError, json.JSONDecodeError) as e:
        fail(f"could not read {path}: {e}")

    entries = data.get("entryPoints") or []
    if not entries:
        fail(f"{path} has no entryPoints (trigger entry never written)")
    entry = entries[0]

    inp = entry.get("input") or {}
    out = entry.get("output") or {}
    props = inp.get("properties") or {}

    # Core fix: input must be populated, not the empty `{type:object,properties:{}}` bug shape.
    if not props:
        fail("input.properties is empty — Step 6.3 refresh did not run (this is the pre-fix bug shape)")

    # string In-arg
    claim = props.get("claimId")
    if not claim or claim.get("type") != "string":
        fail(f"claimId should be {{type:string}}, got {claim}")
    if claim.get("title") != "claimId":
        fail(f"claimId missing title==name, got {claim}")

    # datetime -> {type:string, format:date-time}
    sub = props.get("submittedAt")
    if not sub or sub.get("type") != "string" or sub.get("format") != "date-time":
        fail(f"submittedAt should be {{type:string, format:date-time}}, got {sub}")

    # float -> {type:number, format:float}; default emitted verbatim as a string
    risk = props.get("riskScore")
    if not risk or risk.get("type") != "number" or risk.get("format") != "float":
        fail(f"riskScore should be {{type:number, format:float}}, got {risk}")
    if risk.get("default") != "1.5":
        fail(f"riskScore default should be the verbatim string '1.5', got {risk.get('default')!r}")

    # file -> $ref + input-level definitions/job-attachment
    ev = props.get("evidenceDoc")
    if not ev or ev.get("$ref") != "#/definitions/job-attachment":
        fail(f"evidenceDoc should be {{$ref:#/definitions/job-attachment}}, got {ev}")
    defs = inp.get("definitions") or {}
    ja = defs.get("job-attachment")
    if not ja:
        fail("input.definitions.job-attachment is missing for the file-typed In-arg")
    if ja.get("x-uipath-resource-kind") != "JobAttachment":
        fail(f"job-attachment definition missing x-uipath-resource-kind, got {ja}")

    # required must be a present array; no Required column in the SDD -> []
    if not isinstance(inp.get("required"), list):
        fail(f"input.required must be a present array, got {inp.get('required')!r}")

    # Out-arg projected with its companion-sourced default
    oprops = out.get("properties") or {}
    dec = oprops.get("decision")
    if not dec or dec.get("type") != "string":
        fail(f"output decision should be {{type:string}}, got {dec}")
    if dec.get("default") != "Pending":
        fail(f"output decision default should be 'Pending' (from the inputOutputs companion), got {dec.get('default')!r}")

    print(f"PASS: {path} input/output projected from In/Out args (5 props, file $ref + definitions, Out default).")


if __name__ == "__main__":
    main()
