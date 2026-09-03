#!/usr/bin/env python3
"""Pack the staged tree into a deployable .zip. No tenant writes.

-n is mandatory: without it the package is named after the staging directory, and the deployment
would not recognise it.
"""

import argparse
import os
import tempfile

from _solution import solution_name, solution_src
from _staging import pack
from _uip import described, emit

DESCRIBE = {
    "name": 'build_package',
    "purpose": 'Pack the staged tree into a deployable .zip',
    "phase": '3 - release',
    "inputs": {'env': ['SOLUTION_SRC', 'UIP_CLI (optional)'], 'args': ['version', 'outdir (optional)']},
    "outputs": {'zip': 'path to the package', 'bytes': 'its size', 'staged': 'one entry per project'},
    "mutates": False,
    "exit_codes": {"0": "ok, result on stdout", "1": "refused or failed, reason on stderr"},
}


def main():
    if described(DESCRIBE):
        return
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("version")
    ap.add_argument("outdir", nargs="?", help="defaults to a temp directory")
    args = ap.parse_args()
    outdir = args.outdir or tempfile.mkdtemp(prefix="ontology-pack-")
    zip_path, report = pack(solution_src(), solution_name(), args.version, outdir)
    emit({"ok": True, "zip": zip_path, "bytes": os.path.getsize(zip_path),
          "staged": report["staged"]})


if __name__ == "__main__":
    main()

