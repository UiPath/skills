"""The one `uip insights` runner the slot scripts share.

Kept out of the two entry points so clear_slot.py and seed_slot.py cannot
drift apart on how a command is run or how its envelope is parsed.
"""

import json
import shutil
import subprocess

# The key create_smoke.yaml hands the agent. It belongs to no Maestro
# process, so a dashboard saved under it is an orphan nobody's Monitoring
# tab reads. The other tasks use sibling all-zero keys ending in 1 to 4
# and a template-only source ending in "a"; the same reasoning covers them.
DEFAULT_PROCESS_KEY = "00000000-0000-0000-0000-000000000000"

# A key no task ever writes to, so its slot always serves the template.
# seed_slot.py copies from it, and copy_smoke.yaml reads it as the source.
TEMPLATE_SOURCE_KEY = "00000000-0000-0000-0000-00000000000a"


def uip_json(*args: str) -> dict | None:
    """Run one `uip insights` command and parse its JSON envelope, or None."""
    exe = shutil.which("uip")
    if exe is None:
        return None
    try:
        proc = subprocess.run(
            [exe, "insights", *args, "--output", "json"],
            capture_output=True,
            text=True,
            timeout=50,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None
