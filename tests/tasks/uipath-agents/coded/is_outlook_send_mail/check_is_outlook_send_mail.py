#!/usr/bin/env python3
"""Two-phase check for the Outlook multipart e2e.

  shape   — offline assertions on the on-disk project
  tenant  — polls Outlook inbox via the test connection to confirm
            the seed subject token arrived
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
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

ROOT = find_project_root("mailer")
WORKDIR = Path.cwd()


def _read(path: Path) -> str:
    if not path.is_file():
        sys.exit(f"FAIL: missing {path}")
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> dict:
    try:
        return json.loads(_read(path))
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def _load_seed() -> dict:
    for candidate in (WORKDIR / "seed.json", ROOT / "seed.json"):
        if candidate.is_file():
            return _load_json(candidate)
    sys.exit("FAIL: seed.json not found")


def check_shape() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")

    doc = load_bindings(ROOT / "bindings.json")
    entry = find_resource(doc, resource="connection", key="outlook-coded-eval")
    assert_value_field(entry, field="ConnectionId", expected="outlook-coded-eval")
    assert_metadata_field(entry, field="UseConnectionService", expected="True")

    # Multipart literal: must declare content_type and multipart_params.
    literal_text = ""
    for candidate in (ROOT / "activities.py", ROOT / "main.py"):
        if candidate.is_file() and "send-mail-v2" in candidate.read_text():
            literal_text = candidate.read_text()
            break
    if not literal_text:
        sys.exit("FAIL: no ActivityMetadata referencing send-mail-v2 found")
    if "multipart/form-data" not in literal_text:
        sys.exit(
            "FAIL: ActivityMetadata literal does not set "
            "`content_type=\"multipart/form-data\"` — defaulting to JSON "
            "returns vendor 400 'Unable to parse multipart body'."
        )
    if "multipart_params" not in literal_text:
        sys.exit(
            "FAIL: ActivityMetadata literal is missing `multipart_params=[...]` "
            "— compact `describe` output filters these; agent must harvest "
            "them from the raw schema cache."
        )
    if "json_body_section" not in literal_text:
        sys.exit(
            "FAIL: ActivityMetadata literal is missing `json_body_section=` — "
            "multipart wrapper key required to package the JSON body section."
        )
    print("OK: ActivityMetadata declares multipart/form-data + multipart_params + json_body_section")

    main_py = ROOT / "main.py"
    violations = find_module_level_llm_clients(main_py)
    if violations:
        sys.exit("FAIL: module-level UiPath* construction: " + " | ".join(violations))
    print("OK: main.py uses lazy UiPath() construction")

    uipath_json = _load_json(ROOT / "__uipath" / "uipath.json")
    overwrites = (
        uipath_json.get("runtime", {})
        .get("internalArguments", {})
        .get("resourceOverwrites", {})
    )
    key = "connection.outlook-coded-eval"
    if key not in overwrites:
        sys.exit(f"FAIL: resourceOverwrites missing key `{key}`")
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
        sys.exit("FAIL: `uip` not on PATH")
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
        sys.exit(f"FAIL: `uip {' '.join(args)}` non-JSON output: {e}")


def check_tenant() -> None:
    seed = _load_seed()
    folder = _uip("or", "folders", "get", seed["folder_path"])
    folder_key = folder.get("Key") or folder.get("data", {}).get("Key")
    if not folder_key:
        sys.exit(f"FAIL: cannot resolve folder key for {seed['folder_path']!r}")

    connections = _uip(
        "is", "connections", "list", "uipath-microsoft-outlook365",
        "--folder-key", folder_key, "--refresh",
    )
    conn_list = connections.get("Data") if isinstance(connections.get("Data"), list) else []
    match = next((c for c in conn_list if c.get("Name") == seed["connection_name"]), None)
    if not match:
        sys.exit(
            f"FAIL: connection {seed['connection_name']!r} not found in "
            f"{seed['folder_path']!r}"
        )
    connection_id = match["Id"]

    # Poll the inbox for the seeded subject token. Outlook delivery
    # latency is typically a few seconds — give it up to 90s.
    deadline = time.monotonic() + 90
    last_titles: list[str] = []
    while time.monotonic() < deadline:
        result = _uip(
            "is", "resources", "run", "uipath-microsoft-outlook365",
            "list_messages_v2",
            "--connection-id", connection_id,
            "--folder-key", folder_key,
            "-d", json.dumps({
                "folder": "Inbox",
                "top": 100,
                "orderBy": "receivedDateTime desc",
                "filter": f"contains(subject, '{seed['subject']}')",
            }),
            timeout=60,
        )
        messages = (
            result.get("Data", {}).get("value")
            or result.get("value")
            or []
        )
        last_titles = [m.get("subject", "") for m in messages]
        if any(seed["subject"] in title for title in last_titles):
            print(f"OK: found {seed['subject']!r} in inbox top 25")
            print("PASS: tenant check complete")
            return
        time.sleep(5)
    sys.exit(
        f"FAIL: subject {seed['subject']!r} did not arrive in {seed['to_address']!r} "
        f"within 90s. Last 25 subjects: {last_titles[:5]}…"
    )


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("shape", "tenant"):
        sys.exit("usage: check_coded_is_outlook_send_mail.py {shape|tenant}")
    if sys.argv[1] == "shape":
        check_shape()
    else:
        check_tenant()


if __name__ == "__main__":
    main()
