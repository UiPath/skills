#!/usr/bin/env python3
"""Build the staging tree: each mapped job written in as its project's main.ts, with a derived manifest.

Writes only to a temp directory, so this is the cheapest proof that a job change reaches the tree
and that its contract can be lowered at all. The source tree is never touched.
"""

import argparse

from _solution import solution_src
from _staging import stage
from _uip import described, emit

DESCRIBE = {
    "name": 'stage_jobs',
    "purpose": "Stage each job as its project's main.ts and derive its manifest",
    "phase": '2 - stage',
    "inputs": {'env': ['SOLUTION_SRC', 'ENTRY_POINTS_TOOL (optional)'], 'args': []},
    "outputs": {'staging': 'temp directory path', 'staged': 'one entry per project'},
    "mutates": False,
    "exit_codes": {"0": "ok, result on stdout", "1": "refused or failed, reason on stderr"},
}


def main():
    if described(DESCRIBE):
        return
    # Takes no arguments; the parser is here for -h and to reject a stray one.
    argparse.ArgumentParser(description=__doc__).parse_args()
    staging, report = stage(solution_src())
    report.update({"ok": True, "staging": str(staging)})
    emit(report)


if __name__ == "__main__":
    main()

