#!/usr/bin/env python3
"""Two-phase check for the coded IS Jira create-issue e2e.

  python3 check_coded_is_jira_create_issue.py shape
  python3 check_coded_is_jira_create_issue.py tenant

`shape` runs offline: validates that the project on disk has the
ActivityMetadata literal, lazy SDK construction, bindings.json
connection entry, and a two-field `connection.jira-coded-eval`
resourceOverwrites block (connectionId + folderKey).

`tenant` runs against the live Jira tenant via `uip is resources run` —
calls `get_issue` against the new issue key (read from
`issue_key.txt` produced by the agent), asserts the summary equals the
seed value, and asserts the issue is filed under the seed `epic_key`
(parent).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.bindings_assertions import (  # noqa: E402
    assert_metadata_field,
    assert_value_field,
    find_resource,
    load_bindings,
)
from _shared.ast_lazy_init_check import find_module_level_llm_clients  # noqa: E402
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("jira-filer")
WORKDIR = Path.cwd()


def _read_text(path: Path) -> str:
    if not path.is_file():
        sys.exit(f"FAIL: missing {path}")
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> dict:
    raw = _read_text(path)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def _load_seed() -> dict:
    for candidate in (WORKDIR / "seed.json", ROOT / "seed.json"):
        if candidate.is_file():
            return _load_json(candidate)
    sys.exit("FAIL: seed.json not found in workdir or project root")


def check_shape() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")

    # 1. bindings.json connection entry
    doc = load_bindings(ROOT / "bindings.json")
    entry = find_resource(doc, resource="connection", key="jira-coded-eval")
    assert_value_field(entry, field="ConnectionId", expected="jira-coded-eval")
    assert_metadata_field(entry, field="UseConnectionService", expected="True")

    # 2. ActivityMetadata literal references curated_create_issue
    literal_found = False
    for candidate in (ROOT / "activities.py", ROOT / "main.py"):
        if candidate.is_file() and "ActivityMetadata(" in candidate.read_text() and "curated_create_issue" in candidate.read_text():
            literal_found = True
            break
    if not literal_found:
        sys.exit(
            "FAIL: no `ActivityMetadata(...)` referencing `curated_create_issue` "
            "in activities.py or main.py."
        )
    print("OK: ActivityMetadata literal for curated_create_issue is present")

    # 3. main.py uses lazy SDK init
    main_py = ROOT / "main.py"
    violations = find_module_level_llm_clients(main_py)
    if violations:
        sys.exit("FAIL: module-level UiPath* construction: " + " | ".join(violations))
    text = main_py.read_text()
    if "invoke_activity" not in text or "connections.retrieve(" not in text:
        sys.exit(
            "FAIL: main.py does not use `sdk.connections.retrieve(<key>)` + "
            "`invoke_activity(...)` — capability runtime pattern missing."
        )
    print("OK: main.py uses lazy UiPath() + retrieve + invoke_activity")

    # 4. resourceOverwrites with the two required fields (NO elementInstanceId)
    uipath_json = _load_json(ROOT / "__uipath" / "uipath.json")
    overwrites = (
        uipath_json.get("runtime", {})
        .get("internalArguments", {})
        .get("resourceOverwrites", {})
    )
    key = "connection.jira-coded-eval"
    if key not in overwrites:
        sys.exit(f"FAIL: __uipath/uipath.json missing resourceOverwrites key `{key}`")
    entry_keys = set(overwrites[key].keys())
    has_conn = "connectionId" in entry_keys or "ConnectionId" in entry_keys
    has_folder = "folderKey" in entry_keys
    if not (has_conn and has_folder):
        sys.exit(
            f"FAIL: resourceOverwrites for `{key}` must carry `connectionId` "
            "(alias `ConnectionId`) and `folderKey` per "
            "`ConnectionResourceOverwrite` (`uipath/platform/common/_bindings.py:100`)."
        )
    if "elementInstanceId" in entry_keys:
        sys.exit(
            f"FAIL: resourceOverwrites for `{key}` contains `elementInstanceId`, "
            "which `ConnectionResourceOverwrite` ignores (`extra=\"ignore\"`). "
            "Remove it — see capability anti-pattern #1."
        )
    print("OK: resourceOverwrites has connectionId + folderKey (and no spurious elementInstanceId)")
    print("PASS: shape checks complete")


def _uip(*args: str, timeout: int = 60) -> dict:
    uip = shutil.which("uip")
    if uip is None:
        sys.exit("FAIL: `uip` not on PATH — required for tenant check")
    proc = subprocess.run(
        [uip, *args, "--output", "json"],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        sys.exit(
            f"FAIL: `uip {' '.join(args)}` exited {proc.returncode}: "
            f"{(proc.stderr or proc.stdout).strip()[:600]}"
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: `uip {' '.join(args)}` non-JSON output: {e}; raw: {proc.stdout[:300]!r}")


def _find_issue_key() -> str:
    """Read the created issue key from the agent's run output (no manual
    bookkeeping file). The agent runs `uip codedagent run main ... --output-file
    out.json`; that file holds the agent's returned output. Tolerant of field
    naming (issueKey / issue_key / key) and of a Data/output/result wrapper."""
    candidates = [ROOT / "out.json", ROOT / "__uipath" / "output.json", WORKDIR / "out.json"]
    field_names = ("issueKey", "issue_key", "key", "issueIdOrKey")
    for path in candidates:
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for blob in (data, *(data.get(w) for w in ("Data", "output", "result") if isinstance(data, dict))):
            if isinstance(blob, dict):
                for k in field_names:
                    v = blob.get(k)
                    if isinstance(v, str) and v.strip():
                        return v.strip()
    sys.exit(
        "FAIL: could not read the created issue key from the agent's run "
        "output. Expected `out.json` (from `uip codedagent run --output-file "
        "out.json`) carrying an `issueKey`/`issue_key` field."
    )


def check_tenant() -> None:
    seed = _load_seed()
    expected_summary = seed["summary"]
    issue_key = _find_issue_key()

    # Resolve the test folder + connection so we can re-read the issue.
    folder = _uip("or", "folders", "get", seed["folder_path"])
    folder_key = (
        folder.get("Key")
        or folder.get("Data", {}).get("Key")
        or folder.get("data", {}).get("Key")
    )
    if not folder_key:
        sys.exit(f"FAIL: could not resolve folder key for {seed['folder_path']!r}: {folder}")

    connections = _uip(
        "is", "connections", "list", "uipath-atlassian-jira",
        "--folder-key", folder_key, "--refresh",
    )
    conn_list = connections.get("Data") if isinstance(connections.get("Data"), list) else []
    match = next((c for c in conn_list if c.get("Name") == seed["connection_name"]), None)
    if not match:
        sys.exit(
            f"FAIL: connection {seed['connection_name']!r} not found in "
            f"{seed['folder_path']!r} (got {[c.get('Name') for c in conn_list]})."
        )
    connection_id = match["Id"]

    # Read the issue back via the curated get the connector supports:
    # `is resources run get <connector> curated_get_issue` with project +
    # issuetype + issueId in the query string (the form that returns fields +
    # parent for this connector).
    result = _uip(
        "is", "resources", "run", "get", "uipath-atlassian-jira",
        "curated_get_issue",
        "--connection-id", connection_id,
        "--query",
        f"project={seed['project_key']}&issuetype={seed['issuetype_id']}&issueId={issue_key}",
        timeout=120,
    )
    fields = (
        result.get("Data", {}).get("fields")
        or result.get("fields")
        or {}
    )
    actual_summary = fields.get("summary")
    if actual_summary != expected_summary:
        sys.exit(
            f"FAIL: Jira issue {issue_key} summary={actual_summary!r}, "
            f"expected {expected_summary!r}. The agent either created the "
            "wrong issue, or `curated_create_issue` silently dropped the "
            "summary field (rename mismatch — see capability doc § Runtime "
            "validation layers, row 3)."
        )
    print(f"OK: Jira issue {issue_key} carries the seed summary")

    # Epic linkage: the issue must be filed under seed `epic_key`. Modern Jira
    # exposes the epic as the unified `parent` field; fall back to scanning
    # field values for the epic key (older epic-link customfield shapes).
    expected_epic = (seed.get("epic_key") or "").strip()
    if expected_epic:
        parent = fields.get("parent") or {}
        parent_key = parent.get("key") if isinstance(parent, dict) else None
        if parent_key != expected_epic:
            scanned = {
                k: v for k, v in fields.items()
                if isinstance(v, str) and v == expected_epic
            }
            if not scanned:
                sys.exit(
                    f"FAIL: Jira issue {issue_key} is not filed under epic "
                    f"{expected_epic!r} (parent={parent_key!r}). The agent did not "
                    "resolve/set the parent/epic-link field on the create call — "
                    "see capability doc § reference-resolution (parent fields)."
                )
        print(f"OK: Jira issue {issue_key} is filed under epic {expected_epic}")
    print("PASS: tenant check complete")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("shape", "tenant"):
        sys.exit("usage: check_coded_is_jira_create_issue.py {shape|tenant}")
    if sys.argv[1] == "shape":
        check_shape()
    else:
        check_tenant()


if __name__ == "__main__":
    main()
