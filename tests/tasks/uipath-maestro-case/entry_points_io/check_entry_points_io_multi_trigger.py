#!/usr/bin/env python3
"""Assert the per-trigger In-arg distribution in entry-points.json (Step 6.3 + per-trigger binding).

SDD binds two In-args to different triggers via §1.5 sourceTriggers:
  claimId  → T02 (manual, primary)   priority → T03 (timer)   decision → Out (default "Resolved")

The FE-ported projection (entry-points-sync.md) scopes input per trigger by elementId and
projects every Out-arg to every entry. So the two entries must partition the In-args:
  - one entry (claimId's trigger)  : input.properties == {claimId} only
  - the other entry (priority's)   : input.properties == {priority} only
  - BOTH entries                   : output.properties has decision (default "Resolved")
(Trigger node ids are minted, e.g. `trigger_mNq7kX` — do NOT assume `trigger_1`.)

This FAILS the old "all In → primary trigger" behavior (which would put both In-args on
trigger_1 and leave the timer's input empty) — so it specifically validates per-trigger binding.
"""
import glob
import json
import os
import sys


def fail(msg):
    sys.exit(f"FAIL: {msg}")


def find_entry_points():
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        return sys.argv[1]
    for path in sorted(glob.glob("**/entry-points.json", recursive=True)):
        try:
            data = json.load(open(path))
        except (OSError, json.JSONDecodeError):
            continue
        if len(data.get("entryPoints") or []) >= 2:
            return path
    fail(f"no 2-entry entry-points.json found (argv={sys.argv[1:]}, cwd={os.getcwd()})")


def in_keys(entry):
    return set((entry.get("input") or {}).get("properties", {}) or {})


def out_props(entry):
    return (entry.get("output") or {}).get("properties", {}) or {}


def load_sibling_caseplan(ep_path):
    cp = os.path.join(os.path.dirname(os.path.abspath(ep_path)), "caseplan.json")
    if not os.path.isfile(cp):
        hits = glob.glob(os.path.join(os.path.dirname(ep_path) or ".", "**", "caseplan.json"), recursive=True)
        cp = hits[0] if hits else None
    if not cp or not os.path.isfile(cp):
        fail(f"sibling caseplan.json not found next to {ep_path} (needed to verify each entry's trigger type)")
    try:
        return json.load(open(cp))
    except (OSError, json.JSONDecodeError) as e:
        fail(f"could not read {cp}: {e}")


def trigger_service_type(caseplan, node_id):
    """serviceType of the trigger node — 'Intsvc.TimerTrigger' for a timer, None/other for a manual."""
    for n in caseplan.get("nodes", []):
        if n.get("id") == node_id:
            up = n.get("data", {}).get("uipath")
            return up.get("serviceType") if isinstance(up, dict) else None
    fail(f"trigger node {node_id!r} (from an entry-point filePath fragment) not found in caseplan.json")


def main():
    path = find_entry_points()
    try:
        data = json.load(open(path))
    except (OSError, json.JSONDecodeError) as e:
        fail(f"could not read {path}: {e}")

    entries = data.get("entryPoints") or []
    if len(entries) != 2:
        fail(f"expected 2 entryPoints (manual T02 + timer T03), got {len(entries)} in {path}")

    by_frag = {e.get("filePath", "").split("#")[-1]: e for e in entries}

    # Partition: each In-arg on exactly one entry, the two entries disjoint.
    keysets = [in_keys(e) for e in entries]
    union = set().union(*keysets)
    inter = set.intersection(*keysets)
    if union != {"claimId", "priority"}:
        fail(f"input union across entries should be {{claimId, priority}}, got {union}")
    if inter:
        fail(f"In-arg(s) on more than one trigger (scoping violation): {inter}")
    if not all(len(k) == 1 for k in keysets):
        fail(f"each entry's input should hold exactly ONE In-arg; got keysets {[sorted(k) for k in keysets]}")

    # Identify each entry by the In-arg it scopes — trigger node ids are minted
    # (e.g. `trigger_mNq7kX`), so do NOT assume the primary is literally `trigger_1`.
    # The partition above already guarantees one entry == {claimId} and one == {priority}.
    claim_entry = next(e for e in entries if in_keys(e) == {"claimId"})
    prio_entry = next(e for e in entries if in_keys(e) == {"priority"})

    # Map each entry back to its trigger node in the sibling caseplan.json and assert the binding
    # DIRECTION — claimId on the MANUAL trigger (T02), priority on the TIMER trigger (T03). The
    # partition check above passes even if T-resolution swapped the two; this catches that.
    caseplan = load_sibling_caseplan(path)
    claim_frag = claim_entry.get("filePath", "").split("#")[-1]
    prio_frag = prio_entry.get("filePath", "").split("#")[-1]
    claim_svc = trigger_service_type(caseplan, claim_frag)
    prio_svc = trigger_service_type(caseplan, prio_frag)
    if claim_svc == "Intsvc.TimerTrigger":
        fail(f"claimId is bound to the TIMER trigger ({claim_frag}); expected the manual trigger (T02) — bindings swapped?")
    if prio_svc != "Intsvc.TimerTrigger":
        fail(f"priority is bound to a non-timer trigger ({prio_frag}, serviceType={prio_svc!r}); expected the timer trigger (T03, Intsvc.TimerTrigger) — bindings swapped?")

    # Types / defaults of the scoped In-args.
    claim = (claim_entry.get("input") or {}).get("properties", {}).get("claimId", {})
    if claim.get("type") != "string":
        fail(f"claimId should be {{type:string}}, got {claim}")
    prio = (prio_entry.get("input") or {}).get("properties", {}).get("priority", {})
    if prio.get("type") != "string" or prio.get("default") != "Medium":
        fail(f"priority should be {{type:string, default:'Medium'}}, got {prio}")

    # Output projected to EVERY entry with its companion default.
    for frag, e in by_frag.items():
        dec = out_props(e).get("decision")
        if not dec or dec.get("type") != "string":
            fail(f"entry '{frag}' output.decision should be {{type:string}}, got {dec}")
        if dec.get("default") != "Resolved":
            fail(f"entry '{frag}' output.decision default should be 'Resolved', got {dec.get('default')!r}")

    print(
        f"PASS: {path} — per-trigger binding verified via caseplan "
        f"(claimId→manual T02, priority→timer T03, no overlap); decision projected to both entries."
    )


if __name__ == "__main__":
    main()
