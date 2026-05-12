# Manage - Instance lifecycle

Use this journey to intervene in a running or faulted BPMN process instance.
Lifecycle actions are cloud-side mutations and require explicit user consent for the specific action.

## Supported decisions

- Pause.
- Resume.
- Cancel.
- Retry after diagnosis.
- Migrate version.
- Move cursor/goto when the runtime supports it and the user explicitly requests it.

## Pre-flight

1. Confirm login:

   ```bash
   uip login status --output json
   ```

2. Resolve the target instance ID and folder key from debug output, process run output, job status, or instance listing.
3. Confirm the target instance and folder/context with the user before acting.
4. Explain the expected side effects of the lifecycle action.
5. For retry, migrate, or cursor movement, diagnose the fault and correlate the deployed asset first.

## Commands

```bash
uip maestro bpmn instance list --output json
uip maestro bpmn instance get <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance pause <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance resume <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance cancel <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance retry <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance migrate <INSTANCE_ID> <NEW_VERSION> -f <FOLDER_KEY> --output json
uip maestro bpmn instance goto <INSTANCE_ID> '[{"sourceElementId":"A","targetElementId":"B"}]' -f <FOLDER_KEY> --output json
```

Use `goto` only when the user provides or approves explicit source and target BPMN element IDs.
Prefer a JSON file or carefully quoted JSON for non-trivial transition sets.

## Decision notes

| Action | Use when |
| --- | --- |
| `pause` | The instance is running and the user needs to halt progress while preserving state. |
| `resume` | The instance is paused and the user wants normal execution to continue. |
| `cancel` | The instance should stop and not continue from current state. |
| `retry` | Root cause is understood and retrying the same deployed definition is expected to succeed. |
| `migrate` | The user explicitly chooses a different package version for an existing instance. |
| `goto` | The user explicitly chooses cursor movement between known BPMN element IDs. |

After every lifecycle command, fetch the instance again and report the resulting status:

```bash
uip maestro bpmn instance get <INSTANCE_ID> -f <FOLDER_KEY> --output json
```

## Handoff

If the action reveals a modeling or binding problem, return to Author with the BPMN element ID, incident summary,
and generated file mismatch if relevant.

## Anti-patterns

- **Never retry before diagnosis.** Fetch incidents, runtime variables, and the deployed BPMN asset first.
- **Never migrate or move a cursor as a generic fix.** These actions change runtime state and need an explicit user decision.
- **Never omit `--folder-key` or `-f` on instance commands.**
- **Never paste private runtime variables, tenant URLs, folder keys, connection IDs, or payloads into public notes.**
