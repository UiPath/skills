#!/usr/bin/env python3
"""Local, dependency-free preflight for UiPath coded-action pairs. The CLI entry point.

    python3 tools/coded_action_preflight.py --workdir DIR --ontology-name NAME
                                           [--action A]... [--skip-typecheck]

One JSON object on stdout, shaped like tools/ontology_preflight.py's: status, gate_results,
artifact_inventory, pairs, errors, warnings. Exit 0 only when no gate failed and nothing went
wrong during discovery. Reads the workdir and nothing else: no service is contacted, nothing is
uploaded, and nothing on disk is modified.

Honoured from the environment: CODED_ACTION_TSC (a TypeScript compiler to use) and
ENTRY_POINTS_TOOL (where to find the contract deriver).

This file owns argparse, the order the gates run in, and the exit code. Why any of it exists, and
what a coded action is, is in coded_action/__init__.py; the checks themselves are in
coded_action/gates.py.

The gate order here is part of the output contract, because diagnostics are emitted in the order
they are logged. tests/coded_action_preflight/golden/support.json pins the whole payload.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# The test suite loads this file with spec_from_file_location, and under that load `tools/` is not
# on sys.path. One line, so `import coded_action.*` resolves under both invocation modes.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from coded_action.gates import (  # noqa: E402
    check_fields,
    check_folder_id,
    check_input,
    check_job_language,
    check_signature,
    check_strictness,
    check_ttl,
    check_writes,
)
from coded_action.job_source import interface_fields, written_edits  # noqa: E402
from coded_action.pairs import SUPPORTED_JOB_LANGUAGES, discover, schema_terms  # noqa: E402
# Re-exported: the test suite path-loads this file and asks it whether a compiler exists.
from coded_action.typecheck import find_tsc, typecheck_job  # noqa: E402,F401
from coded_action.verdict import GATES, GateLog  # noqa: E402



# --------------------------------------------------------------------------- ttl text scanning








# --------------------------------------------------------------------------- job source
# Ported wholesale from the deploy skill's job_source.py: regex, not a TypeScript parser, because
# the job shapes are narrow. Every extraction failure is reported rather than read as "nothing".




# --------------------------------------------------------------------------- schema




# --------------------------------------------------------------------------- gate bookkeeping




# --------------------------------------------------------------------------- typecheck


# --------------------------------------------------------------------------- discovery




# --------------------------------------------------------------------------- gates






















# --------------------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", required=True, type=Path)
    parser.add_argument("--ontology-name", required=True)
    parser.add_argument("--action", action="append", default=[], help="check only this action; repeatable")
    parser.add_argument("--skip-typecheck", action="store_true")
    args = parser.parse_args(argv)

    log = GateLog()
    warnings: list[str] = []
    pairs, other, discovery_errors = discover(args.workdir, args.ontology_name, args.action)

    schema_path = args.workdir / f"{args.ontology_name}.ofn"
    if schema_path.is_file():
        schema = schema_terms(schema_path.read_text(encoding="utf-8"))
        schema_reason = ""
    else:
        schema = None
        schema_reason = f"no schema at {schema_path.name}; entity and field existence cannot be resolved offline"

    reported: list[dict] = []
    for pair in pairs:
        name = pair["action"]
        action = check_ttl(log, name, pair)
        language, job = check_job_language(log, name, pair["jobs"])

        src, edits = None, None
        if job is not None and language in SUPPORTED_JOB_LANGUAGES:
            src = job.read_text(encoding="utf-8")
            edits = written_edits(src)

        marker_args = check_signature(log, name, action) if action else None
        if action is None:
            for gate in ("input-matches-marker", "input-strictness", "writes-cover-edits", "fields-exist-in-schema"):
                log.add(gate, "skipped", f"{name}: the action could not be read from the TTL")
            reported.append(
                {
                    "action": name,
                    "ttl": pair["ttl"].name,
                    "job": job.name if job else None,
                    "job_language": language or None,
                    "process": None,
                    "process_folder_id": None,
                    "deployable": False,
                }
            )
            continue

        job_reason = (
            f"{name}: no job source to read"
            if src is None and job is None
            else f"{name}: job source gates read {', '.join(SUPPORTED_JOB_LANGUAGES)} only, this job is {language}"
        )
        if src is None:
            log.add("input-matches-marker", "skipped", job_reason)
            log.add("input-strictness", "skipped", job_reason)
            log.add("writes-cover-edits", "skipped", job_reason)
            warnings.append(f"{name}: fields-exist-in-schema covered the TTL only; the job's edits were not read")
        else:
            fields = interface_fields(src, "Input")
            if marker_args is None:
                log.add("input-matches-marker", "skipped", f"{name}: no marker arguments to compare Input against")
            elif fields is None:
                # One blame site. A contract this parser cannot read is input-strictness's failure
                # to report, and duplicating it here would just make the author read two gates.
                log.add("input-matches-marker", "skipped",
                        f"{name}: the job's contract could not be read (see input-strictness)")
            else:
                check_input(log, name, marker_args, fields,
                            "could not find `interface Input { ... }` in the job")
            check_strictness(log, name, job, src)
            check_writes(log, name, action, edits)

        check_fields(log, name, action, edits, schema, schema_reason)
        deployable, folder_detail = check_folder_id(log, name, action)
        warnings.append(folder_detail)

        if args.skip_typecheck:
            log.add("typecheck", "skipped", f"{name}: --skip-typecheck")
        elif language != "typescript" or job is None:
            log.add("typecheck", "skipped", f"{name}: typecheck applies to typescript jobs only")
        else:
            status, detail = typecheck_job(job, args.workdir)
            log.add("typecheck", status, f"{name}: {detail}" if detail else "")

        reported.append(
            {
                "action": name,
                "ttl": pair["ttl"].name,
                "job": job.name if job else None,
                "job_language": language or None,
                "process": action["process"],
                "process_folder_id": action["processFolderId"],
                "deployable": deployable,
            }
        )

    results = log.results()
    errors = log.errors()
    if discovery_errors:
        errors["discovery"] = discovery_errors
    failed = discovery_errors or [item for item in results if item["status"] == "failed"]
    payload = {
        "status": "PASS" if not failed else "FAIL",
        "gate_results": results,
        "artifact_inventory": {
            "actions": [pair["ttl"].name for pair in pairs],
            "jobs": [entry["job"] for entry in reported if entry["job"]],
            "schema": [schema_path.name] if schema is not None else [],
            "other": other,
        },
        "pairs": reported,
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
