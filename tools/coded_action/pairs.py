"""Find the (action TTL, job) pairs in a workdir, and read the schema terms they resolve against.

Discovery is by filename convention: `{ontology}-{action}.ttl` beside `jobs/{action}.ts`. An
action named in the TTL with no job, or a job with no TTL, is reported rather than skipped -- a
half-pair is the failure the caller wants to hear about.
"""

from __future__ import annotations

import re
from pathlib import Path

from coded_action.action_model import ttl_model


SUPPORTED_JOB_LANGUAGES = ("typescript",)


JOB_LANGUAGES = {".ts": "typescript", ".js": "javascript", ".py": "python", ".cs": "csharp", ".java": "java"}


def schema_terms(schema_text: str) -> tuple[set[str], set[str], set[str]]:
    """(classes, data properties, identity properties) declared by the local .ofn.

    Identity is the third one because it is annotation-only: PropertyKind is read from
    `AnnotationAssertion(:datatype :X.y "key")` and is never inferred from the XSD range. A
    property carrying no `ont:datatype` is TEXT, so a schema with no annotated key gives its class
    no identity at all -- and every write then dies AFTER the job has run, with
    `Entity 'X' has no identity property` on the `Preparing write statement` step.
    """
    classes = set(re.findall(r"Declaration\(Class\(:([\w.-]+)\)\)", schema_text))
    data_props = set(re.findall(r"Declaration\(DataProperty\(:([\w.-]+)\)\)", schema_text))
    # The annotation is matched by local name, so any prefix bound to the ontology's own namespace
    # is correct; only the property it targets and the "key" token matter here.
    keys = set(re.findall(r'AnnotationAssertion\(\s*:?[\w.-]*datatype\s+:([\w.-]+)\s+"key"\s*\)',
                          schema_text))
    return classes, data_props, keys


def discover(workdir: Path, ontology: str, wanted: list[str]) -> tuple[list[dict], list[str], list[str]]:
    """Coded-action pairs in `workdir`, plus the TTL files that are not coded actions."""
    pairs: list[dict] = []
    other: list[str] = []
    errors: list[str] = []
    jobs_dir = workdir / "jobs"
    for path in sorted(workdir.glob(f"{ontology}-*.ttl")):
        action = path.name[len(ontology) + 1 : -len(".ttl")]
        if wanted and action not in wanted:
            continue
        text = path.read_text(encoding="utf-8")
        model = ttl_model(text)
        if not model["actions"]:
            other.append(path.name)
            continue
        jobs = sorted(p for p in jobs_dir.glob(f"{action}.*") if p.is_file() and p.stem == action)
        pairs.append({"action": action, "ttl": path, "model": model, "jobs": jobs})
    found = {pair["action"] for pair in pairs}
    errors.extend(
        f"--action {action}: no {ontology}-{action}.ttl declaring ont:language \"CODED\" in {workdir}"
        for action in wanted
        if action not in found
    )
    if not wanted and not pairs:
        errors.append(f"no coded-action pairs found: no {ontology}-*.ttl declares ont:language \"CODED\"")
    return pairs, other, errors
