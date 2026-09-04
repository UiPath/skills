#!/usr/bin/env python3
"""Local, dependency-free preflight checks for UiPath ontology artifacts."""

from __future__ import annotations

import argparse
import json
import re

# Turtle is whitespace-insensitive and both contract guides align their predicates in columns, so
# a fixed-space literal misses every conformant file. It used to, and the consequence was silent:
# an action file fell through to the fno:Function branch, `actions` came back empty, ACTION_CONTRACT
# passed vacuously, and a caller consuming artifact_inventory uploaded actions as --type functions.
ACTION_KIND = re.compile(r"""ont:kind\s+["']ACTION["']""")
import sys
from pathlib import Path


GLOBAL_SHAPES = "https://ontology.uipath.com/shapes#"
PLATFORM_ONTOLOGY = "https://ontology.uipath.com/ont#"
GATES = (
    "ARTIFACT_INVENTORY",
    "IRI_CONSISTENCY",
    "OWL_2_QL",
    "DATA_PROPERTY_NAMING",
    "CLASS_ANNOTATIONS",
    "MAPPING_TERMS",
    "CROSS_FILE_TERMS",
    "CLASS_DEPLOYABILITY",
    "RELATIONSHIP",
    "ACTION_CONTRACT",
    "SEMANTIC_CONSISTENCY",
    "NAMESPACE",
)
URI_RE = re.compile(r"https://ontology\.uipath\.com/[^\s<>\"']+")
ONT_TERM_RE = re.compile(r"\bont:([A-Za-z_][\w.-]*(?:\.[A-Za-z_][\w.-]*)?)")


def read_files(workdir: Path) -> dict[str, list[tuple[Path, str]]]:
    files = [(p, p.read_text(encoding="utf-8")) for p in sorted(workdir.iterdir()) if p.is_file()]
    artifacts = {"schema": [], "constraints": [], "functions": [], "actions": [], "mapping": [], "other": []}
    for path, text in files:
        suffix = path.suffix.lower()
        if suffix == ".ofn":
            artifacts["schema"].append((path, text))
        elif suffix in {".yml", ".yaml"}:
            if "prefixes:" in text:
                artifacts["mapping"].append((path, text))
            else:
                artifacts["other"].append((path, text))
        elif suffix in {".ttl", ".turtle"}:
            if "sh:NodeShape" in text or "sh:targetClass" in text or "constraints" in path.name.lower():
                artifacts["constraints"].append((path, text))
            elif ACTION_KIND.search(text) or "action" in path.name.lower():
                artifacts["actions"].append((path, text))
            elif "fno:Function" in text:
                artifacts["functions"].append((path, text))
            else:
                artifacts["other"].append((path, text))
        else:
            artifacts["other"].append((path, text))
    return artifacts


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
        for kind in ("schema", "constraints", "functions", "actions", "mapping")
    }


def parse_handoff(raw: str | None) -> tuple[dict | None, list[str]]:
    if raw is None:
        return None, ["Machine-readable --handoff JSON is required to generate a missing mapping."]
    try:
        handoff = json.loads(raw)
    except json.JSONDecodeError as error:
        return None, [f"--handoff must be valid JSON: {error.msg}"]
    if not isinstance(handoff, dict):
        return None, ["--handoff JSON must be an object."]
    return handoff, []


def generation_metadata_errors(handoff: dict | None, classes: set[str], data_props: set[str]) -> list[str]:
    if handoff is None:
        return ["Machine-readable --handoff JSON is required to generate a missing mapping."]
    class_map = handoff.get("CLASS_MAP")
    field_metadata = handoff.get("FIELD_METADATA")
    relationships = handoff.get("RELATIONSHIPS")
    errors: list[str] = []
    if not isinstance(class_map, dict):
        errors.append("--handoff.CLASS_MAP must map every schema class to entityId and folderId.")
    if not isinstance(field_metadata, dict):
        errors.append("--handoff.FIELD_METADATA must provide fields for every mapped class.")
    if errors:
        return errors
    for class_name in sorted(classes):
        entry = class_map.get(class_name)
        if (
            not isinstance(entry, dict)
            or not entry.get("entityName")
            or not entry.get("entityId")
            or not entry.get("folderId")
        ):
            errors.append(
                f"--handoff.CLASS_MAP.{class_name} must include entityName, entityId, and folderId."
            )
        fields = field_metadata.get(class_name)
        if not isinstance(fields, dict) or not fields:
            errors.append(f"--handoff.FIELD_METADATA.{class_name} must be a non-empty field map.")
            continue
        required_fields = {prop.split(".", 1)[1] for prop in data_props if prop.startswith(f"{class_name}.")}
        missing_fields = sorted(required_fields - set(fields))
        if missing_fields:
            errors.append(f"--handoff.FIELD_METADATA.{class_name} is missing schema fields: {', '.join(missing_fields)}.")
        identifier_count = sum(
            isinstance(metadata, dict) and metadata.get("identifier") is True
            for metadata in fields.values()
        )
        if identifier_count != 1:
            errors.append(f"--handoff.FIELD_METADATA.{class_name} must mark exactly one identifier field.")
    if not isinstance(relationships, list):
        errors.append(
            "--handoff.RELATIONSHIPS must be an explicit list; use [] when the ontology has none."
        )
    return errors


def yaml_without_comments(text: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


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
    parser.add_argument("--handoff", help="Machine-readable JSON containing CLASS_MAP and FIELD_METADATA for mapping generation.")
    args = parser.parse_args(argv)

    artifacts = read_files(args.workdir)
    errors: dict[str, list[str]] = {}
    warnings: list[str] = []
    results: list[dict] = []
    expected_base = f"https://ontology.uipath.com/{args.ontology_name}"

    inventory = artifact_inventory(artifacts)
    inventory_errors: list[str] = []
    if len(artifacts["schema"]) != 1:
        inventory_errors.append(f"Expected exactly one schema artifact; found {len(artifacts['schema'])}.")
    if len(artifacts["constraints"]) != 1:
        inventory_errors.append(f"Expected exactly one constraints artifact; found {len(artifacts['constraints'])}.")
    if len(artifacts["mapping"]) > 1:
        inventory_errors.append(f"Expected at most one mapping artifact; found {len(artifacts['mapping'])}.")
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
            handoff, handoff_errors = parse_handoff(args.handoff)
            metadata_errors = handoff_errors or generation_metadata_errors(handoff, classes, data_props)
            if classes and not metadata_errors:
                mapping_status = "GENERATE_MAPPING"
                warnings.append("Mapping is absent; generate it from --handoff CLASS_MAP and FIELD_METADATA before deployment.")
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
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
