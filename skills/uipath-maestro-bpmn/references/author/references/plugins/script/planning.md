# Script Planning

Use this reference when planning BPMN script tasks.

## When to use

- Deterministic in-process data transformation.
- Small validation or routing helper logic.
- Preparing request bodies for downstream tasks.
- Normalizing outputs before gateways or end events.

## Planning steps

1. Confirm the logic belongs inside BPMN instead of an RPA job, API workflow, agent, or connector.
2. Define input variables, output variables, and error behavior.
3. Keep scripts small, deterministic, and public-safe.
4. Plan `args` input shape and output mappings.
5. Add boundary error handling when script failure should be recoverable.
6. Avoid secrets, tenant data, network calls, and private examples.

## Model may draft

- `bpmn:scriptTask` with JavaScript script CDATA.
- `uipath:scriptVersion`.
- Input and output mappings using declared variables. See [impl.md](impl.md#minimal-jint-script-task-shell) for the exact required shape.
- Diagram geometry and surrounding error paths.

## Stop conditions

Stop when the script needs secrets, network access, long-running work, external packages, or customer-specific logic that should be implemented outside BPMN.
