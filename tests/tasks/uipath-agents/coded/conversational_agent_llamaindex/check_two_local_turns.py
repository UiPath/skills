#!/usr/bin/env python3
"""Assert the LlamaIndex chat agent ran locally for two distinct turns.

Outcome-based replacement for a `command_executed` count of
`uip codedagent run`: see `_shared/two_turn_outputs.py`.

Exits 0 on PASS, with a `FAIL: ...` message otherwise.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.project_root import find_project_root  # noqa: E402
from _shared.two_turn_outputs import assert_two_local_turns  # noqa: E402

ROOT = find_project_root("chat-agent")

if not ROOT.is_dir():
    sys.exit(f"FAIL: project directory {ROOT} does not exist")

assert_two_local_turns(ROOT)
