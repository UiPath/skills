#!/usr/bin/env python3
"""Discovery, the RESOURCES table, and BPMN/.uipx parsing shared by every
checker in this suite (check_shape.py, check_behavior.py, test_checks.py).

Every rule in check_shape.py and check_behavior.py iterates RESOURCES so a
second row (v2's RPA leg, Phase 5) plugs in without touching either
checker's control flow -- only this table, and that row's own
context-field spec, grow. Do NOT assume every wrapper kind shares the
releaseKey/folderKey shape verified below for
`Orchestrator.ExecuteApiWorkflowAsync`: Phase 5's `Orchestrator.StartJob`
row must verify its own runtime contract before copying this one (see
SKILL.md rule 18 -- the same broken-template family, not proven identical
per field).

Standard library only, mirroring `_shared/bpmn_live.py`'s dependency policy.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
UIPATH_NS = "http://uipath.org/schema/bpmn"

# Fixture/tooling directories that must never shadow a submitted solution
# during discovery -- a mutation fixture sitting under this task's own
# fixtures/ dir, or an installed node_modules/, must never be found instead
# of the tree actually being graded.
EXCLUDED_DIR_NAMES = {"node_modules", "fixtures", ".git"}

GUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
VARS_REF_RE = re.compile(r"vars\.([A-Za-z0-9_]+)")
RESULT_REF_RE = re.compile(r"(?<![\w.])result\b")
ANY_VARS_RE = re.compile(r"\bvars\b")


class CompositionError(RuntimeError):
    """The submitted tree could not even be parsed against a RESOURCES row."""


def q(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}"


# ---------------------------------------------------------------------------
# RESOURCES table
# ---------------------------------------------------------------------------

RESOURCES: list[dict[str, Any]] = [
    {
        "kind": "API workflow",
        "markers": ("Workflow.json",),
        "project_file": "project.uiproj",
        "wrapper": "Orchestrator.ExecuteApiWorkflowAsync",
        "output": "message",
        # Verified end-to-end for this wrapper (SKILL.md rule 18 /
        # references/registry-workflow.md): the runtime reads `releaseKey`
        # (bound via =bindings.<id> to the resource's real process Key) and
        # a LITERAL `folderKey` (the target folder's real FolderKey GUID)
        # -- never `name`/`folderPath`, and never the template's own
        # (misnamed) `folderId`.
        "context_fields": {
            "releaseKey": {
                "mode": "binding",
                "binding_resource": "process",
                "binding_attr": "Key",
            },
            "folderKey": {"mode": "literal_guid"},
        },
        # The broken registry template's misnamed field -- its presence
        # signals the template was pasted as served rather than fixed per
        # rule 18. Leftover `name`/`folderPath` are harmless and allowed.
        "forbidden_context_fields": ("folderId",),
    },
]


def resource_output_names(resources: Iterable[dict[str, Any]] = RESOURCES) -> list[str]:
    return [row["output"] for row in resources]


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def _is_excluded(root: Path, path: Path) -> bool:
    try:
        rel_parts = path.relative_to(root).parts
    except ValueError:
        rel_parts = path.parts
    return any(part in EXCLUDED_DIR_NAMES for part in rel_parts)


def find_one(root: Path, *patterns: str) -> Optional[Path]:
    """Shortest path (by depth, then lexicographically) matching any glob
    pattern under root. Excludes node_modules/ and fixtures/ so a mutation
    fixture or an installed skill copy can never be found instead of the
    tree actually being graded."""

    candidates: list[Path] = []
    for pattern in patterns:
        for path in root.rglob(pattern):
            if _is_excluded(root, path):
                continue
            candidates.append(path)
    if not candidates:
        return None
    candidates.sort(key=lambda p: (len(p.parts), str(p)))
    return candidates[0]


def find_uipx(root: Path) -> Optional[Path]:
    return find_one(root, "*.uipx")


def find_bpmn(root: Path) -> Optional[Path]:
    return find_one(root, "*.bpmn")


def find_resource_project(root: Path, row: dict[str, Any]) -> Optional[Path]:
    """The row's project directory: holds `project_file` alongside at least
    one of the row's markers."""

    candidates = []
    for candidate in root.rglob(row["project_file"]):
        if _is_excluded(root, candidate):
            continue
        project_dir = candidate.parent
        if any((project_dir / marker).exists() for marker in row["markers"]):
            candidates.append(project_dir)
    if not candidates:
        return None
    candidates.sort(key=lambda p: (len(p.parts), str(p)))
    return candidates[0]


# ---------------------------------------------------------------------------
# .uipx (solution manifest)
# ---------------------------------------------------------------------------

def uipx_project_dirs(uipx_path: Path) -> set[str]:
    """Registered project directories, as POSIX-style paths relative to the
    solution root (the .uipx's own directory)."""

    data = json.loads(uipx_path.read_text(encoding="utf-8"))
    dirs: set[str] = set()
    for project in data.get("Projects", []) or []:
        rel = project.get("ProjectRelativePath")
        if not rel:
            continue
        dirs.add(str(Path(rel.replace("\\", "/")).parent).replace("\\", "/"))
    return dirs


def project_is_registered(uipx_path: Path, project_dir: Path) -> bool:
    solution_root = uipx_path.parent
    try:
        project_rel_dir = str(project_dir.relative_to(solution_root)).replace("\\", "/")
    except ValueError:
        return False
    return project_rel_dir in uipx_project_dirs(uipx_path)


# ---------------------------------------------------------------------------
# BPMN parsing
# ---------------------------------------------------------------------------

def parse_process(bpmn_path: Path) -> ET.Element:
    root = ET.parse(bpmn_path).getroot()
    process = root.find(q(BPMN_NS, "process"))
    if process is None:
        raise CompositionError(f"{bpmn_path}: no bpmn:process element")
    return process


def declared_variables(process: ET.Element) -> dict[str, dict[str, Optional[str]]]:
    """variable id -> {"name", "type", "elementId", "kind"} for every
    uipath:input / uipath:output / uipath:inputOutput declaration."""

    variables_el = process.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'variables')}"
    )
    result: dict[str, dict[str, Optional[str]]] = {}
    if variables_el is None:
        return result
    for child in variables_el:
        tag = child.tag.rsplit("}", 1)[-1]
        if tag not in ("input", "output", "inputOutput"):
            continue
        vid = child.attrib.get("id")
        if not vid:
            continue
        result[vid] = {
            "name": child.attrib.get("name"),
            "type": child.attrib.get("type"),
            "elementId": child.attrib.get("elementId"),
            "kind": tag,
        }
    return result


def bindings_index(process: ET.Element) -> dict[str, dict[str, str]]:
    bindings_el = process.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'bindings')}"
    )
    result: dict[str, dict[str, str]] = {}
    if bindings_el is None:
        return result
    for child in bindings_el:
        if child.tag.rsplit("}", 1)[-1] != "binding":
            continue
        bid = child.attrib.get("id")
        if bid:
            result[bid] = dict(child.attrib)
    return result


def activity_of(element: ET.Element) -> Optional[ET.Element]:
    return element.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'activity')}"
    )


def find_wrapper_task(process: ET.Element, wrapper_type: str) -> Optional[ET.Element]:
    for element in process.iter():
        activity = activity_of(element)
        if activity is None:
            continue
        type_el = activity.find(q(UIPATH_NS, "type"))
        if type_el is not None and type_el.attrib.get("value") == wrapper_type:
            return element
    return None


def context_fields_of(task_element: ET.Element) -> dict[str, dict[str, str]]:
    activity = activity_of(task_element)
    result: dict[str, dict[str, str]] = {}
    if activity is None:
        return result
    context = activity.find(q(UIPATH_NS, "context"))
    if context is None:
        return result
    for child in context:
        if child.tag.rsplit("}", 1)[-1] != "input":
            continue
        name = child.attrib.get("name")
        if name:
            result[name] = dict(child.attrib)
    return result


def job_arguments_text(task_element: ET.Element) -> Optional[str]:
    activity = activity_of(task_element)
    if activity is None:
        return None
    for child in activity:
        if child.tag.rsplit("}", 1)[-1] != "input":
            continue
        if child.attrib.get("name") == "JobArguments":
            return (child.text or "").strip()
    return None


def output_mappings_of(task_element: ET.Element) -> list[dict[str, str]]:
    activity = activity_of(task_element)
    if activity is None:
        return []
    return [
        dict(child.attrib)
        for child in activity
        if child.tag.rsplit("}", 1)[-1] == "output"
    ]


def response_output_vars(task_element: ET.Element) -> set[str]:
    """Vars the node fills from its own response: `source` absent (the whole
    response) or reading `result` and no process variable, e.g.
    `=result.message` but not `=js:result?.message ?? vars.Var_Name`."""

    return {
        mapping["var"]
        for mapping in output_mappings_of(task_element)
        if mapping.get("var")
        and (
            not mapping.get("source")
            or (RESULT_REF_RE.search(mapping["source"]) and not ANY_VARS_RE.search(mapping["source"]))
        )
    }


def all_output_writes(process: ET.Element) -> list[dict[str, str]]:
    """Every `uipath:output` write anywhere in the process, each tagged with
    the id of the element that owns it -- activity-level (a connector or
    API-workflow result, via `output_mappings_of`) and event-mapping-level
    (a start/end event's `uipath:mapping/uipath:output`) alike.

    Lets a shape check catch a second element silently overwriting a
    resource's node-scoped output variable: a decoy scriptTask (or any other
    element) that also declares `uipath:output var="<the invoking node's own
    var>"` would fake per-node provenance without ever calling the resource.
    """

    writes: list[dict[str, str]] = []
    for element in process.iter():
        owner_id = element.attrib.get("id")
        if not owner_id:
            continue
        for mapping in output_mappings_of(element):
            writes.append({**mapping, "owner": owner_id})
        extension = element.find(f"./{q(BPMN_NS, 'extensionElements')}")
        if extension is None:
            continue
        mapping_el = extension.find(q(UIPATH_NS, "mapping"))
        if mapping_el is None:
            continue
        for child in mapping_el:
            if child.tag.rsplit("}", 1)[-1] == "output":
                writes.append({**dict(child.attrib), "owner": owner_id})
    return writes


def end_event_mappings(process: ET.Element) -> list[dict[str, str]]:
    mappings: list[dict[str, str]] = []
    for end in process.iter(q(BPMN_NS, "endEvent")):
        mapping = end.find(
            f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'mapping')}"
        )
        if mapping is None:
            continue
        for child in mapping:
            if child.tag.rsplit("}", 1)[-1] == "output":
                mappings.append(dict(child.attrib))
    return mappings


def var_refs_in(text: Optional[str]) -> set[str]:
    if not text:
        return set()
    return set(VARS_REF_RE.findall(text))


def all_var_refs_in_process(process: ET.Element) -> set[str]:
    """Every `vars.<id>` id referenced anywhere in the process -- attribute
    values and element text alike -- so an undeclared read anywhere (not
    only inside the invoking node) is caught."""

    refs: set[str] = set()
    for element in process.iter():
        for value in element.attrib.values():
            refs |= var_refs_in(value)
        refs |= var_refs_in(element.text)
    return refs


# ---------------------------------------------------------------------------
# entry-points.json
# ---------------------------------------------------------------------------

def load_entry_points(project_dir: Path) -> Optional[dict]:
    path = project_dir / "entry-points.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _first_entry_point(entry_points: Optional[dict]) -> dict:
    if not entry_points:
        return {}
    eps = entry_points.get("entryPoints") or []
    return eps[0] if eps else {}


def entry_point_input_properties(entry_points: Optional[dict]) -> dict:
    return ((_first_entry_point(entry_points).get("input") or {}).get("properties")) or {}


def entry_point_output_properties(entry_points: Optional[dict]) -> dict:
    return ((_first_entry_point(entry_points).get("output") or {}).get("properties")) or {}


# ---------------------------------------------------------------------------
# Resolvers (live implementations live in check_shape.py's main(); these
# type aliases document the contract so tests can inject stand-ins).
# ---------------------------------------------------------------------------

# resolve_release_key(binding: dict[str, str]) -> set[str] | None
# Returns None only to ABSTAIN (structural-only mode, e.g. never_resolves);
# a live resolver that cannot reach the tenant must raise CompositionError
# instead of returning None, and a live resolver that reaches the tenant but
# finds no matching deployed process must return an EMPTY set, never None --
# only a genuine abstention may look like "nothing to compare".
ReleaseKeyResolver = Callable[[dict[str, str]], Optional[set[str]]]
# resolve_folder_key() -> str | None
# None means the same abstention contract as above; a live resolver raises
# CompositionError on failure rather than returning None.
FolderKeyResolver = Callable[[], Optional[str]]


def never_resolves(*_args: Any, **_kwargs: Any) -> None:
    """A resolver that always abstains (returns None) -- used when live
    tenant lookups are not available (e.g. structural-only checks)."""

    return None
