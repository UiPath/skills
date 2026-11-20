#!/usr/bin/env python3
"""Pass when the robot-less folder holds no enabled time trigger.

With no runtime to run it, an enabled schedule only fires into a folder
that cannot start the job. The agent may create the trigger disabled, or
not create it at all; both pass."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

seed = json.loads(Path("seed.json").read_text())
folder = seed.get("noruntime_folder_path") or sys.exit("FAIL: seed.json missing noruntime_folder_path")

r = subprocess.run(["uip", "or", "triggers", "list", "--type", "time", "--folder-path", folder,
                    "--limit", "200", "--output", "json"], capture_output=True, text=True, timeout=60)
try:
    env = json.loads(r.stdout)
except json.JSONDecodeError:
    sys.exit(f"FAIL: triggers list returned non-JSON: {r.stdout[:200]} {r.stderr[:200]}")
if env.get("Result") != "Success":
    sys.exit(f"FAIL: triggers list failed: {env.get('Message')}")

enabled = [t.get("Name") for t in env.get("Data") or [] if t.get("Enabled")]
if enabled:
    sys.exit(f"FAIL: enabled time trigger(s) in a folder with no runtime: {enabled}")
print(f"PASS: no enabled time trigger in {folder}")
