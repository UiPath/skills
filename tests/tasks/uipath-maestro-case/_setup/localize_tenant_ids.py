#!/usr/bin/env python3
"""Rewrite the cloud-tenant IDs a task's fixtures pin to the IDs of the tenant it runs on.

Usage:
    localize_tenant_ids.py

Run as a ``pre_run`` step from the sandbox root. The fixtures were authored on
the shared cloud tenant, and some of them name a resource by its GUID: a
connection ID, a process ``entityKey``, an action app ID. A provisioned tenant
(an ETE) creates the same resources under new GUIDs, so those fixtures point at
nothing there:

  skill-case-e2e-outcome-external      Outlook/Jira ping: Result=Failure
  skill-case-golden-rebuild-cm-expense No process entry found with entityKey ...

``tenant_ids.json`` records what each pinned ID IS (connector and folder, or
process name and folder, or app name). This script finds that resource on the
live tenant, rewrites every sandbox file that carries the cloud ID, and writes
the mapping to ``_setup/.tenant-ids.map.json`` so checkers that read the
reference fixtures can apply the same rewrite (``case_check.localize_ids``).

An ID that exists on the tenant maps to itself, so on the cloud tenant nothing
changes. An ID it cannot resolve is left as it is and reported: some tasks
still grade other criteria without that resource.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

SETUP_DIR = Path(__file__).resolve().parent
MANIFEST = SETUP_DIR / "tenant_ids.json"
MAP_FILE = Path("_setup") / ".tenant-ids.map.json"
RESOURCE_DIR = Path.home() / ".uip" / "case-resources"
PROCESS_INDEXES = (
    "process",
    "agent",
    "api",
    "processOrchestration",
    "caseManagement",
    "flow",
    "function",
    "businessRule",
)
APP_NAME_FIELDS = ("name", "deploymentTitle", "title", "displayName")
SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__"}
KIND_LABELS = {"connections": "connection", "processes": "process", "apps": "app"}
MAX_FILE_BYTES = 5 * 1024 * 1024


def _uip(args: list[str], timeout: int) -> dict:
    proc = subprocess.run(
        ["uip", *args, "--output", "json"], capture_output=True, text=True, timeout=timeout, check=False
    )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"`uip {' '.join(args)}` exited {proc.returncode} with no JSON") from exc
    if payload.get("Result") != "Success":
        raise RuntimeError(f"`uip {' '.join(args)}` failed: {payload.get('Message', payload)}")
    return payload


def _sandbox_files() -> list[Path]:
    files = []
    for root, dirs, names in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            path = Path(root) / name
            if path.resolve() in (MANIFEST, MAP_FILE.resolve()) or path.stat().st_size > MAX_FILE_BYTES:
                continue
            files.append(path)
    return files


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def _resolve_connection(cloud_id: str, spec: dict) -> str | None:
    connections = _uip(["is", "connections", "list", spec["connector"], "--all-folders"], 90).get("Data") or []
    if any(str(c.get("Id", "")).lower() == cloud_id for c in connections):
        return cloud_id
    enabled = [c for c in connections if c.get("State") == "Enabled"]
    in_folder = [c for c in enabled if c.get("Folder") == spec.get("folder")]
    for candidates in (in_folder, enabled):
        if len(candidates) == 1:
            return str(candidates[0]["Id"])
        defaults = [c for c in candidates if c.get("IsDefault")]
        if defaults:
            return str(defaults[0]["Id"])
        if candidates:
            return str(min(candidates, key=lambda c: str(c.get("Name")))["Id"])
    return None


def _load_index(name: str) -> list[dict]:
    path = RESOURCE_DIR / f"{name}-index.json"
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8") or "[]")
    return [entry for entry in data if isinstance(entry, dict)]


def _folder_paths(entry: dict) -> set[str]:
    return {str(f.get("fullyQualifiedName")) for f in entry.get("folders") or [] if isinstance(f, dict)}


def _resolve_process(cloud_id: str, spec: dict, entries: list[dict]) -> str | None:
    if any(str(e.get("entityKey", "")).lower() == cloud_id for e in entries):
        return cloud_id
    in_folder = [e for e in entries if spec["folder"] in _folder_paths(e)]
    named = [e for e in in_folder if e.get("name") == spec["name"]]
    # A solution can deploy its process under a name other than the SDD's (ProjectEuler RPA deploys
    # "RPA Workflow"), so a folder holding exactly one process is still an unambiguous match.
    match = named if len(named) == 1 else in_folder if len(in_folder) == 1 else []
    return str(match[0]["entityKey"]) if match else None


def _resolve_app(cloud_id: str, spec: dict, apps: list[dict]) -> str | None:
    if any(str(a.get("id", "")).lower() == cloud_id for a in apps):
        return cloud_id
    named = [a for a in apps if spec["name"] in {a.get(field) for field in APP_NAME_FIELDS}]
    return str(named[0]["id"]) if len(named) == 1 else None


def _snapshot(directory: Path) -> dict[Path, bytes] | None:
    if not directory.is_dir():
        return None
    return {path: path.read_bytes() for path in directory.iterdir() if path.is_file()}


def _restore(directory: Path, snapshot: dict[Path, bytes] | None) -> None:
    """Put the registry cache back as the task staged it.

    Some tasks grade the agent's own registry pull or a stale cache they start with,
    so the pull this script needs must not leave a fresh cache behind."""
    if not directory.is_dir():
        return
    for path in directory.iterdir():
        if path.is_file() and (snapshot is None or path not in snapshot):
            path.unlink()
    for path, data in (snapshot or {}).items():
        if not path.is_file() or path.read_bytes() != data:
            path.write_bytes(data)
    if snapshot is None and not any(directory.iterdir()):
        directory.rmdir()


def _load_registry() -> tuple[list[dict], list[dict], str | None]:
    """Process and app index entries from a fresh pull; the cache is restored afterwards."""
    snapshot = _snapshot(RESOURCE_DIR)
    try:
        # A failed resource type is reported in Data.Errors and leaves the others usable,
        # so a partial pull is enough.
        _uip(["maestro", "case", "registry", "pull", "--force"], 240)
        processes = [entry for name in PROCESS_INDEXES for entry in _load_index(name)]
        return processes, _load_index("action-apps"), None
    except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return [], [], str(exc)
    finally:
        _restore(RESOURCE_DIR, snapshot)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = {path: text for path in _sandbox_files() if (text := _read_text(path)) is not None}
    corpus = "\n".join(files.values()).lower()
    pinned = {
        cloud_id: (kind, spec)
        for kind in ("connections", "processes", "apps")
        for cloud_id, spec in manifest[kind].items()
        if cloud_id in corpus
    }
    if not pinned:
        print("OK: no pinned tenant IDs in this task")
        return 0

    processes: list[dict] = []
    apps: list[dict] = []
    registry_error = None
    if any(kind != "connections" for kind, _ in pinned.values()):
        processes, apps, registry_error = _load_registry()

    mapping: dict[str, str] = {}
    unresolved: list[str] = []
    for cloud_id, (kind, spec) in sorted(pinned.items()):
        try:
            if kind == "connections":
                live = _resolve_connection(cloud_id, spec)
            elif kind == "processes":
                live = _resolve_process(cloud_id, spec, processes)
            else:
                live = _resolve_app(cloud_id, spec, apps)
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            live = None
            spec = {**spec, "error": str(exc)}
        if live is None:
            if kind != "connections" and registry_error:
                spec = {**spec, "error": f"registry pull failed: {registry_error}"}
            unresolved.append(f"{KIND_LABELS[kind]} {cloud_id} {json.dumps(spec)}")
            continue
        mapping[cloud_id] = live.lower()
        print(f"OK: {KIND_LABELS[kind]} {cloud_id} -> {mapping[cloud_id]}")

    changed = {cloud_id: live for cloud_id, live in mapping.items() if cloud_id != live}
    if changed:
        pattern = re.compile("|".join(re.escape(cloud_id) for cloud_id in changed), re.IGNORECASE)
        for path, text in files.items():
            rewritten = pattern.sub(lambda m: changed[m.group(0).lower()], text)
            if rewritten != text:
                path.write_text(rewritten, encoding="utf-8")
                print(f"rewrote {path}")
    MAP_FILE.parent.mkdir(exist_ok=True)
    MAP_FILE.write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if unresolved:
        print(
            "WARNING: these pinned IDs have no match on this tenant and stay as authored:\n  "
            + "\n  ".join(unresolved),
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
