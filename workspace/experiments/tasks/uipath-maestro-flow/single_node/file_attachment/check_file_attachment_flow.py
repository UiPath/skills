#!/usr/bin/env python3
"""File attachment: bind a local file to a file-typed input via
``uip maestro flow debug --attachment <varId>=<path>`` and assert the runtime
uploaded it and the flow surfaced the file's name as output.

The attachment filename is generated here at check time with a random token the
agent never saw, so the only way it can appear in the flow output is if the
attachment was actually uploaded, resolved to a Flow Attachment object, read by
the Script node, and mapped to an output variable — i.e. the full
``--attachment`` path works end to end. An agent that hardcodes a filename
literal cannot pass.
"""

import os
import sys
import tempfile
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_outputs_contain,
    find_project_dir,
    read_flow_file_input_vars,
    run_debug,
)


def main():
    # A Script node must read the attachment — prevents echoing a hardcoded literal.
    assert_flow_has_node_type(["core.action.script"])

    project_dir = find_project_dir()
    file_vars = read_flow_file_input_vars(project_dir)
    if not file_vars:
        sys.exit(
            "FAIL: No file-typed input variable (direction:'in', type:'file') "
            "found in the flow — nothing to bind an --attachment to."
        )

    # Unique basename the agent could not have hardcoded.
    token = uuid.uuid4().hex[:12]
    basename = f"evidence-{token}.txt"
    path = os.path.join(tempfile.mkdtemp(), basename)
    with open(path, "w") as f:
        f.write(f"attachment payload {token}\n")

    var_id = file_vars[0]
    print(f"Binding --attachment {var_id}={path}")
    payload = run_debug(attachments={var_id: path}, timeout=240)

    # The runtime resolves a file attachment to {ID, FullName, MimeType, Metadata};
    # FullName is the uploaded file's basename. A passing flow reads it and surfaces
    # it as an output variable.
    assert_outputs_contain(payload, basename)
    print(f"OK: Script node present; flow completed; output surfaced attachment FullName {basename!r}")


if __name__ == "__main__":
    main()
