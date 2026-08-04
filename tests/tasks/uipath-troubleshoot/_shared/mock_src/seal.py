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

Once the seal is committed this machinery has no further use, so it removes
itself: `m/seal` is truncated to zero bytes and `m/.seal.bin` is deleted (see
`_self_destruct`). `m/uip` needs `.uip.bin` and `.store`, never `.seal.bin`,
so dispatch is unaffected for the rest of the run.

Idempotent and safe to run anywhere:
    - No `r/manifest.json` present  → no-op (exit 0), and specifically NOT a
      self-destruct: this path cannot tell "already sealed" from "never had
      fixtures", so it touches nothing. Lets an experiment-level pre_run run
      this for EVERY task; non-mock tasks simply skip, and a re-run in a
      reused sandbox (where sealing already removed `r/`) is a no-op.
    - A PARTIAL seal (a crash mid-way) always leaves `r/manifest.json` in
      place (the store write and `rmtree` happen last), so the pre_run retry
      RESUMES the seal — every step is idempotent or skip-guarded. `.store`
      alone is never treated as proof the seal completed.
    - After a COMPLETED seal, a re-run is an empty program: `m/seal` is zero
      bytes, which is valid Python and exits 0 without doing anything.

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
if "data_seal" not in globals():
    from _cipher import data_seal

# Sandboxes execute this file as an encrypted blob (`m/.seal.bin`, decrypted
# and exec'd by the `m/seal` stub with __file__ set to the blob's path in the
# mock dir), so every data path anchors correctly there and when running this
# source directly.
SCRIPT_DIR = Path(__file__).resolve().parent
RESPONSES_DIR = SCRIPT_DIR / "r"
MANIFEST_PATH = RESPONSES_DIR / "manifest.json"
STORE_PATH = SCRIPT_DIR / ".store"
# This script's own staged artifacts, removed once the seal is committed.
SEAL_STUB = SCRIPT_DIR / "seal"
SEAL_BLOB = SCRIPT_DIR / ".seal.bin"


def _self_destruct() -> None:
    """Remove this script's own machinery from the mock directory.

    Call ONLY after the store is written and `r/` is gone. Ordering is the
    whole risk here: a blank file is valid Python and exits 0, so a `seal`
    blanked before the store is committed would make the pre_run retry report
    success over a sandbox whose `r/` fixtures are still readable — the exact
    leak this script exists to prevent, turned silent. Hence last, and hence
    never on the no-manifest path.

    Truncate the stub BEFORE unlinking the blob, not the other way round. With
    the blob gone first, a crash before the truncate leaves a `seal` whose
    loader exits non-zero on "runtime data missing", failing the `fail_on_error`
    pre_run of a task that was in fact sealed correctly. Blanking first means
    every later crash point still leaves a `seal` that exits 0.

    Best-effort: a failure here leaves readable *machinery*, never readable
    fixtures, so it must not fail the pre_run of a completed seal. `OSError`
    covers the file already being absent (a re-run, or a sandbox that got part
    way through this function) as well as a refused write.

    Opening the stub `r+b` rather than writing it is deliberate: a plain write
    would CREATE the file when it is absent, which for a direct run of this
    source in `mock_src/` (no `seal` stub beside it, only `seal.py`) would drop
    a stray file into the repo.
    """
    try:
        with SEAL_STUB.open("r+b") as stub:
            stub.truncate(0)
    except OSError:
        pass
    try:
        SEAL_BLOB.unlink()
    except OSError:
        pass


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
    packed = data_seal(json.dumps(blob).encode("utf-8"), "store")

    # Commit the store, then remove the readable fixture directory. Store
    # first: the shim must always find either `.store` or `r/`.
    STORE_PATH.write_bytes(packed)
    shutil.rmtree(RESPONSES_DIR)
    # Strictly last: until `r/` is gone, a retry has to be able to re-run this.
    _self_destruct()
    return 0


if __name__ == "__main__":
    sys.exit(main())
