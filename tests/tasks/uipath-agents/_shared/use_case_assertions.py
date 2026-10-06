"""Final-state assertions shared by the low-code use-case tasks.

The use-case tasks under `lowcode/use_cases/` grade only the authored agent
definition — never the CLI trajectory that produced it. Every helper here
reads files from the sandbox (or runs a read-only `uip agent validate` against
them) and exits non-zero with a `FAIL:` line on the first violation, matching
the convention of the other `check_*.py` scripts in this suite.

Resources are always located by content (`$resourceType`, `type`,
`properties.toolType`, ...) rather than by folder name: the prompts describe
capabilities in user language, so the folder name is the agent's choice.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Iterable

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
FILE_READING_TOOL_TYPES = {"analyze-attachments", "load-attachments", "deep-rag"}
VALID_RETRIEVAL_MODES = {"semantic", "structured", "deeprag", "batchtransform"}


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def load(path: Path) -> dict:
    if not path.is_file():
        fail(f"Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        fail(f"{path} is not valid JSON: {e}")


# --- Project-level checks -------------------------------------------------


def assert_valid_project(agent_dir: Path) -> None:
    """Run read-only `uip agent validate` against the final project.

    Validate also fails when derived files (`entry-points.json`) are stale, so
    a pass proves the last edit was followed by a refresh.
    """
    uip = shutil.which("uip")
    if not uip:
        fail("`uip` CLI not found on PATH — cannot validate the final project")
    proc = subprocess.run(
        [uip, "agent", "validate", str(agent_dir), "--output", "json"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    out = proc.stdout
    start = out.find("{")
    try:
        data = json.loads(out[start:]) if start >= 0 else {}
    except json.JSONDecodeError:
        data = {}
    status = (data.get("Data") or {}).get("Status")
    if proc.returncode != 0 or status != "Valid":
        errors = (data.get("Data") or {}).get("Errors") or data.get("Message") or out[-2000:]
        fail(
            f"`uip agent validate {agent_dir.name}` did not report Valid "
            f"(exit={proc.returncode}, status={status!r}): {errors}"
        )
    print(f"OK: uip agent validate reports {agent_dir.name} as Valid")


def assert_project_id(agent: dict) -> str:
    pid = agent.get("projectId")
    if not isinstance(pid, str) or not UUID_RE.match(pid):
        fail(f"projectId is missing or not a UUID: {pid!r}")
    return pid


def assert_autonomous(agent: dict) -> None:
    if (agent.get("metadata") or {}).get("isConversational") is True:
        fail("agent is conversational; the use case needs an autonomous (input → output) agent")
    print("OK: agent is autonomous")


def assert_schema_sync(agent: dict, entry: dict) -> tuple[dict, dict]:
    eps = entry.get("entryPoints")
    if not isinstance(eps, list) or not eps:
        fail("entry-points.json has no entryPoints[0]")
    ep = eps[0]
    if agent.get("inputSchema") != ep.get("input"):
        fail("agent.json.inputSchema != entry-points.json entryPoints[0].input")
    if agent.get("outputSchema") != ep.get("output"):
        fail("agent.json.outputSchema != entry-points.json entryPoints[0].output")
    print("OK: inputSchema/outputSchema in sync with entry-points.json")
    return agent["inputSchema"], agent["outputSchema"]


# --- Schema helpers --------------------------------------------------------


def _resolve(schema: dict, node: dict) -> dict:
    """Follow a local `#/definitions/<name>` $ref one level."""
    ref = node.get("$ref") if isinstance(node, dict) else None
    if isinstance(ref, str) and ref.startswith("#/definitions/"):
        target = (schema.get("definitions") or {}).get(ref.split("/", 2)[2])
        if isinstance(target, dict):
            return target
    return node


def walk_properties(schema: dict) -> dict[str, dict]:
    """Flatten every property name reachable from the root (objects + array items).

    Returns {name: property-node}. A name nested under a wrapper object counts,
    so an output contract may be flat or wrapped in a single result object.
    """
    found: dict[str, dict] = {}

    def visit(node: dict, depth: int) -> None:
        if depth > 6 or not isinstance(node, dict):
            return
        node = _resolve(schema, node)
        for name, prop in (node.get("properties") or {}).items():
            if isinstance(prop, dict):
                found.setdefault(name, _resolve(schema, prop))
                visit(prop, depth + 1)
        items = node.get("items")
        if isinstance(items, dict):
            visit(items, depth + 1)

    visit(schema, 0)
    return found


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def find_property(props: dict[str, dict], *aliases: str) -> tuple[str, dict] | None:
    """Match a property by any alias, ignoring case, `_` and `-`."""
    wanted = {_norm(a) for a in aliases}
    for name, node in props.items():
        if _norm(name) in wanted:
            return name, node
    return None


def assert_has_fields(schema: dict, label: str, fields: dict[str, Iterable[str]]) -> dict[str, dict]:
    """Every logical field must exist under one of its aliases. Returns {field: node}."""
    props = walk_properties(schema)
    matched: dict[str, dict] = {}
    missing = []
    for field, aliases in fields.items():
        hit = find_property(props, field, *aliases)
        if hit is None:
            missing.append(field)
        else:
            matched[field] = hit[1]
    if missing:
        fail(f"{label} is missing field(s) {missing}; found {sorted(props)}")
    print(f"OK: {label} declares {sorted(fields)}")
    return matched


def enum_values(node: dict) -> set[str]:
    node = node.get("items", node) if node.get("type") == "array" else node
    vals = node.get("enum")
    if not isinstance(vals, list):
        vals = [o.get("const") for o in node.get("oneOf") or [] if isinstance(o, dict)]
    return {str(v) for v in vals if v is not None}


def assert_enum(node: dict, label: str, expected: Iterable[str]) -> None:
    """The closed value set must be part of the contract: either a JSON-schema
    enum (enum / oneOf const) or every value spelled out in the field's
    description. The prompts say "one of …" without prescribing `enum`, so a
    documented-in-description contract is accepted too."""
    expected = list(expected)
    got = {_norm(v) for v in enum_values(node)}
    if got:
        missing = [v for v in expected if _norm(v) not in got]
        if missing:
            fail(f"{label} enum is missing {missing}; got {sorted(enum_values(node))}")
        print(f"OK: {label} is an enum covering {sorted(expected)}")
        return
    desc = str(node.get("description") or "")
    if isinstance(node.get("items"), dict):
        desc += " " + str(node["items"].get("description") or "")
    missing = [v for v in expected if not re.search(rf"(?<![A-Za-z0-9_]){re.escape(v)}(?![A-Za-z0-9_])", desc)]
    if missing:
        fail(
            f"{label} must declare its allowed values {expected} as an enum or list them in its "
            f"description; missing {missing} (description={desc.strip()!r})"
        )
    print(f"OK: {label} lists its allowed values {sorted(expected)} in the field description")


def attachment_fields(schema: dict) -> list[str]:
    """Top-level input properties typed as `job-attachment` (directly or as array items)."""
    defs = schema.get("definitions") or {}
    names = []
    for name, prop in (schema.get("properties") or {}).items():
        node = prop.get("items", prop) if isinstance(prop, dict) and prop.get("type") == "array" else prop
        if not isinstance(node, dict):
            continue
        ref = node.get("$ref", "")
        target = defs.get(ref.split("/")[-1]) if ref.startswith("#/definitions/") else node
        if isinstance(target, dict) and target.get("x-uipath-resource-kind") == "JobAttachment":
            names.append(name)
    return names


# --- Messages --------------------------------------------------------------


def message(agent: dict, role: str) -> dict:
    for m in agent.get("messages") or []:
        if isinstance(m, dict) and m.get("role") == role:
            return m
    fail(f"agent.json has no {role} message")


def system_prompt(agent: dict) -> str:
    return message(agent, "system").get("content") or ""


def assert_inputs_referenced(agent: dict, fields: Iterable[str]) -> None:
    """Each input reaches the LLM via `{{input.<field>[.<sub>]}}` in a system or
    user message, with a matching `variable` contentToken (Critical Rules 5/6)."""
    msgs = [m for m in agent.get("messages") or [] if m.get("role") in ("system", "user")]
    for field in fields:
        pattern = re.compile(r"\{\{\s*input\." + re.escape(field) + r"(\.[A-Za-z0-9_]+)*\s*\}\}")
        ok = False
        for m in msgs:
            if not pattern.search(m.get("content") or ""):
                continue
            tokens = m.get("contentTokens") or []
            if any(
                isinstance(t, dict)
                and t.get("type") == "variable"
                and (t.get("rawString") == f"input.{field}" or str(t.get("rawString", "")).startswith(f"input.{field}."))
                for t in tokens
            ):
                ok = True
                break
        if not ok:
            fail(
                f"input.{field} is not templated into the system/user message with a matching "
                "variable contentToken"
            )
    print(f"OK: messages template every input ({', '.join(fields)}) with contentTokens")


# --- Resources -------------------------------------------------------------


def resources(agent_dir: Path) -> list[tuple[Path, dict]]:
    root = agent_dir / "resources"
    if not root.is_dir():
        return []
    out = []
    for path in sorted(root.glob("*/resource.json")):
        try:
            out.append((path, json.loads(path.read_text())))
        except json.JSONDecodeError as e:
            fail(f"{path} is not valid JSON: {e}")
    return out


def find_resources(agent_dir: Path, pred: Callable[[dict], bool]) -> list[tuple[Path, dict]]:
    return [(p, d) for p, d in resources(agent_dir) if pred(d)]


def require_resource(agent_dir: Path, pred: Callable[[dict], bool], what: str) -> tuple[Path, dict]:
    hits = find_resources(agent_dir, pred)
    if not hits:
        kinds = sorted({f"{d.get('$resourceType')}/{d.get('type') or d.get('contextType')}" for _, d in resources(agent_dir)})
        fail(f"no {what} under {agent_dir.name}/resources (found: {kinds or 'none'})")
    path, data = hits[0]
    if not data.get("isEnabled", True):
        fail(f"{what} at {path} is disabled")
    rid = data.get("id")
    if not isinstance(rid, str) or not UUID_RE.match(rid):
        fail(f"{what} at {path} has a missing or non-UUID id: {rid!r}")
    print(f"OK: found {what} at {path.parent.name}/resource.json")
    return path, data


def assert_unique_resource_ids(agent_dir: Path) -> None:
    ids = [d.get("id") for _, d in resources(agent_dir)]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        fail(f"resource ids reused across resources (Anti-pattern 9): {sorted(dupes)}")


def is_file_reading_tool(d: dict) -> bool:
    return (
        d.get("$resourceType") == "tool"
        and d.get("type") == "internal"
        and (d.get("properties") or {}).get("toolType") in FILE_READING_TOOL_TYPES
    )


def is_index_context(index_name: str) -> Callable[[dict], bool]:
    return lambda d: (
        d.get("$resourceType") == "context"
        and d.get("contextType") == "index"
        and d.get("indexName") == index_name
    )


def assert_index_context(resource: dict, folder_path: str) -> None:
    if resource.get("folderPath") != folder_path:
        fail(f"context folderPath should be {folder_path!r}, got {resource.get('folderPath')!r}")
    mode = (resource.get("settings") or {}).get("retrievalMode")
    if mode not in VALID_RETRIEVAL_MODES:
        fail(f"context settings.retrievalMode must be one of {sorted(VALID_RETRIEVAL_MODES)} (lowercase), got {mode!r}")
    print(f"OK: index context in {folder_path!r} with retrievalMode={mode!r}")


def is_integration_tool(connector_key: str, object_pred: Callable[[str], bool]) -> Callable[[dict], bool]:
    def pred(d: dict) -> bool:
        props = d.get("properties") or {}
        conn = props.get("connection") or {}
        return (
            d.get("$resourceType") == "tool"
            and d.get("type") == "integration"
            and (conn.get("connector") or {}).get("key") == connector_key
            and object_pred(str(props.get("objectName") or ""))
        )

    return pred


def assert_integration_wiring(resource: dict) -> dict:
    """Studio Web silent-drop rules from integration-service.md § Gotchas."""
    props = resource.get("properties") or {}
    conn = props.get("connection") or {}
    cid = conn.get("id")
    if not isinstance(cid, str) or not cid:
        fail("IS tool properties.connection.id is empty")
    if (conn.get("solutionProperties") or {}).get("resourceKey") != cid:
        fail("IS tool connection.solutionProperties.resourceKey must equal connection.id")
    folder = conn.get("folder") or {}
    if not folder.get("key") or folder.get("path") != folder.get("key"):
        fail(f"IS tool connection.folder.key/path must both be set and equal, got {folder!r}")
    if conn.get("isDefault") is not False:
        fail(f"IS tool connection.isDefault must be false, got {conn.get('isDefault')!r}")
    icon = resource.get("iconUrl")
    if not isinstance(icon, str) or not icon:
        fail("IS tool iconUrl is empty")
    if not props.get("toolPath") or not props.get("method"):
        fail("IS tool properties.toolPath/method must be populated from the activity metadata")
    for p in props.get("parameters") or []:
        ev = p.get("enumValues")
        if isinstance(ev, list) and any(not isinstance(v, dict) for v in ev):
            fail(f"IS tool parameter {p.get('name')!r} enumValues must be {{name, value}} objects")
    print(f"OK: IS tool wired to connection {conn.get('name')!r} ({cid})")
    return conn


def assert_connection_provisioned(solution_dir: Path, connector_key: str) -> None:
    root = solution_dir / "resources" / "solution_folder" / "connection"
    files = [p for p in root.rglob("*.json")] if root.is_dir() else []
    for p in files:
        try:
            spec = (json.loads(p.read_text()).get("resource") or {}).get("spec") or {}
        except json.JSONDecodeError:
            continue
        if spec.get("connectorKey") == connector_key:
            print(f"OK: solution provisions a {connector_key} connection ({p.relative_to(solution_dir)})")
            return
    fail(
        f"no solution-level connection resource for {connector_key} under "
        "resources/solution_folder/connection/ — solution resources were not refreshed"
    )


def assert_solution_registers(solution_dir: Path, project_names: Iterable[str]) -> None:
    uipx = solution_dir / f"{solution_dir.name}.uipx"
    data = load(uipx)
    paths = " ".join(str(p.get("ProjectRelativePath") or p) for p in data.get("Projects") or [])
    missing = [n for n in project_names if n not in paths]
    if missing:
        fail(f"{uipx.name} does not register project(s) {missing}")
    print(f"OK: {uipx.name} registers {list(project_names)}")


if __name__ == "__main__":
    # `python3 use_case_assertions.py validate <AGENT_DIR> [<AGENT_DIR> ...]`
    # Paths are relative to the sandbox root (the criterion's cwd).
    if len(sys.argv) < 3 or sys.argv[1] != "validate":
        sys.exit("usage: use_case_assertions.py validate <AGENT_DIR> [<AGENT_DIR> ...]")
    for arg in sys.argv[2:]:
        assert_valid_project(Path.cwd() / arg)
