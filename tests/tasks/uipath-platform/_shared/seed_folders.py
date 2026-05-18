#!/usr/bin/env python3
"""pre_run: create N folders under Shared/ with the per-run prefix.

Env vars:
    SEED_FOLDERS_COUNT  Number of folders to create (default 1, max 4).
    SEED_FOLDERS_PARENT Parent path (default "Shared").

Writes into seed.json:
    folders: [{key, path, name}, ...]
    folder_a_key, folder_a_path (for convenience — first folder)
    folder_b_key, folder_b_path (if count >= 2)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_common import load_or_init_seed, naming_prefix, save_seed, uip_json, log
from manifest import append as manifest_append


def main() -> int:
    count = int(os.environ.get("SEED_FOLDERS_COUNT", "1"))
    if not 1 <= count <= 4:
        log(f"FAIL: SEED_FOLDERS_COUNT={count} out of range 1..4")
        return 1
    parent = os.environ.get("SEED_FOLDERS_PARENT", "Shared")

    seed = load_or_init_seed()
    prefix = naming_prefix(seed)
    seed.setdefault("folders", [])

    suffixes = ["fa", "fb", "fc", "fd"]
    for i in range(count):
        suffix = suffixes[i]
        name = f"{prefix}-{suffix}"
        # Already created? (idempotent re-run protection)
        if any(f.get("name") == name for f in seed["folders"]):
            log(f"skip: folder {name} already in seed.json")
            continue

        envelope = uip_json(
            "or", "folders", "create", name,
            "--description", f"e2e test fixture for {seed['task_id']}",
            "--parent", parent,
        )
        data = envelope.get("Data") or {}
        key = data.get("Key")
        if not key:
            log(f"FAIL: folder create returned no Key: {envelope}")
            return 1
        path = data.get("FullyQualifiedName") or data.get("Path") or f"{parent}/{name}"
        record = {"name": name, "key": key, "path": path}
        seed["folders"].append(record)
        manifest_append("folder", key, path=path)
        log(f"OK created folder {name} key={key}")

    # Convenience aliases
    if seed["folders"]:
        seed["folder_a_key"] = seed["folders"][0]["key"]
        seed["folder_a_path"] = seed["folders"][0]["path"]
    if len(seed["folders"]) >= 2:
        seed["folder_b_key"] = seed["folders"][1]["key"]
        seed["folder_b_path"] = seed["folders"][1]["path"]

    save_seed(seed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
