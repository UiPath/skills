#!/usr/bin/env python3
"""Query tenant to verify the 3-folder hierarchy + post-move parent."""

import json
import subprocess
import sys
from pathlib import Path


def _pick(d, *names):
    if not isinstance(d, dict):
        return None
    for n in names:
        for k in (n, n[:1].lower() + n[1:], n.lower()):
            if k in d:
                return d[k]
    return None


def uip_json(*args: str) -> dict:
    r = subprocess.run(["uip", *args, "--output", "json"], capture_output=True, text=True, timeout=60)
    if not r.stdout.strip():
        sys.exit(f"FAIL: uip {' '.join(args)} no stdout")
    return json.loads(r.stdout)


def fetch_folder(name_or_path: str) -> dict:
    env = uip_json("or", "folders", "get", name_or_path)
    if env.get("Result") != "Success":
        sys.exit(f"FAIL: folders get {name_or_path!r} Result={env.get('Result')!r} Message={env.get('Message')!r}")
    return env.get("Data") or {}


seed = json.loads(Path("seed.json").read_text())
uuid8 = seed.get("uuid8")
if not uuid8:
    sys.exit("FAIL: seed.json has no uuid8")

parent = seed.get("parent_folder_path") or "Shared"
top_name = f"e2e-fh-{uuid8}-top"
a_name = f"e2e-fh-{uuid8}-A"
b_name = f"e2e-fh-{uuid8}-B"

top = fetch_folder(f"{parent}/{top_name}")
a = fetch_folder(f"{parent}/{top_name}/{a_name}")
b = fetch_folder(f"{parent}/{top_name}/{b_name}")

top_id = _pick(top, "ID", "Id")
a_id = _pick(a, "ID", "Id")
a_parent = _pick(a, "ParentID", "ParentId")
b_parent = _pick(b, "ParentID", "ParentId")

if a_parent != top_id:
    sys.exit(f"FAIL: A.ParentID={a_parent!r} expected top.ID={top_id!r}")
if b_parent != top_id:
    sys.exit(f"FAIL: B.ParentID={b_parent!r} expected top.ID={top_id!r} (the move must have happened — B should be sibling of A)")

print(f"OK: hierarchy verified — top({top_id}) parents both A({a_id}) and B (after move)")
