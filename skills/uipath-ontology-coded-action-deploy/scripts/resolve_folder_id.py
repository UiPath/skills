#!/usr/bin/env python3
"""Resolve a folder path to the numeric Id that ont:processFolderId wants.

Reads OrganizationUnitId off a process in the folder, because that is the only place the CLI
exposes the numeric id -- the folder commands return keys and names, not ids.

Needs no SOLUTION_SRC: it asks the tenant about a folder, not the source tree about a solution.
"""

import argparse

from _solution import folder_id
from _uip import described, emit

DESCRIBE = {
    "name": 'resolve_folder_id',
    "purpose": 'Resolve a folder path to its numeric OrganizationUnitId',
    "phase": '4 - resolve',
    "inputs": {'env': ['UIP_CLI (optional)'], 'args': ['path']},
    "outputs": {'folderId': 'the numeric id', 'folderPath': 'the path asked for'},
    "mutates": False,
    "exit_codes": {"0": "ok, result on stdout", "1": "refused or failed, reason on stderr"},
}


def main():
    if described(DESCRIBE):
        return
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="fully qualified folder name, e.g. Shared/support-jobs")
    args = ap.parse_args()
    emit(folder_id(args.path))


if __name__ == "__main__":
    main()

