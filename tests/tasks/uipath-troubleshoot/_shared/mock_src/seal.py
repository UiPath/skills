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
`r/` directory is gone and `.store` is opaque. The shim (`m/uip`)
transparently reads `.store` instead of `r/`.

This script ships to the sandbox only as an encrypted docstring-stripped
blob (`m/seal` is a thin loader for `m/.seal.bin`, packed by
`_shared/scripts/compile_mocks.py`), so nothing readable in the sandbox
documents the manifest schema or the `.store` format.

Idempotent and safe to run anywhere:
    - No `r/manifest.json` present  → no-op (exit 0). Lets an experiment-level
      pre_run run this for EVERY task; non-mock tasks simply skip, and a
      re-run in a reused sandbox (where sealing already removed `r/`) is a
      no-op.
    - A PARTIAL seal (a crash mid-way) always leaves `r/manifest.json` in
      place, so the pre_run retry RESUMES the seal — every step is idempotent
      or skip-guarded. `.store` alone is never treated as proof the seal
      completed.

      The deletion order is what makes that true, and a whole-tree delete is
      not: it is not atomic, and `manifest.json` is not the last name it
      reaches (`README.md` — the scenario write-up that NAMES the root cause —
      sorts after it). One undeletable child, and a file lock from an indexer
      or a scanner is enough, would then leave `README.md` readable with no
      manifest beside it: the retry hits the no-op guard above, exits 0 without
      sealing, and the answer is in the agent's working directory while the run
      reports success. So every OTHER child goes first, and only once all of
      them are gone is `manifest.json` unlinked and the directory removed. Any
      failure before that point leaves the manifest, and the retry resumes.
    - A retry re-seals from what SURVIVES in `r/`, which after a partial
      deletion is a subset — so a naive rewrite would replace a complete
      `.store` with a degraded one and the run would grade against fixtures
      that are no longer served. The store is therefore written only when the
      copy on disk does not already cover the current manifest and every
      surviving fixture byte-for-byte; otherwise the existing, more complete
      `.store` is kept and the retry only finishes the deletion. Refusing to
      proceed instead would strand the retry with readable fixtures on every
      attempt; keeping the better copy always terminates.

Blob format (`.store`): this utf-8 JSON document, compressed and then
encrypted under `DATA_KEY` (`mock_src/_cipher.py`, purpose `store`):

    { "manifest": <manifest dict>,
      "files":    { "<name>": "<base64 of the file's raw bytes>", ... } }

Raw bytes are preserved per file so UTF-16/BOM fixtures survive. That base64
lives inside the encrypted payload, never on disk, so nothing readable in the
sandbox describes how `.store` is encoded.
"""

import base64
import json
import shutil
import sys
from pathlib import Path

# The packed blob carries `_cipher.py` inlined ahead of this module, so this
# name is already bound there and NO import is attempted. Only a direct run of
# this source (where `_cipher.py` is the sibling on `sys.path[0]`) imports. The
# condition is load-bearing: an unconditional import would resolve against
# whatever `_cipher.py` sits in the loader's own directory in a sandbox, which
# is writable, and a planted module can read `DATA_KEY` out of its importer's
# globals.
if "data_open" not in globals():
    from _cipher import data_open, data_seal

# Sandboxes execute this file as an encrypted blob (`m/.seal.bin`, decrypted
# and exec'd by the `m/seal` stub with __file__ set to the blob's path in the
# mock dir), so every data path anchors correctly there and when running this
# source directly.
SCRIPT_DIR = Path(__file__).resolve().parent
RESPONSES_DIR = SCRIPT_DIR / "r"
MANIFEST_PATH = RESPONSES_DIR / "manifest.json"
STORE_PATH = SCRIPT_DIR / ".store"


def _store_already_covers(manifest: dict, files: dict[str, str]) -> bool:
    """True when `.store` already holds this manifest and at least these fixtures.

    A resumed seal sees only the fixtures the previous attempt had not deleted
    yet, so rewriting unconditionally would downgrade a complete store. Anything
    unreadable, wrong-shaped, from another manifest, or disagreeing on a
    surviving fixture's bytes answers False: the readable `r/` is authoritative
    then, and rewriting from it is correct.
    """
    if not STORE_PATH.is_file():
        return False
    try:
        blob = json.loads(data_open(STORE_PATH.read_bytes(), "store").decode("utf-8"))
    except (OSError, ValueError):
        return False
    if not isinstance(blob, dict) or blob.get("manifest") != manifest:
        return False
    have = blob.get("files")
    if not isinstance(have, dict):
        return False
    return all(have.get(name) == b64 for name, b64 in files.items())


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

    # Commit the store, then remove the readable fixture directory. Store
    # first: the shim must always find either `.store` or `r/`.
    if not _store_already_covers(manifest, files):
        blob = {"manifest": manifest, "files": files}
        STORE_PATH.write_bytes(data_seal(json.dumps(blob).encode("utf-8"), "store"))

    # Every other child first; `manifest.json` only once they are all gone, so
    # any failure here leaves the manifest and the pre_run retry resumes.
    for item in sorted(RESPONSES_DIR.iterdir()):
        if item.name == "manifest.json":
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
    MANIFEST_PATH.unlink()
    # The seal is complete by here — store written, nothing readable left — so a
    # directory that will not go is cosmetic, and raising would fail a pre_run
    # whose work is done.
    try:
        RESPONSES_DIR.rmdir()
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
