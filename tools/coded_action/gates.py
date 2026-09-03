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

from coded_action.action_model import PENDING_DEPLOY, marker_of
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
        failures.append(f"{name}: no fno:Function named '{name}' with ont:language \"IMPERATIVE\" (found: {others})")
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
            # contract carries its own schema and cannot be lowered, so the deploy step would keep
            # whatever manifest is already in the project -- in template mode, the skeleton's
            # exemplar contract -- and the job would deploy under the wrong input schema.
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
    log: GateLog, name: str, action: dict, edits: dict | None, schema: tuple[set[str], set[str]] | None, reason: str
) -> None:
    if schema is None:
        log.add("fields-exist-in-schema", "skipped", f"{name}: {reason}")
        return
    classes, data_props = schema
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


def classify_folder_id(name: str, action: dict) -> tuple[bool, str]:
    """(deployable, detail) for one action's ont:processFolderId. Not a gate.

    This used to log a gate that always passed, which is worse than no gate: a `passed` row
    teaches the caller that a check ran and could have failed. It cannot. The placeholder is the
    EXPECTED state between generation and deploy, so there is nothing here to fail on -- the
    answer is a classification, and callers sequence on it through `pairs[].deployable`.
    """
    folder = action["processFolderId"]
    if folder == PENDING_DEPLOY:
        return False, f"{name}: ont:processFolderId is the {PENDING_DEPLOY} placeholder; publish first, then patch it"
    if folder.isdigit():
        return True, f"{name}: ont:processFolderId is {folder}"
    if not folder:
        return False, f"{name}: no ont:processFolderId; the service-wide fallback applies, which is rarely wanted"
    return False, f"{name}: ont:processFolderId {folder!r} is neither numeric nor {PENDING_DEPLOY}"


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
