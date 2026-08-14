#!/usr/bin/env python3
"""
End-state assertion for a FEDERATED Data Fabric entity built from an external
connector source joined to one or more native entities.

Confirms the agent produced a real federated (live, read-only) entity — not a
native entity with imported rows — and that it carries the expected number of
sources and join criteria.

Usage (as a success_criteria run_command):
    verify_federated_entity.py --entity-name UserDirectory \
        --expected-sources 3 --min-joins 2 --external-object sys_user

Checks:
    - entity exists and EntityClass == "Federated"
    - ExternalFields (sources) count == --expected-sources
    - SourceJoinCriterias count >= --min-joins
    - at least one source's external object name matches --external-object
      (case-insensitive substring; skipped when the flag is omitted)

Exit codes:
    0  — all assertions pass
    1  — any assertion fails, entity not found, or a uip call fails
"""

import argparse
import json
import subprocess
import sys
import time

UIP_TIMEOUT_SECONDS = 30
LOOKUP_ATTEMPTS = 2
LOOKUP_RETRY_SECONDS = 2
TENANT_SCOPE = "00000000-0000-0000-0000-000000000000"


def run_uip(*args: str) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True, text=True, timeout=UIP_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {UIP_TIMEOUT_SECONDS}s"
    except FileNotFoundError:
        return 127, "", "uip CLI not on PATH"
    return result.returncode, result.stdout, result.stderr


def folder_key_of(entity: dict) -> str:
    fk = (
        entity.get("FolderKey") or entity.get("folderKey")
        or entity.get("FolderId") or entity.get("folderId") or ""
    )
    return "" if str(fk).lower() == TENANT_SCOPE else str(fk)


def find_federated_entity(name: str) -> tuple[str | None, str | None]:
    """Return (entity_id, folder_key) for a federated entity by name, else (None, None)."""
    for attempt in range(LOOKUP_ATTEMPTS):
        # --federated-only so the federated entity is visible (native-only would hide it).
        code, out, err = run_uip("df", "entities", "list", "--federated-only", "--include-folders")
        if code == 0 and out.strip():
            try:
                data = json.loads(out)
            except json.JSONDecodeError:
                data = None
            inner = data.get("Data") if isinstance(data, dict) else data
            rows = inner if isinstance(inner, list) else (inner or {}).get("Records", []) if isinstance(inner, dict) else []
            for e in rows or []:
                ename = e.get("Name") or e.get("name") or ""
                if ename.lower() == name.lower():
                    eid = e.get("Id") or e.get("id")
                    return (eid, folder_key_of(e))
        if attempt < LOOKUP_ATTEMPTS - 1:
            time.sleep(LOOKUP_RETRY_SECONDS)
    return (None, None)


def main() -> int:
    ap = argparse.ArgumentParser(description="Assert a federated entity's structure.")
    ap.add_argument("--entity-name", required=True)
    ap.add_argument("--expected-sources", type=int, default=None,
                    help="Exact number of sources (ExternalFields) expected.")
    ap.add_argument("--min-joins", type=int, default=1,
                    help="Minimum number of SourceJoinCriterias expected.")
    ap.add_argument("--external-object", default=None,
                    help="A source's external object name that must be present (substring, case-insensitive).")
    ap.add_argument("--assert-queryable", action="store_true",
                    help="Also read records back from the federated entity and assert the query returns rows.")
    ap.add_argument("--min-records", type=int, default=1,
                    help="Minimum records the read must return when --assert-queryable is set.")
    args = ap.parse_args()

    eid, fk = find_federated_entity(args.entity_name)
    if not eid:
        print(f"FAIL: federated entity '{args.entity_name}' not found (list --federated-only).")
        return 1

    get_args = ["df", "entities", "get", eid]
    if fk:
        get_args += ["--folder-key", fk]
    code, out, err = run_uip(*get_args)
    if code != 0 or not out.strip():
        print(f"FAIL: `entities get {eid}` failed (exit {code}): {err.strip()}")
        return 1
    try:
        entity = (json.loads(out).get("Data") or {})
    except json.JSONDecodeError as e:
        print(f"FAIL: could not parse entities get output: {e}")
        return 1

    ok = True

    entity_class = entity.get("EntityClass") or entity.get("entityClass") or ""
    if str(entity_class).lower() != "federated":
        print(f"FAIL: EntityClass is '{entity_class}', expected 'Federated' (agent may have imported data into a native entity).")
        ok = False
    else:
        print("OK: EntityClass == Federated")

    sources = entity.get("ExternalFields") or entity.get("externalFields") or []
    if args.expected_sources is not None:
        if len(sources) == args.expected_sources:
            print(f"OK: {len(sources)} sources (expected {args.expected_sources})")
        else:
            print(f"FAIL: {len(sources)} sources, expected {args.expected_sources}")
            ok = False

    joins = entity.get("SourceJoinCriterias") or entity.get("sourceJoinCriterias") or []
    if len(joins) >= args.min_joins:
        print(f"OK: {len(joins)} join criteria (>= {args.min_joins})")
    else:
        print(f"FAIL: {len(joins)} join criteria, expected >= {args.min_joins}")
        ok = False

    if args.external_object:
        names = []
        for s in sources:
            detail = s.get("ExternalObjectDetail") or s.get("externalObjectDetail") or {}
            names.append(str(detail.get("ExternalObjectName") or detail.get("externalObjectName") or ""))
        if any(args.external_object.lower() in n.lower() for n in names):
            print(f"OK: a source references external object '{args.external_object}'")
        else:
            print(f"FAIL: no source references '{args.external_object}' (found: {names})")
            ok = False

    if args.assert_queryable:
        q_args = ["df", "records", "list", eid]
        if fk:
            q_args += ["--folder-key", fk]
        q_args += ["--limit", "5"]
        code, out, err = run_uip(*q_args)
        rows, total = 0, None
        if code == 0 and out.strip():
            try:
                qd = json.loads(out)
                data = qd.get("Data") if isinstance(qd, dict) else qd
                if isinstance(data, dict):
                    # `uip df records list` returns {Data: {Items: [...], TotalCount: N}}.
                    # Keep the other keys as fallbacks for other shapes/versions.
                    items = (data.get("Items") or data.get("value")
                             or data.get("items") or data.get("Records") or [])
                    rows = len(items) if isinstance(items, list) else 0
                    tc = data.get("TotalCount")
                    total = tc if isinstance(tc, int) else None
                elif isinstance(data, list):
                    rows = len(data)
                if total is None:
                    pag = (qd.get("Pagination") if isinstance(qd, dict) else {}) or {}
                    total = pag.get("TotalCount") if isinstance(pag.get("TotalCount"), int) else None
            except json.JSONDecodeError:
                pass
        effective = total if total is not None else rows
        if code == 0 and effective >= args.min_records:
            print(f"OK: federated query returned {effective} record(s) (>= {args.min_records}) — the live view reads back")
        else:
            print(f"FAIL: federated query did not return >= {args.min_records} record(s) "
                  f"(exit {code}, rows={rows}, total={total}): {err.strip()[:200]}")
            ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
