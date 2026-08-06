#!/usr/bin/env python3
"""Record a real `uip` response into a scenario's passthrough cache.

Operator-only re-recording path. The sandbox dispatcher (`mock_src/uip.py`)
never invokes the real CLI: a `passthrough: true` rule replays a recorded
cache entry, and a query with no valid entry falls through to the manifest's
`unmocked_default`. To give a scenario a real recorded response for a
passthrough query, run this script from the repo checkout - it is never
staged into a sandbox, so nothing the agent types can reach it:

    python tests/tasks/uipath-troubleshoot/_shared/scripts/record_passthrough.py \\
        tests/tasks/uipath-troubleshoot/products/orchestrator/<scenario> \\
        -- docsai ask "How do I configure X?"

Requires the real `uip` CLI on PATH with valid auth. The response is written
to `<scenario>/data/m/r/_cache/<md5(args)[:16]>.json`, signed with the
dispatcher's cache HMAC so the sandbox shim accepts it (`m/seal` moves
`r/_cache` beside the shim at seal time). Commit the file with the scenario.
"""

import importlib.util
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parent.parent
UIP_SRC = SHARED_DIR / "mock_src" / "uip.py"

USAGE = "usage: record_passthrough.py <scenario-dir> -- <uip args...>"


def _load_dispatcher_module():
    """Import mock_src/uip.py for its cache key + signature helpers (SSOT)."""
    spec = importlib.util.spec_from_file_location("mock_uip", UIP_SRC)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv: list[str]) -> int:
    if "--" not in argv:
        print(USAGE, file=sys.stderr)
        return 2
    split = argv.index("--")
    head, cli_args = argv[:split], argv[split + 1 :]
    if len(head) != 1 or not cli_args:
        print(USAGE, file=sys.stderr)
        return 2

    responses_dir = Path(head[0]) / "data" / "m" / "r"
    if not (responses_dir / "manifest.json").is_file():
        print(f"record_passthrough: no manifest at {responses_dir / 'manifest.json'}", file=sys.stderr)
        return 2

    real_uip = shutil.which("uip")
    if real_uip is None:
        print("record_passthrough: real `uip` CLI not found on PATH", file=sys.stderr)
        return 2

    proc = subprocess.run(
        [real_uip] + cli_args,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.stderr:
        sys.stderr.write(proc.stderr)

    dispatcher = _load_dispatcher_module()
    args_str = " ".join(cli_args)
    entry = {
        "args": args_str,
        "stdout": proc.stdout,
        "exit_code": proc.returncode,
        "cached_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    entry["sig"] = dispatcher._cache_sig(entry)

    out = responses_dir / "_cache" / f"{dispatcher._cache_key(args_str)}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
    print(f"recorded (exit {proc.returncode}) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
