#!/usr/bin/env python3
"""
Idempotent pre-seed for a tenant-scoped Data Fabric choice set with a fixed
value list. Used by smoke/integration tests that reference brownfield choice
sets whose scope must match tenant-scoped parent entities.

Behavior:
  - If a choice set with `--name` exists, ensure each expected value is
    present (add missing ones via `choice-set-values create`). Extra values
    on the choice set are left alone.
  - If the choice set does not exist, create it at tenant level and add each
    value.

Never fails the test — WARN + exit 0 on any uip error.

Usage:
    seed_choice_set.py --name CE_SmokeCategories \\
        --display-name "Smoke Categories" \\
        --values travel,meals,lodging

Or via a JSON spec file:
    seed_choice_set.py --spec seeds/smoke_categories.choice_set.json

Spec file shape:
    {
      "name": "CE_SmokeCategories",
      "displayName": "Smoke Categories",
      "description": "Tenant-scoped categories for smoke tests",
      "values": ["travel", "meals", "lodging"]
    }
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

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
        detail = (err.strip() or out.strip())[:400] or "(no output)"
        print(f"WARN: choice-sets list failed (exit {code}): {detail}", file=sys.stderr)
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return None
    inner = data.get("Data") if isinstance(data, dict) else None
    items = inner if isinstance(inner, list) else (
        (inner.get("Items") or inner.get("Records") or inner.get("records") or [])
        if isinstance(inner, dict) else []
    )
    for cs in items:
        if isinstance(cs, dict) and (cs.get("Name") or cs.get("name")) == name:
            return cs.get("ID") or cs.get("Id") or cs.get("id")
    return None


def list_value_names(cs_id: str) -> set[str]:
    code, out, _ = run_uip("df", "choice-sets", "list-values", cs_id)
    if code != 0 or not out.strip():
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


def create_choice_set(name: str, display_name: str, description: str) -> str | None:
    args = ["df", "choice-sets", "create", name, "--display-name", display_name]
    if description:
        args += ["--description", description]
    code, out, err = run_uip(*args)
    if code != 0:
        # uip prints the error JSON to stdout on non-zero exit; stderr can be
        # empty. Show both streams so CI logs surface the real reason.
        detail = (err.strip() or out.strip())[:400] or "(no output)"
        print(f"WARN: choice-sets create {name} failed (exit {code}): {detail}", file=sys.stderr)
        # If the create failed because the choice set already exists, one more
        # find_choice_set may reveal it (list may have been stale earlier).
        retry_id = find_choice_set(name)
        if retry_id:
            print(f"OK: choice-sets create {name} reported already-exists; using id {retry_id}")
            return retry_id
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return None
    d = data.get("Data") if isinstance(data.get("Data"), dict) else data
    return d.get("Id") or d.get("ID") or d.get("id")


def create_value(cs_id: str, value_name: str, display_name: str | None = None) -> None:
    args = ["df", "choice-set-values", "create", cs_id, value_name]
    if display_name:
        args += ["--display-name", display_name]
    code, _, err = run_uip(*args)
    if code == 0:
        print(f"OK: added value {value_name!r} to {cs_id}")
    else:
        print(f"WARN: choice-set-values create {value_name!r} failed (exit {code}): {err.strip()[:200]}", file=sys.stderr)


def load_spec(spec: dict, cli_args: argparse.Namespace) -> tuple[str, str, str, list[str]]:
    name = cli_args.name or spec.get("name")
    if not name:
        print("FAIL: missing --name / spec.name", file=sys.stderr); sys.exit(1)
    display_name = cli_args.display_name or spec.get("displayName") or name
    description = cli_args.description or spec.get("description") or ""
    values_raw = cli_args.values or spec.get("values")
    if not values_raw:
        print("FAIL: no values provided", file=sys.stderr); sys.exit(1)
    values = [v.strip() for v in values_raw.split(",")] if isinstance(values_raw, str) else list(values_raw)
    return name, display_name, description, values


def main() -> None:
    p = argparse.ArgumentParser(description="Idempotently seed a tenant-scoped choice set.")
    p.add_argument("--spec", help="Path to a JSON spec file (name/displayName/values)")
    p.add_argument("--name")
    p.add_argument("--display-name")
    p.add_argument("--description", default="")
    p.add_argument("--values", help="Comma-separated value names")
    args = p.parse_args()

    spec = {}
    if args.spec:
        try:
            spec = json.loads(Path(args.spec).read_text())
        except (OSError, json.JSONDecodeError) as e:
            print(f"FAIL: could not read spec {args.spec}: {e}", file=sys.stderr); sys.exit(1)

    name, display_name, description, values = load_spec(spec, args)

    cs_id = find_choice_set(name)
    if not cs_id:
        cs_id = create_choice_set(name, display_name, description)
        if not cs_id:
            print(f"WARN: could not create choice set {name}; skipping value seed", file=sys.stderr)
            sys.exit(0)
        print(f"OK: created choice set {name} ({cs_id})")
    else:
        print(f"OK: choice set {name} already present ({cs_id})")

    existing = list_value_names(cs_id)
    for v in values:
        if v.lower() in existing:
            print(f"OK: value {v!r} already on {name}")
        else:
            create_value(cs_id, v, display_name=v.capitalize())

    sys.exit(0)


if __name__ == "__main__":
    main()
