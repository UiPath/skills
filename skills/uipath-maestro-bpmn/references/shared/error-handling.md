# Error Handling

Maestro supports BPMN error paths plus UiPath-specific retry and error-mapping
metadata. These features are executable behavior, so add them in pass 2 only
after the process shape and error intent are clear.

## BPMN error paths

- Declare reusable errors with `bpmn:error` and a stable `errorCode`.
- Attach `bpmn:boundaryEvent` with `bpmn:errorEventDefinition` to the activity
  whose failure should branch locally.
- Omit `errorRef` on an error event definition only for a deliberate catch-all
  handler.
- Use event subprocesses for scoped error handling that should catch errors not
  handled by a more local boundary event.
- Give each event subprocess exactly one start event.
- Boundary error event outgoing flows are exception flows. Do not also list
  those flows as normal outgoing flows on the attached activity.

## Retry metadata

Place retry metadata inside the activity extension elements:

```xml
<uipath:retry maxRetryCount="2" retryBackoff="PT30S" retryAllErrors="false">
  <uipath:errorDefinition errorRef="Error_ServiceUnavailable" />
</uipath:retry>
```

Supported retry attributes are:

- `maxRetryCount`
- `retryBackoff`
- `retryAllErrors`
- `retryBackoffType`
- `maxDuration`
- `exponentialBase`

Do not use stale aliases such as `maxAttempts` or `interval` in new XML.

## Error mapping metadata

Use error mapping when an activity needs to classify runtime failures for
retry, routing, or diagnostics:

```xml
<uipath:errorMapping version="v1">
  <uipath:error
    id="Mapped_ServiceUnavailable"
    errorRef="Error_ServiceUnavailable"
    priority="1"
    condition="=vars.error.code == &quot;SERVICE_UNAVAILABLE&quot;"
    detail="Service unavailable"
    retryable="true" />
</uipath:errorMapping>
```

Error mapping entries support:

- `id`
- `errorRef`
- `priority`
- `condition`
- `detail`
- `retryable`

Use `errorRef` to connect to a declared `bpmn:error`. Use `priority` when
multiple mappings may match. Conditions are lint-sensitive expressions and may
read the built-in runtime error through `vars.error`.

Do not use `code="..."` on `uipath:error` in new XML; model the code on
`bpmn:error errorCode="..."` and reference it through `errorRef`.

## Validation checklist

- Every `errorRef` resolves to a declared `bpmn:error`.
- Retry attributes use current names.
- Error mapping priorities are numeric.
- Error mapping `retryable` values are `true` or `false`.
- Conditions use `=vars.error...` and contain no assignments.
- Boundary handlers are attached to valid activities.
- Event subprocess handlers stay inside the scope whose errors they catch.
