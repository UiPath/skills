#!/usr/bin/env python3
"""Live helpers for the connector-backed golden graders (Jira release notes, Salesforce
expiring contracts): a `uip` wrapper that reads only the JSON envelope, the run user's one
connection per connector, the agent's workflow and its declared inputs, and a signed-in
workflow run (connector activities refuse `--no-auth`).

An InfraError means the run says nothing about the agent: a missing or ambiguous
connection, an unreadable CLI answer, a provider outage. Graders exit INFRA_EXIT for it.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evals" / "_setup"))
from eval_scoring import run_row  # noqa: E402

INFRA_EXIT = 3
PROVIDER_REFUSAL = re.compile(r"\b429\b|rate.?limit|insufficient_quota|\b50[234]\b|service unavailable",
                              re.IGNORECASE)


class InfraError(Exception):
    pass


def uip(*args, timeout=120):
    """The envelope `uip <args> --output json` prints. stderr is dropped: a merged CLI
    notice ("Checking today's update ...") would make the JSON unparseable."""
    label = " ".join(args[:4])
    try:
        proc = subprocess.run(["uip", *args, "--output", "json"], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise InfraError(f"uip {label}: {type(exc).__name__}") from exc
    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise InfraError(f"uip {label} printed no JSON (exit {proc.returncode})") from exc
    if not isinstance(envelope, dict):
        raise InfraError(f"uip {label} printed a non-object envelope")
    return envelope


def data(*args, timeout=120):
    """`Data` of a Success envelope; anything else is an InfraError naming the call."""
    envelope = uip(*args, timeout=timeout)
    if envelope.get("Result") != "Success":
        detail = {key: envelope[key] for key in ("ErrorCode", "Message") if key in envelope}
        raise InfraError(f"uip {' '.join(args[:4])} failed: {json.dumps(detail)[:300]}")
    return envelope.get("Data")


def field(record, name):
    """`record[name]`, matching the key case-insensitively (the CLI and the providers
    disagree on casing: `Id` vs `id`, `key` vs `Key`)."""
    if not isinstance(record, dict):
        return None
    for key, value in record.items():
        if key.lower() == name.lower():
            return value
    return None


def dicts_in(value):
    """Every dict in `value` at any depth (the CLI's list payloads nest their records)."""
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from dicts_in(item)
    elif isinstance(value, list):
        for item in value:
            yield from dicts_in(item)


def connection_id(connector_key):
    """The one Enabled `connector_key` connection the run user can list, across folders.
    None or several is an InfraError: the agent could not have bound the right one."""
    rows = data("is", "connections", "list", connector_key, "--all-folders", "--refresh")
    rows = [row for row in rows or [] if str(field(row, "ConnectorKey") or "").lower() == connector_key]
    enabled = [row for row in rows if str(field(row, "State") or "").lower() == "enabled"]
    if len(enabled) != 1:
        raise InfraError(f"expected one Enabled {connector_key} connection, found {len(enabled)} of {len(rows)}")
    return field(enabled[0], "Id")


def find_workflow(root="."):
    """The first Workflow.json inside a project folder, in the same order as the task
    YAML's `find | LC_ALL=C sort | head -1` checks."""
    root = Path(root).resolve()
    found = sorted((p for p in root.rglob("Workflow.json") if p.parent != root and "node_modules" not in p.parts),
                   key=str)
    return found[0] if found else None


def declared_inputs(workflow):
    """{name: schema} of the workflow's declared inputs (at most 20)."""
    schema = field(field(workflow, "input"), "schema")
    properties = field(field(schema, "document"), "properties")
    if not isinstance(properties, dict):
        return {}
    return {name: spec if isinstance(spec, dict) else {} for name, spec in list(properties.items())[:20]}


def run_workflow(workflow_path, inputs, timeout):
    """(ok, raw output, error) of a signed-in run of the agent's workflow."""
    try:
        return run_row(workflow_path, inputs, timeout=timeout, no_auth=False)
    except OSError as exc:
        raise InfraError(f"cannot run uip: {exc}") from exc


def strings_in(value):
    """Every string in `value` at any depth, keys included. A string holding JSON (a model
    answer passed through verbatim) is decoded too, so its contents count."""
    found = []
    if isinstance(value, str):
        found.append(value)
        decoded = decode_json_string(value)
        if decoded is not None:
            found += strings_in(decoded)
    elif isinstance(value, dict):
        for key, item in value.items():
            found.append(str(key))
            found += strings_in(item)
    elif isinstance(value, list):
        for item in value:
            found += strings_in(item)
    return found


def decode_json_string(value):
    """The object or list a string holds as JSON, else None."""
    text = value.strip()
    if not text or text[0] not in "[{":
        return None
    try:
        decoded = json.loads(text)
    except ValueError:
        return None
    return decoded if isinstance(decoded, (dict, list)) else None
