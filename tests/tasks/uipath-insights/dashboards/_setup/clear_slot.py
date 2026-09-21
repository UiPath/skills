#!/usr/bin/env python3
"""Free the placeholder process's dashboard slot before a create task runs.

A create is one shot per slot. Once a run has saved a dashboard there, the
next run reads `Saved: true`, the prompt's own rule tells the agent to stop,
and the create criterion can never fire again: the task passes once and
fails forever, and an A/B of two variants fails whichever runs second. So
the slot is cleared in a `pre_run` step, which is the rule in the team's
Command Optimization note, section 5.

The delete verb ships on the cli dashboard stack after the create does, so
an installed CLI that lacks it is not an error here: the task still runs,
and the agent's own read tells it what the slot holds. Nothing in this
script raises, and it always exits zero, because a failed clearing must
never fail the task.
"""

import json
import shutil
import subprocess
import sys

# The same key create_smoke.yaml hands the agent. It belongs to no Maestro
# process, so a dashboard saved under it is an orphan nobody's Monitoring
# tab reads.
PROCESS_KEY = "00000000-0000-0000-0000-000000000000"


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


def main() -> None:
    read = uip_json("dashboards", "get", "--process-key", PROCESS_KEY)
    if read is None or read.get("Result") != "Success":
        print("clear_slot: the slot could not be read, leaving it alone")
        return
    data = read.get("Data") or {}
    if not data.get("Saved"):
        print("clear_slot: the slot already serves the template")
        return
    dashboard_id = str(data.get("Id"))
    gone = uip_json("dashboards", "delete", dashboard_id, "--yes")
    state = ((gone or {}).get("Data") or {}).get("DeleteState")
    print(f"clear_slot: delete of dashboard {dashboard_id} -> {state or 'unavailable'}")


if __name__ == "__main__":
    main()
    sys.exit(0)
