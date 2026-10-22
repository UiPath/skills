#!/usr/bin/env python3
"""Live helpers for the connector-backed golden graders (Jira release notes, Salesforce
expiring contracts): a `uip` wrapper that reads only the JSON envelope, the run user's one
connection per connector, the agent's workflow, its declared inputs and outputs and the
connector calls that would change something when it runs, and a signed-in workflow run
(connector activities refuse `--no-auth`). The VAT grader uses only the helpers that choose
the project to grade.

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
MODEL_CONNECTORS = ("uipath-openai-openai", "uipath-uipath-airdk")
READ_ENDPOINT = re.compile(r"search|query|soql|sosl|jql", re.IGNORECASE)


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
    """The run user's one Enabled `connector_key` connection: the one in their personal
    workspace (the unscoped listing the skill runs first), else the one across all folders
    when the workspace has no Enabled one or cannot be listed. None or several in the scope
    that decides is an InfraError: the agent could not have bound the right one."""
    for scope, where in (((), "in the personal workspace"), (("--all-folders",), "across all folders")):
        try:
            rows = data("is", "connections", "list", connector_key, *scope, "--refresh")
        except InfraError:
            if scope:
                raise
            continue
        rows = [row for row in rows or [] if str(field(row, "ConnectorKey") or "").lower() == connector_key]
        enabled = [row for row in rows if str(field(row, "State") or "").lower() == "enabled"]
        if len(enabled) == 1:
            return field(enabled[0], "Id")
        if enabled:
            break
    raise InfraError(f"expected one Enabled {connector_key} connection {where}, found {len(enabled)} of {len(rows)}")


def workflow_paths(root="."):
    """Every Workflow.json inside a project folder under `root`, in sorted path order. The
    root's own Workflow.json and node_modules are left out."""
    root = Path(root).resolve()
    return sorted((p for p in root.rglob("Workflow.json") if p.parent != root and "node_modules" not in p.parts),
                  key=str)


def read_workflow(path):
    """The workflow object in `path`, or None when it is not a readable JSON object."""
    try:
        workflow = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None
    return workflow if isinstance(workflow, dict) else None


def choose_workflow(fits, answers, root="."):
    """The project to grade, since an agent can leave helper projects beside the one the
    prompt asked for: the first in path order whose workflow `fits` the scenario's input
    contract and `answers` with its output, else the first that fits, else the first
    project, as before. None without a project."""
    paths = workflow_paths(root)
    fitting, answering = [], []
    for path in paths:
        workflow = read_workflow(path)
        if workflow is not None and fits(workflow):
            fitting.append(path)
            if answers(workflow):
                answering.append(path)
    chosen = answering or fitting or paths
    return chosen[0] if chosen else None


def declared_inputs(workflow):
    """{name: schema} of the workflow's declared inputs (at most 20)."""
    return _schema_properties(field(workflow, "input"))


def declared_outputs(workflow):
    """{name: schema} of the workflow's declared outputs (at most 20)."""
    return _schema_properties(field(workflow, "output"))


def _schema_properties(side):
    properties = field(field(field(side, "schema"), "document"), "properties")
    if not isinstance(properties, dict):
        return {}
    return {name: spec if isinstance(spec, dict) else {} for name, spec in list(properties.items())[:20]}


def needed_inputs(workflow):
    """Names of the inputs a run must pass: required by the input schema, with no default."""
    required = field(field(field(field(workflow, "input"), "schema"), "document"), "required")
    if not isinstance(required, list):
        return []
    declared = declared_inputs(workflow)
    return [name for name in required if isinstance(name, str) and "default" not in declared.get(name, {})]


def connector_calls(workflow):
    """(activity name, connector key, method, endpoint) of every Integration Service activity
    in the workflow, the key lowercased and the method uppercased."""
    calls = []
    stack = [(None, workflow)]
    while stack:
        name, node = stack.pop()
        if isinstance(node, dict):
            spec = node.get("with")
            if node.get("call") == "UiPath.IntSvc" and isinstance(spec, dict):
                calls.append((name, str(spec.get("connector") or "").lower(), str(spec.get("method") or "").upper(),
                              str(spec.get("endpoint") or "")))
            stack.extend(node.items())
        elif isinstance(node, list):
            stack.extend((name, item) for item in node)
    return sorted(calls, key=lambda call: str(call[0]))


def side_effects(workflow, reads_from):
    """The workflow's connector calls that would change something or reach someone each time it
    runs, as "<activity> (<connector> <method> <endpoint>)": every Integration Service call but
    a GET or a search or query on `reads_from`, the connector the scenario reads, and the model
    calls of MODEL_CONNECTORS. HTTP Request activities are not looked at: without a connection
    they reach only public endpoints."""
    found = []
    for name, connector, method, endpoint in connector_calls(workflow):
        reads = connector == reads_from and (method == "GET" or READ_ENDPOINT.search(endpoint))
        if connector not in MODEL_CONNECTORS and not reads:
            found.append(f"{name} ({connector} {method} {endpoint})")
    return found


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
