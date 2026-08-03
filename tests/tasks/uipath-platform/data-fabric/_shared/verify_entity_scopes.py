#!/usr/bin/env python3
"""Verify tenant and folder entity visibility from two folder contexts."""

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


def folder_key_from_item(folder: dict) -> str:
    return str(folder.get("Key") or folder.get("key") or "")


def folder_identifiers(folder: dict) -> set[str]:
    return {
        str(value)
        for value in (
            folder.get("Key"),
            folder.get("key"),
            folder.get("Id"),
            folder.get("ID"),
            folder.get("id"),
        )
        if value not in (None, "")
    }


def list_folders(folder_a_name: str) -> tuple[str, str, set[str]]:
    code, out, err = run_uip("or", "folders", "list")
    if code != 0 or not out.strip():
        print(
            f"FAIL: could not list folders: {err.strip() or f'exit {code}'}",
            file=sys.stderr,
        )
        return "", "", set()
    try:
        folders = records_from_response(out)
    except json.JSONDecodeError:
        print("FAIL: could not parse folders list output", file=sys.stderr)
        return "", "", set()

    folder_a = next(
        (
            folder
            for folder in folders
            if str(folder.get("Name") or folder.get("name") or "")
            == folder_a_name
        ),
        None,
    )
    folder_a_key = folder_key_from_item(folder_a or {})
    folder_a_identifiers = folder_identifiers(folder_a or {})
    folder_b_key = next(
        (
            folder_key_from_item(folder)
            for folder in folders
            if folder_key_from_item(folder)
            and folder_key_from_item(folder) != folder_a_key
        ),
        "",
    )
    if not folder_a_key:
        print(f"FAIL: folder {folder_a_name!r} not found", file=sys.stderr)
    if not folder_b_key:
        print("FAIL: no second visible folder found", file=sys.stderr)
    return folder_a_key, folder_b_key, folder_a_identifiers


def list_entities_in_context(folder_key_value: str = "") -> list[dict]:
    args = ["df", "entities", "list", "--native-only"]
    if folder_key_value:
        args += ["--folder-key", folder_key_value]
    code, out, err = run_uip(*args)
    if code != 0 or not out.strip():
        raise RuntimeError(err.strip() or f"exit {code}")
    return records_from_response(out)


def entity_names(entities: list[dict]) -> set[str]:
    return {
        str(entity.get("Name") or entity.get("name") or "")
        for entity in entities
    }


def names_in_context(
    folder_key_value: str = "", required_names: set[str] | None = None
) -> set[str]:
    last_error = ""
    for attempt in range(ATTEMPTS):
        try:
            names = entity_names(list_entities_in_context(folder_key_value))
        except (json.JSONDecodeError, RuntimeError) as exc:
            last_error = str(exc)
        else:
            missing = (required_names or set()) - names
            if not missing:
                return names
            last_error = f"entities not visible yet: {', '.join(sorted(missing))}"
        if attempt + 1 < ATTEMPTS:
            time.sleep(2)
    raise RuntimeError(last_error)


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
    parser.add_argument("--folder-a-name", default="Shared")
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

    folder_a_key, folder_b_key, folder_a_identifiers = list_folders(
        args.folder_a_name
    )
    if (
        folder is not None
        and folder_a_identifiers
        and folder_key(folder) not in folder_a_identifiers
    ):
        failures.append(
            f"{args.folder_entity!r} is not scoped to {args.folder_a_name!r}"
        )

    if folder_a_key and folder_b_key:
        try:
            tenant_names = names_in_context(
                required_names={args.tenant_entity}
            )
            folder_a_names = names_in_context(
                folder_a_key,
                required_names={args.tenant_entity, args.folder_entity},
            )
            folder_b_names = names_in_context(folder_b_key)
        except (json.JSONDecodeError, RuntimeError) as exc:
            failures.append(f"could not verify folder visibility: {exc}")
        else:
            if args.tenant_entity not in tenant_names:
                failures.append(
                    f"{args.tenant_entity!r} is absent from the tenant context"
                )
            if args.tenant_entity not in folder_a_names:
                failures.append(
                    f"{args.tenant_entity!r} is absent from folder A context"
                )
            if args.folder_entity not in folder_a_names:
                failures.append(
                    f"{args.folder_entity!r} is absent from folder A context"
                )
            if args.folder_entity in folder_b_names:
                failures.append(
                    f"{args.folder_entity!r} is visible from folder B context"
                )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        sys.exit(1)

    print(
        f"OK: {args.tenant_entity} is visible tenant-wide; "
        f"{args.folder_entity} is visible only from {args.folder_a_name}"
    )


if __name__ == "__main__":
    main()
