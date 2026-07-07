#!/usr/bin/env python3
"""
Assert a tenant-scoped Data Fabric choice set exists and contains a set of
required value names.

Used as a `run_command` criterion to verify agent-authored choice sets took —
independent of how many separate Bash tool calls the agent used to add the
values (agents commonly chain multiple `uip df choice-set-values create`
invocations into one Bash call).

Usage:
    verify_choice_set_values.py --name CE_SmokePaymentStatus \\
        --required paid,unpaid,refunded

Exit codes:
    0 — choice set exists AND every required value is present (case-insensitive)
    1 — choice set missing, any required value missing, or uip call failed
"""

import argparse
import json
import subprocess
import sys

UIP_TIMEOUT_SECONDS = 60


def run_uip(*args: str) -> tuple[int, str, str]:
    try:
        r = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True, text=True, timeout=UIP_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {UIP_TIMEOUT_SECONDS}s"
    except FileNotFoundError:
        return 127, "", "uip CLI not on PATH"
    return r.returncode, r.stdout, r.stderr


def find_choice_set(name: str) -> str | None:
    code, out, err = run_uip("df", "choice-sets", "list")
    if code != 0 or not out.strip():
        print(f"FAIL: uip df choice-sets list failed: {err.strip()}", file=sys.stderr)
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return None
    inner = data.get("Data") if isinstance(data, dict) else None
    items = inner if isinstance(inner, list) else (
        (inner.get("Items") or inner.get("Records") or [])
        if isinstance(inner, dict) else []
    )
    for cs in items:
        if isinstance(cs, dict) and (cs.get("Name") or cs.get("name")) == name:
            return cs.get("Id") or cs.get("ID") or cs.get("id")
    return None


def list_value_names(cs_id: str) -> set[str]:
    code, out, err = run_uip("df", "choice-sets", "list-values", cs_id)
    if code != 0 or not out.strip():
        print(f"FAIL: uip df choice-sets list-values {cs_id} failed: {err.strip()}", file=sys.stderr)
        return set()
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return set()
    inner = data.get("Data") if isinstance(data, dict) else None
    items = inner if isinstance(inner, list) else (
        (inner.get("Items") or inner.get("Values") or [])
        if isinstance(inner, dict) else []
    )
    return {
        (v.get("Name") or v.get("name") or "").lower()
        for v in items if isinstance(v, dict)
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Assert a choice set has all required value names.")
    p.add_argument("--name", required=True, help="Choice set Name")
    p.add_argument("--required", required=True, help="Comma-separated required value names")
    args = p.parse_args()

    required = {v.strip().lower() for v in args.required.split(",") if v.strip()}
    if not required:
        print("FAIL: --required must have at least one value", file=sys.stderr)
        sys.exit(1)

    cs_id = find_choice_set(args.name)
    if not cs_id:
        print(f"FAIL: choice set {args.name!r} not found", file=sys.stderr)
        sys.exit(1)

    names = list_value_names(cs_id)
    missing = required - names
    if missing:
        print(
            f"FAIL: {args.name} missing values {sorted(missing)}; got {sorted(names)}",
            file=sys.stderr,
        )
        sys.exit(1)

    extras = names - required
    extra_hint = f" (plus extras: {sorted(extras)})" if extras else ""
    print(f"OK: {args.name} has all {len(required)} required values{extra_hint}")
    sys.exit(0)


if __name__ == "__main__":
    main()
