#!/usr/bin/env python3
"""File attachment: bind a local file to a file-typed input via
``uip maestro flow debug --attachment <varId>=<path>`` and assert the runtime
uploaded it and the flow surfaced the file's name as output.

The attachment filename is generated here at check time with a random token the
agent never saw, so it can only reach a declared OUTPUT variable if the
attachment was actually uploaded, resolved to a Flow Attachment object, read via
``.FullName``, and mapped out — i.e. the full ``--attachment`` path works end to
end. An agent that hardcodes a filename literal cannot pass.

Node-shape agnostic on purpose. The feature under test is the ``--attachment``
binding and ``file``-variable hydration, not any particular node: the skill
documents reading a hydrated ``file`` variable BOTH in a Script node body and
directly in an End node's ``outputs.<varId>.source`` via ``=js:`` (see
``references/shared/node-output-wiring.md`` — End nodes). Both surface
``.FullName``, so pinning ``core.action.script`` rejected a correct two-node
``trigger -> End`` flow that the skill itself steers agents toward.

Scoping the match to the flow's ``out`` globals is what keeps the check honest,
and it is NOT interchangeable with :func:`assert_outputs_contain`. That helper
flattens every global — including the ``in`` file variable, whose runtime value
IS the attachment object carrying ``FullName``. Matching the basename against
that set is a tautology: it passes whenever a file uploads at all, even for a
flow that outputs a hardcoded literal or nothing. Verified against a live
tenant — a flow whose End node mapped ``fileName`` to the literal
``"sample-report.txt"`` still "passed", because the runtime globals were::

    {"start.output.inputDoc": {"ID": ..., "FullName": "evidence-<rand>.txt", ...},
     "fileName": "sample-report.txt"}

:func:`assert_named_output_contains` scopes to one declared output global — the
value a downstream consumer actually receives — so the input echo cannot satisfy
it. Do not "simplify" this back to a whole-payload match.
"""

import json
import os
import sys
import tempfile
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.flow_check import (  # noqa: E402
    assert_named_output_contains,
    find_project_dir,
    read_flow_file_input_vars,
    run_debug,
)


def read_flow_out_vars(project_dir: str) -> list[str]:
    """Return the ids of ``direction:"out"`` globals declared on the first
    ``.flow`` file in ``project_dir`` — the variables a caller receives.

    Local rather than shared: the mirror-image ``read_flow_file_input_vars``
    lives in ``_shared``, but only this task needs the out-side view, and
    keeping it here avoids widening the shared surface for one caller.
    """
    import glob

    flows = glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True)
    if not flows:
        sys.exit(f"FAIL: No .flow file found under {project_dir}")
    with open(flows[0]) as f:
        flow = json.load(f)
    variables = flow.get("variables") or flow.get("workflow", {}).get("variables") or {}
    return [v["id"] for v in (variables.get("globals") or []) if v.get("direction") == "out"]


def main():
    project_dir = find_project_dir()
    file_vars = read_flow_file_input_vars(project_dir)
    if not file_vars:
        sys.exit(
            "FAIL: No file-typed input variable (direction:'in', type:'file') "
            "found in the flow — nothing to bind an --attachment to."
        )
    out_vars = read_flow_out_vars(project_dir)
    if not out_vars:
        sys.exit(
            "FAIL: No output variable (direction:'out') found in the flow — "
            "nothing for the attachment's file name to surface through."
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
    # it through a declared `out` variable — scoped per-variable so the `in`
    # attachment object's own FullName cannot satisfy the match (see module docstring).
    if len(out_vars) == 1:
        assert_named_output_contains(payload, out_vars[0], basename)
    else:
        # Multiple declared outputs: the name must land in at least one of them.
        for name in out_vars:
            try:
                assert_named_output_contains(payload, name, basename)
                break
            except SystemExit:
                continue
        else:
            sys.exit(
                f"FAIL: attachment FullName {basename!r} did not appear in any "
                f"declared output variable {out_vars}."
            )
    print(
        f"OK: flow completed; output variable surfaced attachment FullName {basename!r}"
    )


if __name__ == "__main__":
    main()
