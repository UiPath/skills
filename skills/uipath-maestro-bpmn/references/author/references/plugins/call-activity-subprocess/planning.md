# Call Activity and Subprocess Planning

Use this reference when planning reusable or scoped process blocks.

## When to use

- Expanded subprocesses for local scoped work.
- Event subprocesses for scoped exception handling.
- Call activities for reusable processes or external workflows.
- Isolating variables, retries, and boundaries.

## Planning steps

1. Decide whether the work is local subprocess content or a call to another reusable process.
2. Define subprocess start/end behavior, variables, and mappings.
3. Confirm whether nested content must render in Studio Web and needs its own diagram.
4. Plan boundary events on the activity or subprocess.
5. Keep sequence flows inside scope; use mappings for data crossing boundaries.
6. Record unresolved called-resource bindings as placeholders.

## Model may draft

- `bpmn:subProcess`, event subprocess, and `bpmn:callActivity` structure.
- Scoped variables, input/output mappings, loop metadata, and diagram geometry.
- Boundary events and error paths.

## Stop conditions

Stop when a called process/resource is unknown, subprocess scope would be crossed by sequence flows, or input/output contracts are unclear.
