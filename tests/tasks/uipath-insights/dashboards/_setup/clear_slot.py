#!/usr/bin/env python3
"""Free a placeholder process's dashboard slot before a task runs.

A create is one shot per slot. Once a run has saved a dashboard there, the
next run reads `Saved: true`, the prompt's own rule tells the agent to stop,
and the create criterion can never fire again: the task passes once and
fails forever, and an A/B of two variants fails whichever runs second. So
the slot is cleared in a `pre_run` step, which is the rule in the team's
Command Optimization note, section 5. The copy task clears its destination
for the same reason: copy refuses an occupied slot.

Usage: clear_slot.py [process-key]. The default is the create task's key.
Each task that writes owns one placeholder key, so tasks running side by
side in the same eval never clear or seed each other's slot.

The delete verb ships on the cli dashboard stack after the create does, so
an installed CLI that lacks it is not an error here: the task still runs,
and the agent's own read tells it what the slot holds. Nothing in this
script raises, and it always exits zero, because a failed clearing must
never fail the task.
"""

import sys

from _slot import DEFAULT_PROCESS_KEY, uip_json


def main(process_key: str) -> None:
    read = uip_json("dashboards", "get", "--process-key", process_key)
    if read is None or read.get("Result") != "Success":
        print(f"clear_slot: slot {process_key} could not be read, leaving it alone")
        return
    data = read.get("Data") or {}
    if not data.get("Saved"):
        print(f"clear_slot: slot {process_key} already serves the template")
        return
    dashboard_id = str(data.get("Id"))
    gone = uip_json("dashboards", "delete", dashboard_id, "--yes")
    state = ((gone or {}).get("Data") or {}).get("DeleteState")
    print(f"clear_slot: delete of dashboard {dashboard_id} -> {state or 'unavailable'}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROCESS_KEY)
    sys.exit(0)
