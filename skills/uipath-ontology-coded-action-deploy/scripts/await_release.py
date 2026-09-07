#!/usr/bin/env python3
"""Poll a release in a folder until it is ready, stale, or missing.

A deployment reports success before Orchestrator has finished provisioning, and invoking against a
release that is not ready yet is what produced three consecutive JsCodedFunction.ValidationFailed
faults. Waiting is cheaper than diagnosing that.

Needs no SOLUTION_SRC: it asks the tenant about a release, not the source tree about a solution.
"""

import argparse
import time

from _solution import release_records, release_version
from _uip import described, die, emit

# Ten minutes at ten-second intervals. Provisioning after a deploy has been observed to take
# minutes, and the failure this avoids costs far more to diagnose than the wait.
AWAIT_POLLS = 60
AWAIT_INTERVAL = 10

DESCRIBE = {
    "name": 'await_release',
    "purpose": 'Poll a release until ready, stale, or missing',
    "phase": '4 - resolve',
    "inputs": {'env': ['UIP_CLI (optional)'], 'args': ['process', 'version', '--folder-path']},
    "outputs": {'state': 'ready | stale | missing', 'version': 'the version seen'},
    "mutates": False,
    "exit_codes": {"0": "ok, result on stdout", "1": "refused or failed, reason on stderr"},
}


def await_release(process, want, folder_path):
    """Poll rather than assume. A stale Release is indistinguishable from a fresh one at the API
    surface, and invoking against one is what produced three consecutive
    JsCodedFunction.ValidationFailed faults: the contract had moved on, the deployed job had not.

    Three outcomes: ready (exit 0), stale (keep polling until the timeout), missing (fail at once,
    listing what the folder does contain).
    """
    got = None
    for attempt in range(AWAIT_POLLS):
        records = release_records(folder_path)
        hit = next((r for r in records if r.get("Name") == process), None)
        if hit is None:
            die("release %r not found in folder %s" % (process, folder_path),
                state="missing", available=[r.get("Name") for r in records])
        got = release_version(hit)
        if got == want:
            return {"ok": True, "state": "ready", "process": process, "version": got}
        if attempt + 1 < AWAIT_POLLS:
            time.sleep(AWAIT_INTERVAL)
    die("timed out waiting for %s to reach %s" % (process, want),
        state="stale", process=process, version=got, wanted=want)


def main():
    if described(DESCRIBE):
        return
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("process")
    ap.add_argument("version")
    ap.add_argument("--folder-path", required=True,
                    help="fully qualified folder name, e.g. Shared/support-jobs-1-0-3")
    args = ap.parse_args()
    emit(await_release(args.process, args.version, args.folder_path))


if __name__ == "__main__":
    main()

