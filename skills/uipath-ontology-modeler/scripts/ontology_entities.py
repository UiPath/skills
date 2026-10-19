#!/usr/bin/env python3
"""Turn an ontology handoff into local Data Fabric entity definitions, one EntityRecord JSON per class."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9]{2,99}$")
SYSTEM_FIELDS = {"Id", "CreatedAt", "UpdatedAt", "CreatedBy", "UpdatedBy"}
SYSTEM_FIELDS_LOWER = {name.lower(): name for name in SYSTEM_FIELDS}
DEFAULT_STRING_LENGTH = 200
SQL_TYPES: dict[str, tuple[str, int | None]] = {
    "xsd:string": ("NVARCHAR", DEFAULT_STRING_LENGTH),
    "xsd:anyURI": ("NVARCHAR", DEFAULT_STRING_LENGTH),
    "xsd:decimal": ("DECIMAL", None),
    "xsd:double": ("DECIMAL", None),
    "xsd:float": ("DECIMAL", None),
    "xsd:integer": ("INT", None),
    "xsd:int": ("INT", None),
    "xsd:long": ("BIGINT", None),
    "xsd:boolean": ("BIT", None),
    "xsd:date": ("DATE", None),
    "xsd:dateTime": ("DATETIME2", None),
}
RELATIONSHIP_SQL_TYPE = "UNIQUEIDENTIFIER"


def build_entities(handoff: dict) -> tuple[dict[str, dict], list[str]]:
    errors: list[str] = []
    class_map = handoff.get("CLASS_MAP")
    field_metadata = handoff.get("FIELD_METADATA")
    relationships = handoff.get("RELATIONSHIPS", [])
    if not isinstance(class_map, dict) or not class_map:
        return {}, ["CLASS_MAP must map every class to an entityName."]
    if not isinstance(field_metadata, dict):
        return {}, ["FIELD_METADATA must map every class to its fields."]
    if not isinstance(relationships, list):
        return {}, ["RELATIONSHIPS must be a list; use [] when there are none."]

    entity_names: dict[str, str] = {}
    for class_name, entry in class_map.items():
        name = entry.get("entityName") if isinstance(entry, dict) else None
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            errors.append(f"CLASS_MAP.{class_name}.entityName '{name}' must match {NAME_RE.pattern}.")
            continue
        if isinstance(entry, dict) and {"entityId", "folderId"} & entry.keys():
            errors.append(f"CLASS_MAP.{class_name} must not carry entityId or folderId; entities are authored locally.")
        entity_names[class_name] = name
    seen: dict[str, str] = {}
    for class_name, name in entity_names.items():
        other = seen.setdefault(name.lower(), class_name)
        if other != class_name:
            errors.append(f"Entity name '{name}' is used by more than one class ({other}, {class_name}).")

    targets: dict[tuple[str, str], str] = {}
    for rel in relationships:
        if not isinstance(rel, dict) or not all(isinstance(rel.get(k), str) for k in ("from", "field", "to")):
            errors.append(f"RELATIONSHIPS entry {rel!r} must have string from, field and to.")
            continue
        if rel["to"] not in class_map:
            errors.append(f"Relationship {rel['from']}.{rel['field']} targets unknown class '{rel['to']}'.")
            continue
        targets[(rel["from"], rel["field"])] = rel["to"]

    entities: dict[str, dict] = {}
    for class_name, name in entity_names.items():
        fields_in = field_metadata.get(class_name)
        if not isinstance(fields_in, dict):
            errors.append(f"FIELD_METADATA.{class_name} must be a field map.")
            continue
        fields: list[dict] = []
        for field_name, meta in fields_in.items():
            if field_name in SYSTEM_FIELDS:
                continue
            if field_name.lower() in SYSTEM_FIELDS_LOWER:
                errors.append(
                    f"{class_name}.{field_name}: collides with the system field "
                    f"'{SYSTEM_FIELDS_LOWER[field_name.lower()]}'; drop it or rename it."
                )
                continue
            meta = meta if isinstance(meta, dict) else {}
            if not NAME_RE.fullmatch(field_name):
                errors.append(f"{class_name}.{field_name}: field name must match {NAME_RE.pattern}.")
                continue
            field = {
                "Name": field_name,
                "DisplayName": meta.get("displayName") or field_name,
                "IsRequired": bool(meta.get("required")),
            }
            target = targets.get((class_name, field_name))
            if target is not None:
                if target in entity_names:
                    field["FieldDisplayType"] = "Relationship"
                    field["SqlType"] = {"Name": RELATIONSHIP_SQL_TYPE}
                    field["ReferenceEntity"] = {"Name": entity_names[target]}
                    fields.append(field)
                continue
            xsd = meta.get("type")
            if not isinstance(xsd, str) or xsd not in SQL_TYPES:
                errors.append(
                    f"{class_name}.{field_name}: unknown type '{xsd}'; use one of {', '.join(sorted(SQL_TYPES))} or declare it in RELATIONSHIPS."
                )
                continue
            sql_name, length = SQL_TYPES[xsd]
            if sql_name == "NVARCHAR" and isinstance(meta.get("length"), int):
                length = meta["length"]
            field["SqlType"] = {"Name": sql_name, **({"LengthLimit": length} if length else {})}
            fields.append(field)
        entry = class_map[class_name]
        entities[name] = {
            "Name": name,
            "DisplayName": entry.get("displayName") or name,
            "Fields": fields,
        }
    return entities, errors


def fail(errors: list[str]) -> int:
    print(json.dumps({"status": "FAIL", "errors": errors}, indent=2))
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", required=True, type=Path,
                        help="Ontology WORKDIR; reads input/handoff.json and writes entities/.")
    args = parser.parse_args(argv)
    workdir = args.workdir.expanduser().resolve()
    handoff_file = workdir / "input" / "handoff.json"
    out_dir = workdir / "entities"
    if args.workdir.is_symlink() or not workdir.is_dir():
        return fail([f"WORKDIR {args.workdir} must be an existing folder, not a symlink."])
    if handoff_file.is_symlink() or not handoff_file.is_file():
        return fail([f"{handoff_file} must be a regular file."])
    if out_dir.exists() and (out_dir.is_symlink() or not out_dir.is_dir()):
        return fail([f"{out_dir} must be a folder, not a file or symlink."])
    try:
        handoff = json.loads(handoff_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return fail([f"input/handoff.json: {error}"])
    entities, errors = build_entities(handoff if isinstance(handoff, dict) else {})
    if errors:
        return fail(errors)
    out_dir.mkdir(exist_ok=True)
    keep = {f"{name}{suffix}" for name in entities for suffix in (".json", ".patch.json")}
    removed = []
    for stale in sorted(out_dir.glob("*.json")):
        if stale.name not in keep and stale.is_file() and not stale.is_symlink():
            stale.unlink()
            removed.append(stale.name)
    written = []
    for name, record in entities.items():
        path = out_dir / f"{name}.json"
        patch = out_dir / f"{name}.patch.json"
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        patch.write_text(json.dumps({"resourceJson": json.dumps(record)}) + "\n", encoding="utf-8")
        written.append({"name": name, "path": str(path), "patch": str(patch)})
    print(json.dumps({"status": "PASS", "entities": written, "removed": removed}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
