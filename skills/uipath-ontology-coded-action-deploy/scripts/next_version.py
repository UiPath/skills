#!/usr/bin/env python3
"""Report the package's current version and the next one to publish.

Every job in one ontology's Solution ships in one package, so a publish moves them all onto the
same version line. The current value is read from the live deployment rather than tracked locally,
because the deployment is the only thing that knows what is actually out there.
"""

import argparse

from _solution import solution_name, version_info
from _uip import described, emit

DESCRIBE = {
    "name": 'next_version',
    "purpose": "Report the package's current and next version",
    "phase": '3 - release',
    "inputs": {'env': ['SOLUTION_SRC or SOLUTION_NAME', 'UIP_CLI (optional)'], 'args': []},
    "outputs": {'current': 'the live version, or null', 'next': 'the version to publish'},
    "mutates": False,
    "exit_codes": {"0": "ok, result on stdout", "1": "refused or failed, reason on stderr"},
}


def main():
    if described(DESCRIBE):
        return
    ap = argparse.ArgumentParser(description=__doc__)
    args = ap.parse_args()
    emit(version_info(solution_name()))


if __name__ == "__main__":
    main()

