#!/usr/bin/env python3
"""Delete the feedback record created during the e2e run."""

import json
import subprocess
import sys
from pathlib import Path

create_path = Path("feedback_create.json")
if not create_path.is_file():
    print("SKIP: feedback_create.json not found — nothing to clean up")
    sys.exit(0)

try:
    data = json.loads(create_path.read_text())
except json.JSONDecodeError:
    print("SKIP: feedback_create.json is not valid JSON")
    sys.exit(0)

d = data.get("Data") or {}
feedback_id = d.get("Id") or d.get("id")
folder_key = d.get("FolderKey") or d.get("folderKey")

if not feedback_id:
    print("SKIP: no Data.Id in feedback_create.json")
    sys.exit(0)

cmd = ["uip", "traces", "feedback", "delete", feedback_id, "--output", "json"]
if folder_key:
    cmd += ["--folder-key", folder_key]

result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode == 0:
    print(f"OK: deleted feedback {feedback_id}")
else:
    print(
        f"WARN: delete returned exit {result.returncode}: {result.stdout.strip() or result.stderr.strip()}"
    )
