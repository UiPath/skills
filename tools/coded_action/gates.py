"""The nine gates: each a predicate over one pair, each reporting through the GateLog.

No gate reads the filesystem and none of them decides anything -- they observe and report, and the
entry point decides the exit code. That split is what makes them cheap to reason about: a gate that
cannot answer says "skipped" with a reason, and a skip never counts as a pass.

The ordering of log.add calls within a gate is part of the output contract, since diagnostics are
emitted in call order. tests/coded_action_preflight/golden/support.json pins it.
"""

from __future__ import annotations

import re
from pathlib import Path

from coded_action.action_model import PROCESS_TYPES, marker_of
from coded_action.contract import foreign_idiom, load_deriver
from coded_action.pairs import JOB_LANGUAGES, SUPPORTED_JOB_LANGUAGES
from coded_action.verdict import GateLog


def check_ttl(log: GateLog, name: str, pair: dict) -> dict | None:
    """The ported ttl_actions validate rules that text can check. Returns the action, or None."""
    model = pair["model"]
    failures = [f"{name}: statement for {subject} is not terminated with '.'" for subject in model["unterminated"]]
    for subject, bodies in model["nodes"].items():
        if len(bodies) > 1:
            failures.append(
                f"{name}: subject '{subject}' is defined {len(bodies)} times; RDF merges these, so "
                f"ont:writes becomes the union of both and ont:process becomes ambiguous"
            )
    action = next(
        (candidate for candidate in model["actions"].values() if candidate["name"] == name),
        None,
    )
    if action is None:
        others = ", ".join(sorted(model["actions"])) or "none"
        failures.append(f"{name}: no fno:Function named '{name}' with ont:language \"CODED\" (found: {others})")
        for failure in failures:
            log.add("ttl-parses-and-well-formed", "failed", failure)
        return None

    if not action["statements_is_list"]:
        failures.append(
            f"{name}: ont:statements must be an RDF list ( \"func:...\" ), found a plain string "
            f"{action['statements_scalar']!r}"
        )
    elif len(action["statements"]) != 1:
        failures.append(f"{name}: expected exactly one func: marker, found {len(action['statements'])}")
    elif marker_of(action) is None:
        failures.append(f"{name}: statement is not a func:name(args) marker: {action['statements'][0]!r}")

    for node, read in action["read_nodes"].items():
        if not read["defined"]:
            failures.append(f"{name}: ont:reads names {node}, which no statement in the file defines")
        elif not read["bindsTo"]:
            failures.append(f"{name}: read '{node}' has no ont:bindsTo")
        elif not read["statement"]:
            failures.append(f"{name}: read '{read['bindsTo']}' has no ont:statement")
    for node, param in action["params"].items():
        if not param["defined"]:
            failures.append(f"{name}: fno:expects names {node}, which no statement in the file defines")
        elif not param["paramName"]:
            failures.append(f"{name}: parameter '{node}' has no ont:paramName")

    if not action["process"]:
        failures.append(f"{name}: coded action declares no ont:process")
    if action["writes_is_list"]:
        failures.append(
            f"{name}: ont:writes is written as an RDF list; it must be repeated triples "
            f"(ont:writes \"A.b\", \"C.d\"), or the runtime sees zero writable targets"
        )
    elif not action["writes"]:
        failures.append(f"{name}: declares no ont:writes; every edit its job returns would be rejected")

    for failure in failures:
        log.add("ttl-parses-and-well-formed", "failed", failure)
    if not failures:
        log.add("ttl-parses-and-well-formed", "passed")
    return action


def check_signature(log: GateLog, name: str, action: dict) -> list[str] | None:
    marker = marker_of(action)
    if marker is None:
        log.add("signature-resolves", "skipped", f"{name}: no single well-formed func: marker to resolve against")
        return None
    marker_args = marker[1]
    params = [param["paramName"] for param in action["params"].values() if param["paramName"]]
    binds = [read["bindsTo"] for read in action["read_nodes"].values() if read["bindsTo"]]
    declared = set(params) | set(binds)
    unresolved = [arg for arg in marker_args if arg not in declared]
    unnamed = [bind for bind in binds if bind not in marker_args]
    if unresolved or unnamed:
        parts = []
        if unresolved:
            parts.append(f"arguments naming neither a parameter nor a read: {unresolved}")
        if unnamed:
            parts.append(f"reads the marker never names (fetched then discarded): {unnamed}")
        log.add("signature-resolves", "failed", f"{name}: " + "; ".join(parts))
    else:
        log.add("signature-resolves", "passed")
    return marker_args


def check_input(log: GateLog, name: str, marker_args: list[str], fields: list[str] | None, missing_msg: str) -> None:
    if fields is None:
        log.add("input-matches-marker", "failed", f"{name}: {missing_msg}")
        return
    missing = [arg for arg in marker_args if arg not in fields]
    extra = [field for field in fields if field not in marker_args]
    if missing or extra:
        detail = []
        if missing:
            detail.append(f"marker declares {missing}, absent from Input")
        if extra:
            detail.append(
                f"Input declares {extra}, which the marker never sends; the SDK validates with "
                f"additionalProperties:false, so the job faults before the handler runs"
            )
        log.add("input-matches-marker", "failed", f"{name}: " + "; ".join(detail))
    else:
        log.add("input-matches-marker", "passed")


def check_strictness(log: GateLog, name: str, job_path, src: str) -> None:
    """input-strictness: additionalProperties:false is what faults a drifted Input before the
    handler runs, so every contract has to end up carrying it.

    A type<T>() contract is inert on its own; the manifest is derived from its interfaces at stage
    time, and that derivation is what supplies additionalProperties:false. Running the deriver
    here is therefore the real check: it fails on exactly the contracts that could not produce a
    manifest, and a job that cannot be lowered would otherwise fail at pack time with nothing
    written.
    """
    module = load_deriver()
    if module is None:
        log.add("input-strictness", "skipped",
                f"{name}: tools/entry_points.py not found, cannot lower the type<T>() contract")
        return
    try:
        input_schema, _ = module.derive(job_path)
    except Exception as exc:
        library = foreign_idiom(src)
        if library:
            # Naming the library is not the point; naming what it costs at deploy time is. Such a
            # contract carries its own schema and cannot be lowered. The deploy step refuses
            # rather than keeping whatever manifest is already in the project, because such a
            # manifest came from another job and would deploy this one under a foreign schema.
            detail = (
                f"the contract is declared with {library}, which this pipeline cannot deploy: it "
                f"stages a derived entry-points.json and only the type<T>() idiom can be lowered. "
                f"Declare the contract as plain interfaces behind type<T>()"
            )
        else:
            detail = (
                f"the type<T>() contract cannot be lowered to a manifest, so the deploy step could "
                f"not derive entry-points.json and pack would fail: {exc}"
            )
        log.add("input-strictness", "failed", f"{name}: {detail}")
        return
    if input_schema.get("additionalProperties") is False:
        log.add("input-strictness", "passed")
    else:
        log.add("input-strictness", "failed",
                f"{name}: the derived input schema does not carry additionalProperties:false, so "
                f"a drifted Input would reach the handler instead of faulting")


def check_writes(log: GateLog, name: str, action: dict, edits: dict) -> None:
    writes = set(action["writes"])
    if edits["unresolved"]:
        log.add(
            "writes-cover-edits",
            "failed",
            f"{name}: could not trace the properties of the edit(s) on "
            + ", ".join(edits["unresolved"])
            + "; the edit shape is one this checker does not recognise, so verify by hand",
        )
        return
    if not edits["pairs"]:
        log.add(
            "writes-cover-edits",
            "failed",
            f"{name}: found no written properties in the job; either it never writes, or the edit "
            f"shape is one this checker does not recognise, so verify by hand",
        )
        return
    undeclared = sorted(
        f"{entity}.{key}"
        for entity, key in edits["pairs"]
        if entity not in writes and f"{entity}.{key}" not in writes
    )
    if undeclared:
        log.add(
            "writes-cover-edits",
            "failed",
            f"{name}: the job writes {undeclared} which ont:writes does not cover ({sorted(writes)}); "
            f"the runtime refuses these at 'Preparing write statement' with SQL_GUARD_REJECTED, "
            f"after the job has already run",
        )
    else:
        log.add("writes-cover-edits", "passed")


def check_fields(
    log: GateLog, name: str, action: dict, edits: dict | None, schema: tuple[set[str], set[str], set[str]] | None, reason: str
) -> None:
    if schema is None:
        log.add("fields-exist-in-schema", "skipped", f"{name}: {reason}")
        return
    classes, data_props, _keys = schema
    wanted = set(action["writes"])
    for read in action["read_nodes"].values():
        wanted.update(re.findall(r"\{\{([^}]+)\}\}", read["statement"]))
    if edits is not None:
        wanted.update(f"{entity}.{key}" for entity, key in edits["pairs"])
    unknown = []
    for entry in sorted(wanted):
        entity, _, field = entry.partition(".")
        if entity not in classes:
            unknown.append(f"{entry} (no such entity)")
        elif field and entry not in data_props:
            unknown.append(f"{entry} (no such field)")
    if unknown:
        log.add(
            "fields-exist-in-schema",
            "failed",
            f"{name}: not declared in the schema: {unknown}; a field named in the TTL or written by "
            f"the job but absent from the .ofn looks fine locally and fails at write time",
        )
    else:
        log.add("fields-exist-in-schema", "passed")


def check_process_type(log: GateLog, name: str, action: dict) -> None:
    """process-type-declared: a coded action must name the runtime that computes it.

    Required because `ont:language "CODED"` says only that a job computes the edits, not what kind
    of job. Naming it here means a second runtime later needs no migration and no defaulting rule,
    and the service rejects a coded action without it as a contract violation -- so catching it
    offline is the difference between a refused upload and one line of prose.
    """
    declared = action.get("processType")
    if declared in PROCESS_TYPES:
        log.add("process-type-declared", "passed")
    elif not declared:
        log.add("process-type-declared", "failed",
                f"{name}: no ont:processType. A coded action must declare the runtime that computes "
                f"it; the only value today is {sorted(PROCESS_TYPES)[0]!r}")
    else:
        log.add("process-type-declared", "failed",
                f"{name}: ont:processType {declared!r} is not a runtime this vocabulary knows "
                f"(expected one of {sorted(PROCESS_TYPES)})")

def check_identity(log: GateLog, name: str, action: dict,
                   schema: tuple[set[str], set[str], set[str]] | None, reason: str) -> None:
    """entity-identity-declared: every entity this action writes has exactly one key property.

    The runtime resolves an edit's target row by the identity property's own NAME, so a written
    entity needs exactly one property annotated `ont:datatype "key"`. Without it the write is
    refused at `Preparing write statement` -- after the job has already run, reporting
    `rowsAffected: 0`, which in a summary is indistinguishable from a legitimate no-op.

    Nothing else catches this. The annotation is absent from a schema written strictly to the OWL
    guide, the artifact uploads and validates cleanly, and the failure appears only at the first
    invoke that tries to write.
    """
    if schema is None:
        log.add("entity-identity-declared", "skipped", f"{name}: {reason}")
        return
    classes, _props, keys = schema
    written = sorted({entry.partition(".")[0] for entry in action["writes"] if entry})
    if not written:
        log.add("entity-identity-declared", "skipped",
                f"{name}: ont:writes names no entity, so there is no identity to require")
        return
    problems = []
    for entity in written:
        if entity not in classes:
            continue  # fields-exist-in-schema owns that failure; do not report it twice
        owned = sorted(k for k in keys if k.partition(".")[0] == entity)
        if not owned:
            problems.append(
                f"{entity} has no property annotated ont:datatype \"key\", so the runtime cannot "
                f"resolve which row an edit targets and the write is refused after the job runs")
        elif len(owned) > 1:
            problems.append(f"{entity} declares {len(owned)} key properties ({', '.join(owned)}); "
                            f"identity must be exactly one")
    if problems:
        log.add("entity-identity-declared", "failed", f"{name}: " + "; ".join(problems))
    else:
        log.add("entity-identity-declared", "passed")


def check_job_language(log: GateLog, name: str, jobs: list[Path]) -> tuple[str, Path | None]:
    if not jobs:
        log.add(
            "job-language",
            "failed",
            f"{name}: no job file at jobs/{name}.* ; a coded action is a TTL plus a job, and the "
            f"TTL alone deploys an action whose process has nothing to run",
        )
        return "", None
    if len(jobs) > 1:
        log.add(
            "job-language",
            "failed",
            f"{name}: {len(jobs)} job files match jobs/{name}.* ({[job.name for job in jobs]}); "
            f"exactly one job implements an action",
        )
        return "", None
    job = jobs[0]
    language = JOB_LANGUAGES.get(job.suffix.lower(), job.suffix.lstrip(".").lower() or "unknown")
    if language not in SUPPORTED_JOB_LANGUAGES:
        log.add(
            "job-language",
            "failed",
            f"{name}: job {job.name} is {language}; supported languages: {', '.join(SUPPORTED_JOB_LANGUAGES)}",
        )
        return language, job
    log.add("job-language", "passed")
    return language, job
