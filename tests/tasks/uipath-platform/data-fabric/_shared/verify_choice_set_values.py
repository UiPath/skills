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
        --required paid,unpaid,refunded \\
        [--bound-entity-name CE_SmokeExpense]

Exit codes:
    0 — choice set exists, every required value is present (case-insensitive),
        and the optional entity has a field bound to it
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


def entity_uses_choice_set(entity_name: str, choice_set_id: str) -> bool:
    code, out, err = run_uip("df", "entities", "list", "--native-only")
    if code != 0 or not out.strip():
        print(f"FAIL: uip df entities list failed: {err.strip()}", file=sys.stderr)
        return False
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return False
    inner = data.get("Data") if isinstance(data, dict) else None
    entities = inner if isinstance(inner, list) else (
        (inner.get("Records") or inner.get("records") or [])
        if isinstance(inner, dict) else []
    )
    entity_id = next(
        (
            entity.get("Id") or entity.get("ID") or entity.get("id")
            for entity in entities
            if isinstance(entity, dict)
            and (entity.get("Name") or entity.get("name")) == entity_name
        ),
        None,
    )
    if not entity_id:
        print(f"FAIL: entity {entity_name!r} not found", file=sys.stderr)
        return False

    code, out, err = run_uip("df", "entities", "get", str(entity_id))
    if code != 0 or not out.strip():
        print(f"FAIL: uip df entities get failed: {err.strip()}", file=sys.stderr)
        return False
    try:
        schema = json.loads(out).get("Data") or {}
    except json.JSONDecodeError:
        return False
    return any(
        str(field.get("ChoiceSetId") or field.get("choiceSetId") or "").lower()
        == choice_set_id.lower()
        for field in schema.get("Fields") or []
        if isinstance(field, dict)
    )


def main() -> None:
    p = argparse.ArgumentParser(description="Assert a choice set has all required value names.")
    p.add_argument("--name", required=True, help="Choice set Name")
    p.add_argument("--required", required=True, help="Comma-separated required value names")
    p.add_argument(
        "--bound-entity-name",
        help="Also require at least one field on this tenant entity to use the choice set",
    )
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

    if args.bound_entity_name and not entity_uses_choice_set(
        args.bound_entity_name, str(cs_id)
    ):
        print(
            f"FAIL: no field on {args.bound_entity_name!r} is bound to "
            f"{args.name!r}",
            file=sys.stderr,
        )
        sys.exit(1)

    extras = names - required
    extra_hint = f" (plus extras: {sorted(extras)})" if extras else ""
    binding_hint = (
        f" and is used by {args.bound_entity_name}"
        if args.bound_entity_name
        else ""
    )
    print(
        f"OK: {args.name} has all {len(required)} required values"
        f"{extra_hint}{binding_hint}"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
