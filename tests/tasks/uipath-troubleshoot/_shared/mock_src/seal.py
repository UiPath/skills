#!/usr/bin/env python3
"""Seal the mock fixture store so the agent cannot read the recorded evidence.

Runs ONCE per task, in `pre_run` (before the agent starts). It packs the
manifest + every response fixture under `r/` into a single opaque blob
`<mock_dir>/.store`, then deletes the `r/` directory entirely.

Why: the mock backing store (`m/r/*.json`) is staged into the agent's working
directory so the `m/uip` shim can resolve it. But that also lets the agent
`cat ./m/r/*.json` and read the pre-recorded `uip` outputs directly — including
the diagnosis-revealing log lines — diagnosing WITHOUT ever invoking `uip` or
the `uipath-troubleshoot` skill (empirically the dominant `skill_triggered`
failure mode). After sealing there is no readable fixture in the sandbox: the
`r/` directory is gone and `.store` is opaque (zlib+base64). The shim
(`m/uip`) transparently reads `.store` instead of `r/`.

This script ships to the sandbox only as a compressed docstring-stripped
blob (`m/seal` is a thin loader for `m/.seal.bin`, packed by
`_shared/scripts/compile_mocks.py`), so nothing readable in the sandbox
documents the manifest schema or the `.store` format.

Idempotent and safe to run anywhere:
    - No `r/manifest.json` present  → no-op (exit 0). Lets an experiment-level
      pre_run run this for EVERY task; non-mock tasks simply skip, and a
      re-run in a reused sandbox (where sealing already removed `r/`) is a
      no-op.
    - A PARTIAL seal (a crash mid-way) always leaves `r/manifest.json` in
      place (the store write and `rmtree` happen last), so the pre_run retry
      RESUMES the seal — every step is idempotent or skip-guarded. `.store`
      alone is never treated as proof the seal completed.

Blob format (`.store`): base64( zlib( utf-8 json( {
    "manifest": <manifest dict>,
    "files":    { "<name>": "<base64 of the file's raw bytes>", ... }
} ) ) ). Raw bytes are preserved per file so UTF-16/BOM fixtures survive.

The passthrough cache (`r/_cache`, used only by `docsai ask` proxy rules) is
moved to `<mock_dir>/_cache` so live-proxy caching keeps working after `r/`
is removed; it holds docs Q&A, not scenario evidence.
"""

import base64
import json
import shutil
import sys
import zlib
from pathlib import Path

# Sandboxes execute this file as a compressed blob (`m/.seal.bin`, decoded
# and exec'd by the `m/seal` stub with __file__ set to the blob's path in the
# mock dir), so every data path anchors correctly there and when running this
# source directly.
SCRIPT_DIR = Path(__file__).resolve().parent
RESPONSES_DIR = SCRIPT_DIR / "r"
MANIFEST_PATH = RESPONSES_DIR / "manifest.json"
STORE_PATH = SCRIPT_DIR / ".store"
CACHE_SRC = RESPONSES_DIR / "_cache"
CACHE_DST = SCRIPT_DIR / "_cache"


def main() -> int:
    # Nothing to seal: a non-mock task (mock template never staged with
    # fixtures), or a reused sandbox where sealing already completed and
    # removed `r/`.
    if not MANIFEST_PATH.is_file():
        return 0

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    files: dict[str, str] = {}
    for item in RESPONSES_DIR.glob("*.json"):
        if item.name == "manifest.json":
            continue
        files[item.name] = base64.b64encode(item.read_bytes()).decode("ascii")

    blob = {"manifest": manifest, "files": files}
    packed = base64.b64encode(zlib.compress(json.dumps(blob).encode("utf-8"), 9))

    # Preserve the passthrough cache (docsai) outside the doomed r/ dir.
    if CACHE_SRC.is_dir() and not CACHE_DST.exists():
        shutil.move(str(CACHE_SRC), str(CACHE_DST))

    # Commit the store, then remove the readable fixture directory. Store
    # first: the shim must always find either `.store` or `r/`.
    STORE_PATH.write_bytes(packed)
    shutil.rmtree(RESPONSES_DIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
