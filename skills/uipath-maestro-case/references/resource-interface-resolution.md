# Resource Interface Resolution

One resolver gates every Case consumer that invokes a resource. It is deliberately independent of task type: the owning plugin declares how to acquire a contract, which recovery actions it supports, and which placeholder to emit. The resolver only acquires, normalizes, compares, records, and routes the result.

In scope:

- all nine task types;
- connector event triggers;
- `wait-for-connector` rules in all four condition scopes.

Manual/timer triggers and ordinary non-connector condition rules do not invoke a resource and stay outside this resolver. `wait-for-timer` participates explicitly through the `none` provider.

## Plugin declaration

Every consumer plugin owns a declaration in its `planning.md`:

```yaml
interface-provider: <provider or origin-to-provider map>
placeholder-profile: task | event-trigger | connector-rule | none
recovery-capabilities: select-alternate | create | correct-fresh | adapt | defer
provider-config:
  <provider-specific identity, extraction, and native-type normalization>
```

The provider/config declaration is authoritative. The resolver MUST NOT branch on `taskType`, plugin folder, or consumer kind. To add a future type, change only that type's plugin declaration and implementation recipe.

## Canonical provider contract

All providers return the same normalized object:

```text
acquire(context) -> {
  provider,
  origin,
  resourceRef,
  schemaSource,
  inputs:  [{name, type, required}],
  outputs: [{name, type}]
}
```

Rules common to every provider:

1. Preserve field names exactly, including case.
2. Normalize native types through the map declared by the owning plugin. Do not guess an unknown native type; leave it deferred and record the native value in `schemaSource`/the decision log.
3. Preserve the resource identity and version/revision in `resourceRef`. Contract reuse depends on it.
4. On a mechanical read/CLI failure, retry acquisition once. A second failure is `unavailable`; it is not an empty compatible contract.
5. A readable, intentionally empty contract is valid. An unreadable expected non-empty contract is blocking.

### Reusable providers

| Provider | Acquisition behavior |
|---|---|
| `tasks-describe` | Run the plugin-declared `uip maestro case tasks describe` command and normalize its input/output schema. Used by tenant Process, Agent, RPA, Action, API Workflow, and child Case resources. |
| `local-entry-points` | Read the plugin-declared on-disk contract paths. Used by local/fresh Agent and API Workflow siblings. A future inline RPA plugin may declare its own paths without changing this document. |
| `case-spec-activity` | Read `inputs.bodyFields[]`, `inputs.pathParameters[]`, `inputs.queryParameters[]`, multipart parameters, and `outputs.responseFields[]` from the activity spec using the extraction paths declared by the connector-activity plugin. |
| `case-spec-trigger` | Read `inputs.eventParameters[]` and `outputs.responseFields[]` from the trigger spec using the extraction paths declared by the event/task/rule plugin. |
| `none` | Return `origin: "none"` with empty inputs/outputs; no CLI/file read. The resolver records `status: "not-applicable"`. |

`case-spec-*` validates only canonical invocation I/O here. Connection selection, operation/object selection, reference IDs, filters, mandatory event parameters, `caseShape`, registration keys, and context placeholder substitution remain in the connector plugins.

## Requested contract

Build one requested contract per consumer from the SDD declaration:

- Inputs: every supplied input binding, whether literal, Case variable, metadata expression, or upstream task output.
- Outputs: only `->` extracts consumed from the resource/event payload.
- Exclude `=` computed outputs. The Case computes those values; the resource does not emit them.
- Carry the exact field name, direction, and requested type. A type is deferred only when the SDD has no authoritative type source (for example, a name-only literal or unresolved upstream output).

Shared resources still get one result per consumer. Two tasks may invoke the same resource with different requested/effective bindings.

## Canonical comparison

Comparison is exact for names/direction and directional for types.

### Names and direction

- Names are exact and case-sensitive. Do not convention-match, singularize, prefix, or case-fold.
- A requested input must exist as an actual input; a requested output must exist as an actual output.
- A same-named field in the opposite direction is a reversed-direction blocking mismatch.

### Directional type assignability

For an input, test `Case value type -> resource input type`. For an output, test `resource output type -> Case variable type`.

Permitted safe widening after plugin normalization:

```text
integer -> float -> double
date -> datetime
```

Exact types are assignable. A deferred requested type accepts a readable actual type and records the decision. A deferred/unknown **actual** type cannot satisfy a known requested type because assignability cannot be proven; classify it blocking. Every other scalar change is blocking: never silently narrow, coerce to `string`, parse strings, or synthesize conversion expressions.

For `jsonSchema`, compare the top-level container (`object` vs `array`) and any declared item container only. Do not validate business payload properties or semantics. For `file`, require the JobAttachment shape (`ID`, `FullName`, `MimeType`, `Metadata`, or the equivalent canonical `$ref`); ordinary JSON objects are not files.

### Classification

| Finding | Classification |
|---|---|
| All requested fields exist with correct direction and assignable types | `compatible` |
| Optional actual input not requested | compatible extra |
| Actual output not consumed | compatible extra |
| Actual required input not requested | `adaptable` — user must supply/map it or choose another recovery |
| Missing requested input/output | blocking |
| Reversed direction | blocking |
| Incompatible/narrowing type | blocking |
| Expected contract unreadable after one retry | blocking/unavailable |

Compatible extras update the snapshot without a prompt. `adaptable` is not resolved until the user explicitly approves an effective mapping. A blocking mismatch can never remain resolved through best-effort continuation.

## Resolution and recovery

The resolver intersects the plugin's declared capabilities with the candidate origin. It presents only actions that are both declared and valid:

| Origin | Valid recovery |
|---|---|
| Fresh resource built in the current Create flow | Correct fresh resource, adapt Case, or defer |
| Existing local sibling | Adapt Case, create a uniquely named replacement when supported, or defer |
| Tenant resource | Adapt Case, fetch/select another candidate on demand, create a replacement when supported, or defer |
| No-contract (`none`) | Mark `not-applicable`; continue without a prompt |

Invariants:

- Never modify an existing tenant or local resource.
- Never automatically mutate on a semantic mismatch.
- Fetch alternate tenant contracts on demand; do not prefetch every search match.
- Phase 0 may resolve/select/adapt/defer, but never creates a resource.
- In Phase 0, an approved adaptation updates `sdd.draft.md` and becomes the requested contract at Approve.
- In Phase 1, an approved adaptation is recorded only as `effectiveContract`; never silently edit an existing `sdd.md`.
- Fresh correction requires an explicit user choice and follows [`plugins/tasks/create-inline-common.md`](plugins/tasks/create-inline-common.md). Allow at most two correction attempts, reacquiring after each. Registration happens only after a compatible/adapted result.
- If resolution ends in `deferred` or `unavailable`, discard incompatible best-effort bindings and route to the declared placeholder.

## Persistence: `tasks/interface-resolved.json`

`registry-resolved.json` remains the resource identity/search audit. Interface compatibility and approved I/O live in a separate sidecar adjacent to `tasks.md`:

```json
[
  {
    "owner": {
      "kind": "task|event-trigger|condition-rule",
      "stage": null,
      "scope": null,
      "parent": null,
      "name": "Exact SDD declaration name"
    },
    "plugin": "agent",
    "provider": "tasks-describe",
    "origin": "tenant|local|fresh|none",
    "resourceRef": {},
    "schemaSource": "...",
    "requestedContract": {
      "inputs": [{"name": "prompt", "type": "string", "required": true}],
      "outputs": [{"name": "result", "type": "string"}]
    },
    "effectiveContract": {
      "inputs": [{"name": "prompt", "type": "string", "required": true}],
      "outputs": [{"name": "result", "type": "string"}]
    },
    "actualContract": {
      "inputs": [{"name": "prompt", "type": "string", "required": true}],
      "outputs": [{"name": "result", "type": "string"}]
    },
    "status": "compatible|adapted|deferred|unavailable|not-applicable",
    "decisions": []
  }
]
```

Owner rules:

- Task: `kind: task`, exact stage/name, other fields `null`.
- Event trigger: `kind: event-trigger`, exact trigger name, stage/scope/parent `null`.
- Connector condition rule: `kind: condition-rule`; exact scope and declaration name; `stage` and `parent` carry the exact named stage/task when applicable rather than a parsed composite key.
- Never collapse owner identity into strings such as `"Stage.Task"`.

`requestedContract` is the SDD contract. `effectiveContract` equals it unless the user explicitly approves an adaptation. `actualContract` is the normalized provider result. `decisions[]` records each approval, alternate selection, correction, compatible-extra refresh, or deferral with its reason.

### Cache reuse

Phase 1 may reuse a Phase 0 result only when all of these match exactly:

1. owner object;
2. plugin and provider;
3. resource identity and version/revision;
4. requested contract;
5. status is `compatible`, `adapted`, or `not-applicable`.

Otherwise reacquire and replace only that owner's record. A legacy run with no sidecar is valid, but MUST resolve interfaces once before reuse/materialization.

## Phase protocol

### Phase 0 / Phase 1

For each consumer:

1. Identify candidate and read its plugin declaration.
2. Build `requestedContract`.
3. Acquire/normalize the actual contract (one retry on mechanical failure).
4. Compare and classify.
5. Apply explicit recovery until compatible/adapted/not-applicable or deferred/unavailable.
6. Persist one owner record.
7. Mark the consumer resolved only for `compatible`, `adapted`, or `not-applicable`.

Fresh resources are created only in Phase 1. Build first, resolve/correct while unregistered, then register exactly once after the gate passes.

### Phase 2 / Phase 3 materialization

Before materializing a resolved consumer, reacquire or reuse a current matching result and verify there is no blocking drift. Phase 3's full `case spec --input-details`, `tasks describe`, or local contract read refreshes `actualContract` before final bindings are written.

If the provider result is unchanged, reuse prior approvals and do not repeat questions. Compatible extras refresh the sidecar. Blocking drift reopens resolution; if it does not end compatible/adapted, emit the placeholder instead of a partially enriched consumer.

### Consumer Interface Integrity (end of Phase 3)

This replaces the task-only resolved-resource Check 5. Iterate over `interface-resolved.json` and the final consumer shapes:

1. Require status `compatible`, `adapted`, or `not-applicable`.
2. Verify every actual required input/event parameter in the approved effective contract has a final value.
3. Verify every consumed output/payload extraction exists.
4. Recheck exact direction and directional assignability.
5. Detect drift using the current Phase 2 `tasks describe`, Phase 3 `case spec`, or reread local contract.
6. Repair Case bindings only through an explicit adaptation. Otherwise replace the consumer with its placeholder and update status/decisions.

Do not repeat a question when owner, resourceRef, requested/effective/actual contracts, and status are unchanged.

## Placeholder routing

| Profile | Blocking/unavailable result |
|---|---|
| `task` | Keep structural task fields and write `data: {}`. |
| `event-trigger` | Keep render/entry-point structure and write only `data.uipath.serviceType: "Intsvc.EventTrigger"`. |
| `connector-rule` | Write the validated stub `uipath` from `connector-trigger-common.md`. |
| `none` | No placeholder; `not-applicable` continues. |

Placeholder output contains no incompatible binding, partial `caseShape`, or best-effort field. Existing specialized connector checks still run when the interface is compatible/adapted.
