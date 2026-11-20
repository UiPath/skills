"""Print the project's ``.bpmn`` path for a shell command (``uip maestro bpmn validate "$(...)"``).

Resolves ``<name>.bpmn`` or Studio Web's ``Process.bpmn`` in a project directory named
``<name>``, wherever the agent put the project; fails unless exactly one project matches.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import fail, resolve_bpmn_file  # noqa: E402

if len(sys.argv) != 2:
    fail("usage: print_bpmn_path.py <name>.bpmn")
print(resolve_bpmn_file(sys.argv[1]).relative_to(os.getcwd()))
