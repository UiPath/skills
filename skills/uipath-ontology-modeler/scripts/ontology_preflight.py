#!/usr/bin/env python3
"""Local, dependency-free preflight checks for UiPath ontology artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


GLOBAL_SHAPES = "https://ontology.uipath.com/shapes#"
PLATFORM_ONTOLOGY = "https://ontology.uipath.com/ont#"
GATES = (
    "PATHS",
    "ARTIFACT_INVENTORY",
    "IRI_CONSISTENCY",
    "OWL_2_QL",
    "DATA_PROPERTY_NAMING",
    "CLASS_ANNOTATIONS",
    "MAPPING_TERMS",
    "LOCAL_ENTITIES",
    "CROSS_FILE_TERMS",
    "CLASS_DEPLOYABILITY",
    "RELATIONSHIP",
    "ACTION_CONTRACT",
    "SEMANTIC_CONSISTENCY",
    "NAMESPACE",
)
URI_RE = re.compile(r"https://ontology\.uipath\.com/[^\s<>\"']+")
SYSTEM_FIELDS = {"Id", "CreatedAt", "UpdatedAt", "CreatedBy", "UpdatedBy"}
ENTITY_ID_KEY_RE = re.compile(r"\b(entityId|folderId)\s*:")
ARTIFACT_KINDS = ("schema", "constraints", "functions", "actions", "mapping", "business-rules", "summary", "context")
ONT_TERM_RE = re.compile(r"\bont:([A-Za-z_][\w.-]*(?:\.[A-Za-z_][\w.-]*)?)")
ONTOLOGY_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
SOLUTION_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
ENTITY_FILE_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9]{2,99}\.json$")
WORKDIR_SUBDIRS = {"input", "entities"}
# Extensions accepted by the solution Ontology resource (fileUploadKinds).
ARTIFACT_SUFFIXES = (".yarrrml.yml", ".ofn", ".ttl", ".txt", ".json")


def artifact_suffix(name: str) -> str | None:
    lower = name.lower()
    return next((suffix for suffix in ARTIFACT_SUFFIXES if lower.endswith(suffix)), None)


def classify_turtle(name: str, text: str) -> str:
    lower = name.lower()
    if "business-rules" in lower:
        return "business-rules"
    if "-constraints" in lower or "sh:NodeShape" in text or "sh:targetClass" in text:
        return "constraints"
    if re.search(r"ont:kind\s+(?:\"ACTION\"|'ACTION')", text):
        return "actions"
    if "-functions" in lower or "fno:Function" in text:
        return "functions"
    return "other"


def read_files(workdir: Path, name: str) -> tuple[dict[str, list[tuple[Path, str]]], list[str]]:
    artifacts: dict[str, list[tuple[Path, str]]] = {kind: [] for kind in (*ARTIFACT_KINDS, "other")}
    errors: list[str] = []
    for path in sorted(workdir.iterdir()):
        if path.name.startswith(".") or path.is_dir():
            continue
        if path.is_symlink() or not path.is_file():
            errors.append(f"{path.name}: must be a regular file inside WORKDIR, not a symlink or special file.")
            continue
        suffix = artifact_suffix(path.name)
        if suffix is None:
            errors.append(
                f"Unclassified artifact file: {path.name} (allowed extensions: {', '.join(ARTIFACT_SUFFIXES)}; "
                "a mapping must end in .yarrrml.yml)."
            )
            continue
        if not (path.name.startswith(f"{name}.") or path.name.startswith(f"{name}-")):
            errors.append(f"{path.name}: artifact file names must start with '{name}.' or '{name}-'.")
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            errors.append(f"{path.name}: cannot be read as UTF-8 ({error}).")
            continue
        if suffix == ".ofn":
            kind = "schema"
        elif suffix == ".yarrrml.yml":
            kind = "mapping" if "mappings:" in text else "other"
        elif suffix == ".txt":
            kind = "summary"
        elif suffix == ".json":
            kind = "context"
        else:
            kind = classify_turtle(path.name, text)
        artifacts[kind].append((path, text))
    for path, _ in artifacts["schema"]:
        if path.name != f"{name}.ofn":
            errors.append(f"{path.name}: the schema must be named {name}.ofn.")
    for path, _ in artifacts["mapping"]:
        if path.name != f"{name}-mapping.yarrrml.yml":
            errors.append(f"{path.name}: the mapping must be named {name}-mapping.yarrrml.yml.")
    return artifacts, errors


def is_within(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def path_errors(workdir: Path, name: str, solution_dir: Path | None) -> tuple[list[str], dict]:
    """Validate the WORKDIR layout and SOLUTION_DIR before anything is written or run."""
    errors: list[str] = []
    paths: dict = {"workdir": str(workdir)}
    if not ONTOLOGY_NAME_RE.fullmatch(name):
        errors.append(f"--ontology-name '{name}' must match {ONTOLOGY_NAME_RE.pattern} (it becomes the IRI slug and file prefix).")
    if workdir.name != name:
        errors.append(f"WORKDIR must be a folder named after the ontology ('{name}'); got '{workdir.name}'.")
    for child in sorted(workdir.iterdir()):
        if child.name.startswith(".") or not child.is_dir():
            continue
        if child.is_symlink():
            errors.append(f"{child.name}/: must not be a symlink.")
        elif child.name not in WORKDIR_SUBDIRS:
            errors.append(f"{child.name}/: unexpected folder; WORKDIR holds artifact files plus input/ and entities/ only.")
    handoff = workdir / "input" / "handoff.json"
    if handoff.exists() and (handoff.is_symlink() or not handoff.is_file()):
        errors.append("input/handoff.json must be a regular file, not a symlink.")
    entities = workdir / "entities"
    paths["entities_dir"] = str(entities) if entities.is_dir() else None
    paths["handoff_file"] = str(handoff) if handoff.is_file() else None
    if solution_dir is None:
        return errors, paths
    paths["solution_dir"] = str(solution_dir)
    if is_within(solution_dir, workdir) or is_within(workdir, solution_dir):
        errors.append("SOLUTION_DIR and WORKDIR must be separate folders; neither may contain the other.")
    if not SOLUTION_NAME_RE.fullmatch(solution_dir.name):
        errors.append(f"SOLUTION_DIR folder name '{solution_dir.name}' must match {SOLUTION_NAME_RE.pattern}.")
    if solution_dir.exists():
        projects = sorted(solution_dir.glob("*.uipx")) if solution_dir.is_dir() else []
        if solution_dir.is_symlink() or len(projects) != 1:
            errors.append("SOLUTION_DIR exists but is not a solution folder with exactly one .uipx file; choose a new folder name or an existing solution.")
        paths["solution_state"] = "existing"
    elif not solution_dir.parent.is_dir():
        errors.append(f"SOLUTION_DIR parent {solution_dir.parent} does not exist.")
    else:
        paths["solution_state"] = "new"
    if not entities.is_dir():
        errors.append("entities/ is missing; run ontology_entities.py before building the solution.")
    return errors, paths


def schema_model(
    schema_text: str,
) -> tuple[str, set[str], set[str], set[str], set[str], set[str], set[str]]:
    base_match = re.search(r"Ontology\(<([^>]+)>", schema_text)
    base = base_match.group(1).rstrip("#") if base_match else ""
    classes = set(re.findall(r"Declaration\(Class\(:([\w.-]+)\)\)", schema_text))
    data_props = set(re.findall(r"Declaration\(DataProperty\(:([\w.-]+)\)\)", schema_text))
    object_props = set(re.findall(r"Declaration\(ObjectProperty\(:([\w.-]+)\)\)", schema_text))
    labels = set(re.findall(r"AnnotationAssertion\(rdfs:label\s+:([\w.-]+)\s+", schema_text))
    comments = set(re.findall(r"AnnotationAssertion\(rdfs:comment\s+:([\w.-]+)\s+", schema_text))
    domains = set(
        re.findall(
            r"(?:DataPropertyDomain|ObjectPropertyDomain)\(:[\w.-]+\s+:([\w.-]+)\)",
            schema_text,
        )
    )
    return base, classes, data_props, object_props, labels, comments, domains


def mapping_instantiated_classes(mapping: str) -> set[str]:
    inline = re.findall(r"\[\s*a\s*,\s*ont:([A-Za-z_][\w.-]*)\s*\]", mapping)
    block = re.findall(
        r"(?m)^\s*-\s*-\s*a\s*$\s*^\s*-\s*ont:([A-Za-z_][\w.-]*)\s*$",
        mapping,
    )
    return set(inline) | set(block)


def owl_2_ql_errors(schema_text: str) -> list[str]:
    forbidden = (
        "ObjectUnionOf",
        "ObjectComplementOf",
        "ObjectAllValuesFrom",
        "ObjectMinCardinality",
        "ObjectMaxCardinality",
        "ObjectExactCardinality",
        "DataAllValuesFrom",
        "DataMinCardinality",
        "DataMaxCardinality",
        "DataExactCardinality",
        "ObjectOneOf",
        "DataOneOf",
        "HasKey",
        "FunctionalObjectProperty",
        "FunctionalDataProperty",
        "InverseFunctionalObjectProperty",
        "TransitiveObjectProperty",
    )
    return [
        f"schema uses OWL construct forbidden by the OWL 2 QL profile: {construct}"
        for construct in forbidden
        if re.search(rf"\b{construct}\s*\(", schema_text)
    ]


def gate(gate_id: str, passed: bool, diagnostics: list[str] | None = None) -> dict:
    return {"id": gate_id, "passed": passed, "diagnostics": diagnostics or []}


def artifact_inventory(artifacts: dict[str, list[tuple[Path, str]]]) -> dict[str, list[str]]:
    return {
        kind: [path.name for path, _ in artifacts[kind]]
        for kind in ARTIFACT_KINDS
    }


def parse_handoff(path: Path) -> tuple[dict | None, list[str]]:
    if not path.is_file():
        return None, ["input/handoff.json is required to generate a missing mapping."]
    try:
        handoff = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return None, [f"input/handoff.json must be valid JSON: {error}"]
    if not isinstance(handoff, dict):
        return None, ["input/handoff.json must be a JSON object."]
    return handoff, []


def generation_metadata_errors(handoff: dict | None, classes: set[str], data_props: set[str]) -> list[str]:
    if handoff is None:
        return ["input/handoff.json is required to generate a missing mapping."]
    class_map = handoff.get("CLASS_MAP")
    field_metadata = handoff.get("FIELD_METADATA")
    relationships = handoff.get("RELATIONSHIPS")
    errors: list[str] = []
    if not isinstance(class_map, dict):
        errors.append("handoff.CLASS_MAP must map every schema class to entityName.")
    if not isinstance(field_metadata, dict):
        errors.append("handoff.FIELD_METADATA must provide fields for every mapped class.")
    if errors:
        return errors
    for class_name in sorted(classes):
        entry = class_map.get(class_name)
        if not isinstance(entry, dict) or not entry.get("entityName"):
            errors.append(f"handoff.CLASS_MAP.{class_name} must include entityName.")
        elif {"entityId", "folderId"} & entry.keys():
            errors.append(
                f"handoff.CLASS_MAP.{class_name} must not include entityId or folderId; entities are authored locally and referenced by name."
            )
        fields = field_metadata.get(class_name)
        if not isinstance(fields, dict) or not fields:
            errors.append(f"handoff.FIELD_METADATA.{class_name} must be a non-empty field map.")
            continue
        required_fields = {prop.split(".", 1)[1] for prop in data_props if prop.startswith(f"{class_name}.")}
        missing_fields = sorted(required_fields - set(fields))
        if missing_fields:
            errors.append(f"handoff.FIELD_METADATA.{class_name} is missing schema fields: {', '.join(missing_fields)}.")
        identifier_count = sum(
            isinstance(metadata, dict) and metadata.get("identifier") is True
            for metadata in fields.values()
        )
        if identifier_count != 1:
            errors.append(f"handoff.FIELD_METADATA.{class_name} must mark exactly one identifier field.")
    if not isinstance(relationships, list):
        errors.append(
            "handoff.RELATIONSHIPS must be an explicit list; use [] when the ontology has none."
        )
    return errors


def yaml_without_comments(text: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


def mapping_class_blocks(mapping: str) -> dict[str, str]:
    text = yaml_without_comments(mapping)
    body = text.split("mappings:", 1)[1] if "mappings:" in text else ""
    parts = re.split(r"(?m)^  ([A-Za-z_][\w.-]*):[ \t]*$", body)
    return dict(zip(parts[1::2], parts[2::2]))


def load_local_entities(entities_dir: Path) -> tuple[dict[str, set[str]], list[str]]:
    entities: dict[str, set[str]] = {}
    errors: list[str] = []
    for path in sorted(entities_dir.iterdir()):
        if path.name.startswith(".") or path.name.endswith(".patch.json"):
            continue
        if path.is_symlink() or not path.is_file() or not ENTITY_FILE_RE.fullmatch(path.name):
            errors.append(f"entities/{path.name}: expected only regular {{EntityName}}.json and {{EntityName}}.patch.json files.")
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            errors.append(f"{path.name}: not valid JSON ({error}).")
            continue
        name = record.get("Name") if isinstance(record, dict) else None
        if not isinstance(name, str) or not name:
            errors.append(f"{path.name}: missing entity Name.")
            continue
        if path.stem != name:
            errors.append(f"{path.name}: file name must match its entity Name '{name}'.")
        if not path.with_name(f"{path.stem}.patch.json").is_file():
            errors.append(f"{path.name}: {path.stem}.patch.json is missing; rerun ontology_entities.py.")
        fields = {
            field["Name"]
            for field in record.get("Fields", [])
            if isinstance(field, dict) and isinstance(field.get("Name"), str)
        }
        entities[name] = fields | SYSTEM_FIELDS
    if not entities and not errors:
        errors.append(f"No entity definitions found in {entities_dir}.")
    return entities, errors


def local_entity_errors(mapping: str, entities: dict[str, set[str]]) -> list[str]:
    by_lower = {name.lower(): name for name in entities}
    blocks = mapping_class_blocks(mapping)
    tables = {
        cls: re.findall(r"\btable:\s*['\"]?([A-Za-z_]\w*)", block)
        for cls, block in blocks.items()
    }
    errors: list[str] = []
    used: set[str] = set()
    for cls, block in sorted(blocks.items()):
        if not tables[cls]:
            errors.append(f"mapping {cls} has no table: source.")
            continue
        allowed: set[str] = set()
        for table in tables[cls]:
            entity = by_lower.get(table.lower())
            if entity is None:
                errors.append(
                    f"mapping {cls} reads table {table}, which is not a local entity (have: {', '.join(sorted(entities)) or 'none'})."
                )
                continue
            used.add(entity)
            allowed |= entities[entity]
        for target in re.findall(r"\bmapping:\s*([A-Za-z_][\w.-]*)", block):
            for table in tables.get(target, []):
                entity = by_lower.get(table.lower())
                if entity is not None:
                    allowed |= entities[entity]
        if not allowed:
            continue
        for column in sorted(set(re.findall(r"\$\(([^)\s]+)\)", block)) - allowed):
            errors.append(f"mapping {cls}: column $({column}) is not a field of its entity (names are case-sensitive).")
    errors.extend(f"entity {name} is not used by any mapping table:." for name in sorted(set(entities) - used))
    return errors


def statement_bodies(text: str) -> list[str]:
    pattern = re.compile(
        r"ont:statements?\s+(?:\"\"\"(.*?)\"\"\"|'''(.*?)'''|\"((?:\\.|[^\"])*)\"|'((?:\\.|[^'])*)')",
        flags=re.DOTALL,
    )
    return [next(part for part in match.groups() if part is not None) for match in pattern.finditer(text)]


def action_resources(text: str) -> list[tuple[str, str]]:
    pattern = re.compile(
        r"(?ms)^\s*(?P<subject>[\w.-]+:[\w.-]+)\s+a\s+fno:Function\s*;(?P<body>.*?)(?=^\s*[\w.-]+:[\w.-]+\s+a\s+fno:Function\b|\Z)"
    )
    return [(match.group("subject"), match.group("body")) for match in pattern.finditer(text) if re.search(r"ont:kind\s+(?:\"ACTION\"|'ACTION')", match.group("body"))]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", required=True, type=Path)
    parser.add_argument("--ontology-name", required=True)
    parser.add_argument("--mapping-mode", choices=("auto", "required"), default="auto")
    parser.add_argument("--solution-dir", type=Path, help="Solution folder to create or update; validated before any uip solution command.")
    args = parser.parse_args(argv)

    workdir = args.workdir.expanduser().resolve()
    solution_dir = args.solution_dir.expanduser().resolve() if args.solution_dir else None
    if args.workdir.is_symlink() or not workdir.is_dir():
        diagnostics = [f"WORKDIR {args.workdir} must be an existing folder, not a symlink."]
        print(json.dumps({"status": "FAIL", "gate_results": [gate("PATHS", False, diagnostics)],
                          "errors": {"PATHS": diagnostics}, "warnings": []}, indent=2, sort_keys=True))
        return 1

    errors: dict[str, list[str]] = {}
    warnings: list[str] = []
    results: list[dict] = []
    expected_base = f"https://ontology.uipath.com/{args.ontology_name}"

    layout_errors, paths = path_errors(workdir, args.ontology_name, solution_dir)
    if layout_errors:
        errors["PATHS"] = layout_errors
    results.append(gate("PATHS", not layout_errors, layout_errors))

    artifacts, inventory_errors = read_files(workdir, args.ontology_name)
    inventory = artifact_inventory(artifacts)
    if len(artifacts["schema"]) != 1:
        inventory_errors.append(f"Expected exactly one schema artifact; found {len(artifacts['schema'])}.")
    if len(artifacts["constraints"]) < 1:
        inventory_errors.append("Expected at least one constraints artifact; found 0.")
    if len(artifacts["mapping"]) > 1:
        inventory_errors.append(f"Expected at most one mapping artifact; found {len(artifacts['mapping'])}.")
    for kind in ("summary", "context"):
        if len(artifacts[kind]) > 1:
            inventory_errors.append(f"Expected at most one {kind} artifact; found {len(artifacts[kind])}.")
    inventory_errors.extend(f"Unclassified artifact file: {path.name}" for path, _ in artifacts["other"])
    if inventory_errors:
        errors["ARTIFACT_INVENTORY"] = inventory_errors
    results.append(gate("ARTIFACT_INVENTORY", not inventory_errors, inventory_errors))

    if len(artifacts["schema"]) != 1:
        errors["IRI_CONSISTENCY"] = ["No .ofn schema artifact was found."]
        results.append(gate("IRI_CONSISTENCY", False, errors["IRI_CONSISTENCY"]))
        base, classes, data_props, object_props = "", set(), set(), set()
        labels, comments, domains = set(), set(), set()
    else:
        schema_text = artifacts["schema"][0][1]
        base, classes, data_props, object_props, labels, comments, domains = schema_model(schema_text)
        iri_errors: list[str] = []
        all_text = [text for kind in inventory for _, text in artifacts[kind]]
        observed = {uri.rstrip("#/") for text in all_text for uri in URI_RE.findall(text)
                    if not uri.startswith(GLOBAL_SHAPES.rstrip("#"))}
        if base != expected_base:
            iri_errors.append(f"schema IRI is {base or '<missing>'}; expected {expected_base}")
        allowed_iris = {
            expected_base,
            f"{expected_base}/function",
            f"{expected_base}/action",
            PLATFORM_ONTOLOGY.rstrip("#"),
        }
        for uri in sorted(observed):
            if uri.rstrip("#/") not in {value.rstrip("#/") for value in allowed_iris}:
                iri_errors.append(f"artifact references old or inconsistent IRI: {uri}")
        if iri_errors:
            errors["IRI_CONSISTENCY"] = iri_errors
        results.append(gate("IRI_CONSISTENCY", not iri_errors, iri_errors))

    ql_errors = owl_2_ql_errors(schema_text) if len(artifacts["schema"]) == 1 else []
    if ql_errors:
        errors["OWL_2_QL"] = ql_errors
    results.append(gate("OWL_2_QL", not ql_errors, ql_errors))

    naming_errors = [
        f"data property ont:{prop} uses forbidden has{{Prop}} naming"
        for prop in sorted(data_props)
        if re.fullmatch(r"has[A-Z].*", prop.rsplit(".", 1)[-1])
    ]
    if naming_errors:
        errors["DATA_PROPERTY_NAMING"] = naming_errors
    results.append(gate("DATA_PROPERTY_NAMING", not naming_errors, naming_errors))

    annotation_errors: list[str] = []
    for term in sorted(classes | data_props | object_props):
        missing = [
            annotation
            for annotation, present in (("rdfs:label", labels), ("rdfs:comment", comments))
            if term not in present
        ]
        if missing:
            annotation_errors.append(f"ont:{term} is missing {', '.join(missing)}")
    if annotation_errors:
        errors["CLASS_ANNOTATIONS"] = annotation_errors
    results.append(gate("CLASS_ANNOTATIONS", not annotation_errors, annotation_errors))

    mapping = artifacts["mapping"][0][1] if len(artifacts["mapping"]) == 1 else None
    if mapping is None:
        if args.mapping_mode == "required":
            mapping_status = "BLOCKED_AMBIGUITY"
            errors["MAPPING_TERMS"] = ["Mapping is required but missing."]
        else:
            handoff, handoff_errors = parse_handoff(workdir / "input" / "handoff.json")
            metadata_errors = handoff_errors or generation_metadata_errors(handoff, classes, data_props)
            if classes and not metadata_errors:
                mapping_status = "GENERATE_MAPPING"
                warnings.append("Mapping is absent; generate it from input/handoff.json CLASS_MAP (entityName) and FIELD_METADATA, referring to entities by table: name.")
            else:
                mapping_status = "BLOCKED_AMBIGUITY"
                errors["MAPPING_TERMS"] = metadata_errors or ["Mapping is missing and no schema classes were found for generation."]
    else:
        mapping_status = "PRESENT_VALID"
        terms = set(ONT_TERM_RE.findall(yaml_without_comments(mapping)))
        allowed = classes | data_props | object_props
        unknown = sorted(term for term in terms if term not in allowed)
        if unknown:
            mapping_status = "PRESENT_INVALID"
            errors["MAPPING_TERMS"] = [f"mapping references undeclared schema term ont:{term}" for term in unknown]
    mapping_gate_ok = "MAPPING_TERMS" not in errors
    results.append(gate("MAPPING_TERMS", mapping_gate_ok, errors.get("MAPPING_TERMS", [])))

    local_errors: list[str] = []
    if mapping and ENTITY_ID_KEY_RE.search(yaml_without_comments(mapping)):
        local_errors.append("mapping must not carry entityId or folderId; refer to each entity by name with table: only.")
    if paths["entities_dir"] is None:
        warnings.append("entities/ not found; mapping table: names were not checked against local entities.")
    else:
        entities, load_errors = load_local_entities(workdir / "entities")
        local_errors.extend(load_errors)
        if mapping and entities:
            local_errors.extend(local_entity_errors(mapping, entities))
    if local_errors:
        errors["LOCAL_ENTITIES"] = local_errors
    results.append(gate("LOCAL_ENTITIES", not local_errors, local_errors))

    cross_file_errors: list[str] = []
    allowed = classes | data_props | object_props
    for path, text in artifacts["constraints"]:
        references = re.findall(r"(?:sh:targetClass|sh:path|sh:class)\s+ont:([A-Za-z_][\w.-]*)", text)
        cross_file_errors.extend(
            f"{path.name}: references undeclared schema term ont:{term}"
            for term in references if term not in allowed
        )
    for path, text in artifacts["functions"] + artifacts["actions"]:
        for statement in statement_bodies(text):
            references = ONT_TERM_RE.findall(statement)
            cross_file_errors.extend(
                f"{path.name}: statement references undeclared schema term ont:{term}"
                for term in references if term not in allowed
            )
    if cross_file_errors:
        errors["CROSS_FILE_TERMS"] = cross_file_errors
    results.append(gate("CROSS_FILE_TERMS", not cross_file_errors, cross_file_errors))

    deployability_errors = [
        f"class ont:{class_name} is not the domain of any declared property"
        for class_name in sorted(classes - domains)
    ]
    if mapping:
        instantiated_classes = mapping_instantiated_classes(mapping)
        deployability_errors.extend(
            f"class ont:{class_name} is not instantiated in the mapping"
            for class_name in sorted(classes - instantiated_classes)
        )
    if deployability_errors:
        errors["CLASS_DEPLOYABILITY"] = deployability_errors
    results.append(gate("CLASS_DEPLOYABILITY", not deployability_errors, deployability_errors))

    relationship_errors: list[str] = []
    if mapping:
        exemptions = set(re.findall(r"(?im)^\s*#\s*RELATIONSHIP_EXEMPT:\s*ont:([A-Za-z_][\w.-]*)\s*$", mapping))
        joins: list[str] = []
        for match in re.finditer(r"(?ms)^\s*-\s*p:\s*ont:([A-Za-z_][\w.-]*)\s*\n(.*?)(?=^\s*-\s*p:|\Z)", yaml_without_comments(mapping)):
            term, body = match.groups()
            if re.search(r"(?m)^\s*o:\s*\n.*?\bmapping:\s*", body, flags=re.DOTALL):
                joins.append(term)
        relationship_errors = [
            f"FK join ont:{term} has no declared OWL object property"
            for term in joins if term not in object_props and term not in exemptions
        ]
    if relationship_errors:
        errors["RELATIONSHIP"] = relationship_errors
    results.append(gate("RELATIONSHIP", not relationship_errors, relationship_errors))

    action_errors: list[str] = []
    for path, text in artifacts["actions"]:
        for action, body in action_resources(text):
            returns = re.search(r"fno:returns\s*\(([^)]*)\)", body, flags=re.DOTALL)
            if not returns:
                action_errors.append(f"{path.name}: action {action} has no fno:returns output declaration")
                continue
            output_list = returns.group(1)
            for output in re.findall(r"[\w:.-]+", output_list):
                if not re.search(rf"{re.escape(output)}\s+a\s+fno:Output", text):
                    action_errors.append(f"{path.name}: action {action} returned output {output} lacks fno:Output metadata")
    if action_errors:
        errors["ACTION_CONTRACT"] = action_errors
    results.append(gate("ACTION_CONTRACT", not action_errors, action_errors))

    semantic_errors: list[str] = []
    semantic_errors.extend(
        f"cross-artifact alignment failed: {diagnostic}"
        for diagnostic in cross_file_errors
    )
    if mapping:
        mapped_terms = set(ONT_TERM_RE.findall(yaml_without_comments(mapping)))
        semantic_errors.extend(
            f"mapping alignment failed: ont:{term} is not declared in the schema"
            for term in sorted(mapped_terms - allowed)
        )
        for prop in sorted((data_props | object_props) - mapped_terms):
            semantic_errors.append(f"schema property ont:{prop} is not aligned to the mapping")
        target_classes: set[str] = set()
        for _, text in artifacts["constraints"]:
            target_classes.update(
                re.findall(r"sh:targetClass\s+(?:ont:|:)([A-Za-z_][\w.-]*)", text)
            )
        for class_name in sorted(classes - target_classes):
            semantic_errors.append(
                f"schema class ont:{class_name} has no aligned SHACL targetClass"
            )
    if semantic_errors:
        errors["SEMANTIC_CONSISTENCY"] = semantic_errors
    results.append(gate("SEMANTIC_CONSISTENCY", not semantic_errors, semantic_errors))

    namespace_errors: list[str] = []
    for path, text in artifacts["constraints"]:
        match = re.search(r"@prefix\s+shape:\s*<([^>]+)>", text)
        if match and match.group(1) != GLOBAL_SHAPES:
            namespace_errors.append(f"{path.name}: shape prefix must be {GLOBAL_SHAPES}")
    if namespace_errors:
        errors["NAMESPACE"] = namespace_errors
    results.append(gate("NAMESPACE", not namespace_errors, namespace_errors))

    failed = [item for item in results if not item["passed"]]
    payload = {
        "status": "PASS" if not failed else "FAIL",
        "gate_results": results,
        "mapping_status": mapping_status,
        "artifact_inventory": inventory,
        "paths": paths,
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
