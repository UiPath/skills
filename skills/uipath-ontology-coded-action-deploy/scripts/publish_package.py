#!/usr/bin/env python3
"""Pack the staged tree and upload the .zip to the tenant solution feed. MUTATES a live tenant.

Prints the commands and changes nothing unless --execute is passed: a publish moves every job in
the Solution onto one version line, so the default is to show what would happen.

--wait is not optional. Publishing is ASYNCHRONOUS, and deploying before it completes fails with a
package-not-found error that never mentions publishing.

Not `uip solution projects publish --project-name`: that publishes an existing *cloud* solution
project and wants a Studio Web project name, so passing the solution's own name fails with
"Project with name '<name>' not found" (error 2003). The CLI cannot enumerate cloud project names
either -- `projects list` reads only the on-disk manifest -- so that route is a dead end. Packing
from source needs no cloud project at all.
"""

import argparse
import shutil
import sys
import tempfile

from _solution import solution_name, solution_src, version_info
from _staging import pack
from _uip import UIP, described, die, emit, uip_json

DESCRIBE = {
    "name": 'publish_package',
    "purpose": 'Pack and upload the package to the tenant feed',
    "phase": '3 - release',
    "inputs": {'env': ['SOLUTION_SRC', 'UIP_CLI (optional)'], 'args': ['version', '--execute']},
    "outputs": {'published': 'the package name', 'version': 'the version published'},
    "mutates": True,
    "exit_codes": {"0": "ok, result on stdout", "1": "refused or failed, reason on stderr"},
}


def main():
    if described(DESCRIBE):
        return
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("version")
    ap.add_argument("--force-version", action="store_true",
                    help="publish a version other than the computed next one")
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    name = solution_name()

    # The version is checked here rather than left to whoever typed it. Republishing a version
    # that already exists is the most expensive trap in this pipeline precisely because every
    # surface reports success: publish returns a package key, deploy reports Successful, and the
    # running code does not change. No output distinguishes it from a real release, so the only
    # place it can be caught is before it happens.
    live = version_info(name)
    if live and args.version != live["next"] and not args.force_version:
        die("refusing to publish %s: the next version for %r is %s (current is %s). Republishing "
            "an existing version is a silent no-op -- publish succeeds, deploy reports Successful, "
            "and the running code does not change. Pass --force-version if you mean it."
            % (args.version, name, live["next"], live["current"]),
            current=live["current"], next=live["next"], requested=args.version)

    if not args.execute:
        emit({"ok": True, "dryRun": True,
              "current": live["current"] if live else None,
              "next": live["next"] if live else None,
              "publishing": args.version,
              "firstRelease": live is None,
              "steps": [
                  [sys.argv[0].replace("publish_package.py", "stage_jobs.py")],
                  [UIP, "solution", "pack", "<staging>", "<outdir>", "-n", name, "-v", args.version],
                  [UIP, "solution", "publish", "<zip>", "--wait"]]})
        return

    outdir = tempfile.mkdtemp(prefix="ontology-pack-")
    zip_path, _ = pack(solution_src(), name, args.version, outdir)
    uip_json(["solution", "publish", zip_path, "--wait"])
    shutil.rmtree(outdir, ignore_errors=True)
    emit({"ok": True, "published": name, "version": args.version})


if __name__ == "__main__":
    main()

