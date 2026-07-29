#!/usr/bin/env python3
"""Verify that one Data Fabric entity is tenant-scoped and another is folder-scoped."""

import argparse
import json
import subprocess
import sys
import time

TENANT_SCOPE = "00000000-0000-0000-0000-000000000000"
TIMEOUT_SECONDS = 30
ATTEMPTS = 2


def run_uip(*args: str) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {TIMEOUT_SECONDS}s"
    except FileNotFoundError:
        return 127, "", "uip CLI not on PATH"
    return result.returncode, result.stdout, result.stderr


def records_from_response(raw: str) -> list[dict]:
    data = json.loads(raw)
    inner = data.get("Data") if isinstance(data, dict) else None
    if isinstance(inner, list):
        return [item for item in inner if isinstance(item, dict)]
    if isinstance(inner, dict):
        records = inner.get("Records") or inner.get("records") or inner.get("Items") or []
        return [item for item in records if isinstance(item, dict)]
    return []


def list_entities(required_names: set[str]) -> list[dict]:
    last_error = ""
    for attempt in range(ATTEMPTS):
        for extra in (["--include-folders"], []):
            code, out, err = run_uip("df", "entities", "list", "--native-only", *extra)
            if code == 0 and out.strip():
                try:
                    entities = records_from_response(out)
                except json.JSONDecodeError:
                    last_error = "could not parse entities list output"
                else:
                    visible_names = {
                        str(item.get("Name") or item.get("name") or "")
                        for item in entities
                    }
                    if required_names <= visible_names:
                        return entities
                    missing = sorted(required_names - visible_names)
                    last_error = f"entities not visible yet: {', '.join(missing)}"
            else:
                last_error = err.strip() or f"exit {code}"
        if attempt + 1 < ATTEMPTS:
            time.sleep(2)
    print(f"FAIL: could not list Data Fabric entities: {last_error}", file=sys.stderr)
    return []


def folder_key(entity: dict) -> str:
    value = (
        entity.get("FolderKey")
        or entity.get("folderKey")
        or entity.get("FolderId")
        or entity.get("folderId")
        or ""
    )
    return "" if str(value).lower() == TENANT_SCOPE else str(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant-entity", required=True)
    parser.add_argument("--folder-entity", required=True)
    args = parser.parse_args()

    entities = list_entities({args.tenant_entity, args.folder_entity})
    by_name = {
        str(entity.get("Name") or entity.get("name") or ""): entity
        for entity in entities
    }
    tenant = by_name.get(args.tenant_entity)
    folder = by_name.get(args.folder_entity)

    failures: list[str] = []
    if tenant is None:
        failures.append(f"tenant entity {args.tenant_entity!r} not found")
    elif folder_key(tenant):
        failures.append(f"{args.tenant_entity!r} is folder-scoped")

    if folder is None:
        failures.append(f"folder entity {args.folder_entity!r} not found")
    elif not folder_key(folder):
        failures.append(f"{args.folder_entity!r} is tenant-scoped")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        sys.exit(1)

    print(
        f"OK: {args.tenant_entity} is tenant-scoped and "
        f"{args.folder_entity} is folder-scoped"
    )


if __name__ == "__main__":
    main()
