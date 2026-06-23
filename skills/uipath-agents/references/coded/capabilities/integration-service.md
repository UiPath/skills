# Integration Service (Coded)

Call IS connector activities (Slack, Jira, Web Search, …) from a coded Python agent via `sdk.connections.invoke_activity()`.

## When to Use

- Coded Python agent needs SaaS / API via IS (Slack, Salesforce, Jira, ServiceNow, Web Search, …).
- Connection exists or user creates one via `uip is connections create <CONNECTOR_KEY>`.

## When NOT to Use

- Calling an Orchestrator process / queue / asset → [process-invocation.md](process-invocation.md), `sdk.processes` / `sdk.queues` / `sdk.assets`.
- LLM-step-bound static IS tool inside Studio Web (no Python agent, just a tool resource) → [../../lowcode/capabilities/integration-service/integration-service.md](../../lowcode/capabilities/integration-service/integration-service.md).
- Vendor exposes a stable public REST API and you do NOT need IS auth/governance → call the vendor directly with `httpx`; IS adds no value.

## Discovery — Use the `uipath-platform` Skill First (Mandatory)

Integration Service discovery — connector → connection → ping → describe, reference-field resolution, parent-driven custom fields — is owned by the **`uipath-platform`** skill. Run its IS discovery workflow before authoring any `invoke_activity` create/update call; do not infer the shape from the worked examples below. If those reads fail, stop and surface — do not improvise.

Discovery is auth-gated (`uip login` + connection selection precede `describe`). **Coded consequence:** you can't author `body_fields` / `ActivityMetadata` without `describe` output, so for IS-using agents do auth + discovery *before* Build, not after.

Read these from the `uipath-platform` skill (`references/integration-service/`) — required even for tenant-free / shape-only authoring (you read them for the workflow, field-resolution, and error-recovery contract regardless of tenant; only the live `describe` step and `uip login` defer when no tenant is available).

**`agent-workflow.md` is ALWAYS mandatory. Reading it does not excuse skipping `reference-resolution.md`** when the target activity carries reference or required fields — that second read is the contract for curated create/update calls, and skipping it is the #1 cause of rejections:

- `agent-workflow.md` — **(always)** Steps 1–4: connector → connection → ping → describe.
- `reference-resolution.md` — **(mandatory before any create/update whose schema has reference or required fields — Jira `project`/`issuetype`/`versions`/`components`, Salesforce lookups, etc.)** reference-field resolution + **Validate Required Fields Before Executing**. Flat-body activities with no reference fields (e.g. Slack `send_message_to_channel_v2`) do not need it.

Then, as needed:

- `resources.md` § Parent-Field-Driven Custom Fields — Jira project/issuetype, Salesforce SOQL, Dataservice V3.
- `connectors.md` — connector disambiguation + option-label format.

Coded-specific layers:

1. **Reuse before discover** — grep cwd for existing `ActivityMetadata` constants before re-running describe.
2. **Present concrete options, then echo every pick.** At each stop point ask the user with the actual candidates as selectable options (one per candidate: short label + one-line description, per the option-label format in the `uipath-platform` skill's `connectors.md`). Recommend the safest default; let the user choose. Never ask open-ended — derive options from the discovery output. After the pick, echo the chosen option back before the next call. Ambiguous answer or "other" → follow up to narrow; do not infer.
   - **Stop points:** connector (multi-hit on `connectors list --filter`), curated-vs-raw object, ambiguous operation verb (`Update` vs `Replace`), parent-field `-f` values, custom-field-by-name with >1 candidate.
   - Silent inference produces wrong-connector / wrong-form / wrong-customfield writes.

## Coded vs Low-code IS Tools

| | Coded | Low-code |
|---|---|---|
| Artifact | Inline `ActivityMetadata` literal in Python | `resources/<Tool>/resource.json` |
| Selection | Author code or LLM tool-call routing | Studio Web binds tool to LLM step |
| Runtime | `sdk.connections.invoke_activity(...)` | Engine dispatches via `properties.toolPath` |
| Bindings | `bindings.json` `resource: "connection"` | Solution-level `connection/<KEY>/…json` (auto-generated) |

## `describe` Output → `ActivityMetadata` Mapping

```python
from uipath.platform.connections import ActivityMetadata, ActivityParameterLocationInfo
```

| `describe` field | → | `ActivityMetadata` | Notes |
|---|---|---|---|
| `operation.path` | → | `object_path` | direct |
| `operation.method` | → | `method_name` | direct |
| (not surfaced) | → | `content_type` | `"application/json"` for non-multipart |
| `parameters[type=query][].name` | → | `query_params` | direct |
| `parameters[type=path][].name` | → | `path_params` | direct |
| `parameters[type=header][]` | → | `header_params` | filtered out of compact summary; raw cache only — see Limitations |
| `parameters[type=multipart][]` | → | `multipart_params` | same filter — see Limitations |
| `requestFields[].name` first-segment, deduped | → | `body_fields` | see Body-Field Reframing |
| (not surfaced) | → | `json_body_section` | Multipart only — name of the form-part that holds the JSON body. `None` → SDK defaults to `"body"`. Override only when the connector expects a different wrapper (e.g., `"RagRequest"`). Ignored for non-multipart. |

### Body-Field Reframing (Non-Obvious)

`requestFields[].name` from describe is emitted as **dotted leaf paths** (`fields.project.key`, `attachment.image_url`) — a flat encoding of a nested schema, NOT routing keys.

`body_fields` is the **top-level envelope whitelist**: first segment of each `requestFields[].name`, deduped. Match is against `activity_input.items()` top-level keys only. Caller pre-nests the body and passes it as one input value; SDK slots it in as-is.

## Constructing `ActivityMetadata` — Worked Examples

**Slack `send_message_to_channel_v2`** — flat body schema; `body_fields` is the full deduped top-level set; single `query_params=["send_as"]`.

```python
SLACK_SEND_MESSAGE = ActivityMetadata(
    object_path="/send_message_to_channel_v2",
    method_name="POST",
    content_type="application/json",
    parameter_location_info=ActivityParameterLocationInfo(
        query_params=["send_as"],
        body_fields=[
            "channel", "messageToSend", "attachment", "buttons", "fields",
            "icon_emoji", "icon_url", "image", "link_names", "metadata",
            "mrkdwn", "parse", "reply_broadcast", "thread_ts",
            "unfurl_links", "unfurl_media", "username",
        ],
    ),
)
```

**Jira `curated_create_issue`** — every requestField starts with `fields.`; `body_fields` collapses to one entry. First run GenerateSchema discovery (auth-required) to surface the project- and issuetype-specific custom + reference fields — do this BEFORE writing the literal:

```bash
uip is resources describe "uipath-atlassian-jira" "curated_create_issue" \
  --connection-id "<CONNECTION_ID>" --operation Create \
  -f fields.project.key=ENGCE -f fields.issuetype.id=3 \
  --action GenerateSchema --output json
```

Resolve any reference fields it reports (`versions`, `components`, assignee, …) per the `uipath-platform` skill's `reference-resolution.md` — passing a name where the connector wants a reference ID is the most common curated-activity rejection.

```python
JIRA_CREATE_ISSUE = ActivityMetadata(
    object_path="/curated_create_issue",
    method_name="POST",
    content_type="application/json",
    parameter_location_info=ActivityParameterLocationInfo(body_fields=["fields"]),
)
```

**Pass the body NESTED, not as dotted keys.** `body_fields=["fields"]` + a pre-nested `{"fields": {...}}` is the shape `curated_create_issue` accepts. Passing flat dotted keys (`body_fields=["fields.project.key", ...]` + `activity_input={"fields.project.key": "ENGCE"}`) is rejected by the connector with `project: Specify a valid project ID or key` — the SDK ships dotted keys as literal top-level JSON keys, which the curated activity does not unflatten.

```python
sdk.connections.invoke_activity(
    activity_metadata=JIRA_CREATE_ISSUE,
    connection_id=connection.id,
    activity_input={
        "fields": {
            "project": {"key": "ENGCE"},
            "issuetype": {"id": "3"},
            "summary": "Triage: agent failure",
            "description": "Auto-filed by coded agent.",
        }
    },
)
```

## Runtime Invocation Pattern

```python
from uipath.platform import UiPath
from uipath.platform.connections import ActivityMetadata, ActivityParameterLocationInfo

# SLACK_SEND_MESSAGE literal: see "Worked Examples" above.

def post_to_slack(channel: str, message: str) -> dict:
    sdk = UiPath()
    # Binding key, NOT a UUID. Locally this 400s unless resourceOverwrites
    # is set — see § Local runtime binding. Do NOT add a try/except or a
    # state health-check around it; gate any deployed-only probe on env.
    connection = sdk.connections.retrieve("slack-triage")
    return sdk.connections.invoke_activity(
        activity_metadata=SLACK_SEND_MESSAGE,
        connection_id=connection.id,
        activity_input={"channel": channel, "messageToSend": message},
    )
```

- **`activity_input` is the single bucket** for query, path, header, multipart, and body values. SDK routes by `parameter_location_info`. No `query=`/`path=`/`header=` kwarg exists.
- **`invoke_activity` calls `retrieve()` internally** (`_connections_service.py:675`), so `connection_id` can be a UUID or a binding-key string — the `@resource_override` decorator on `retrieve` resolves it. The pattern above (explicit retrieve, then pass `connection.id`) is preferred because it gives the agent a typed `Connection` for `metadata()` / `retrieve_token()`; one-shots can use `invoke_activity(connection_id="slack-triage", ...)` directly.
- **Return value** is `response.json()` — keys mirror `responseFields[].name`. Flat connectors return top-level; some wrap in `Data` / `result`. Auto-traced via `@traced`; see [tracing.md](tracing.md).
- **Silent drops** — `None` values and any key not in `parameter_location_info` are skipped (`_connections_service.py:753-770`). Mistyped keys never surface as errors; echo-check writes per Error Handling § "Silent rename / typo".

### Multipart endpoints (silent in describe)

Compact `describe` omits `contentType`. Curated file-attachment activities (Outlook `send-mail-v2`, Slack `send_files_to_channel`, …) are multipart/form-data — `content_type="application/json"` returns `400 "Unable to parse multipart body"`. Read the raw cache (path under Limitations) and set `content_type="multipart/form-data"` with `multipart_params` + `json_body_section`:

```python
ActivityMetadata(
    object_path="/send-mail-v2", method_name="POST",
    content_type="multipart/form-data",
    parameter_location_info=ActivityParameterLocationInfo(
        multipart_params=["body", "file"], query_params=["saveAsDraft"]),
    json_body_section="body",
)
```

Each `multipart_params` value (`_connections_service.py:800-815`) is a 3-tuple `(filename, bytes, content_type)` for file uploads (preferred), raw `bytes` (filename defaults to the field name, `application/octet-stream`), or a scalar string (plain form field, e.g. `saveAsDraft="true"`). The JSON body section (default `"body"`) auto-injects as `(filename="", json.dumps(body), "application/json")`.

### Async variant

Suffix `_async` and `await` the call. Identical semantics, same args. Use inside `async def` framework nodes.

### Other `sdk.connections` methods

| Method | Use when | Cite |
|---|---|---|
| `list(name=, folder_path=, connector_key=, skip=, top=)` | Connection key unknown — enumerate or filter. Sync + `list_async`. Returns `List[Connection]`. | `_connections_service.py:152` |
| `retrieve_token(key, token_type=ConnectionTokenType.DIRECT)` | Need the raw bearer to call the vendor's own REST API directly (e.g., Microsoft Graph) — bypasses `invoke_activity`. Sync + `retrieve_token_async`. Returns `ConnectionToken{access_token,...}`. | `_connections_service.py:368` |
| `retrieve_event_payload(event_args: EventArguments)` | Agent invoked by an IS trigger / webhook — input carries `EventArguments`; unwrap the inbound payload before processing. Sync + `retrieve_event_payload_async`. | `_connections_service.py:421` |
| `metadata(element_instance_id, connector_key, tool_path, parameters=, schema_mode=True, max_jit_depth=5)` | Compact `describe` dropped headers / multipart / JIT-cascaded custom fields. Pass `parameters={...}` to auto-walk JIT URLs up to depth 5. Sync + `metadata_async`. | `_connections_service.py:79` |

**`retrieve_token` escape hatch** is the supported way to fall back to the vendor's own API when an IS curated activity is missing (canonical example: `uipath-langchain-python/samples/email-triage-agent/graph.py` calls Microsoft Graph with the connection's bearer). Distinct from the anti-pattern of hitting `/elements_/v3/…` directly.

## Framework Integration

Wrap `invoke_activity_async` in the framework's tool primitive — runtime body identical, only decorator/registration differs.

| Framework | Primitive | Reference |
|---|---|---|
| LangGraph | Writes (LLM judgment) = node via conditional edge; reads = LLM-callable tool. `invoke_activity_async` inside `async def node(state)`. | [../frameworks/langgraph-integration.md](../frameworks/langgraph-integration.md) |
| LlamaIndex | `FunctionTool.from_defaults(fn=<RUNTIME_FN>)` | [../frameworks/llamaindex-integration.md](../frameworks/llamaindex-integration.md) |
| OpenAI Agents | `@function_tool` on `<RUNTIME_FN>` | [../frameworks/openai-agents-integration.md](../frameworks/openai-agents-integration.md) |

## Connection Resolution — `bindings.json`

Invocation URL is `/elements_/v3/element/instances/<UUID>/…`, so the SDK ultimately needs a UUID. To let admins rebind per environment, write code against a binding key string; `@resource_override("connection", resource_identifier="key")` (`_connections_service.py:51`) on `retrieve` maps it to the deployed UUID. `uip codedagent init` writes `resources: []` — author the connection entry after picking the connection.

Minimal connection entry (`uip codedagent init` writes `resources: []`; add this). The entry-type field is **`resource`** (NOT `type`) — the CLI bindings schema is `{ resource, key, value, metadata }`:

```jsonc
{
  "version": "2.0",
  "resources": [
    {
      "resource": "connection",
      "key": "jira-coded-eval",
      "value": { "ConnectionId": { "defaultValue": "jira-coded-eval" } },
      "metadata": { "UseConnectionService": "True", "Connector": "", "BindingsVersion": "2.2" }
    }
  ]
}
```

Full JSON schema lives in [`../lifecycle/bindings-reference.md`](../lifecycle/bindings-reference.md) § Connection. Coded-agent-specific points only:

- Entry type field is `resource` (`"resource": "connection"`), never `type` — matches every other binding entry.
- `key` is just `<CONNECTION_KEY>` (no `<NAME>.<FOLDER>` dot suffix used by other resources). Same string passed positionally to `retrieve()`.
- `value.ConnectionId.defaultValue` is the binding key string, NOT a UUID. Capital-C `ConnectionId` (other resources use `name`); no `folderPath`.
- `metadata.UseConnectionService: "True"` is mandatory; `Connector: ""` (empty); `BindingsVersion: "2.2"` is the per-resource rev and is independent of the top-level envelope `version: "2.0"`.
- `uip codedagent deploy` repackages as `content/bindings_v2.json` — never hand-author that path.

### Required artifact — `__uipath/uipath.json` (local-run binding)

Every coded IS agent MUST write `__uipath/uipath.json`. It is the file `uipath run` reads for connection overwrites: `cli_run.py` → `read_resource_overwrites_from_file(ctx.runtime_dir)`, `runtime_dir` defaults to `__uipath` (`runtime/context.py`), config name `uipath.json` (`UIPATH_CONFIG_FILE`). Without it, local `retrieve("<KEY>")` 400s with `CNS1026 The value '<KEY>' is not valid` — `bindings.json` is deploy-time only (packed into `content/bindings_v2.json`) and ignored by local run. This is distinct from `./uipath.json` (pack/deploy config). Write both:

```jsonc
{
  "functions": { "main": "main.py:main" },
  "runtime": {
    "internalArguments": {
      "resourceOverwrites": {
        "connection.slack-triage": {
          "connectionId": "<Id from `uip is connections list`>",
          "folderKey":    "<FolderKey from `uip is connections list`>"
        }
      }
    }
  }
}
```

`ConnectionResourceOverwrite` (`uipath/platform/common/_bindings.py:100`, **NOT** `uipath/_utils/_bindings.py`) requires exactly two fields — `connectionId` (alias accepts `ConnectionId`) and `folderKey` — and has `extra="ignore"`, so `elementInstanceId` and any other extras are silently dropped (see anti-pattern #1). Key format is `connection.<BINDING_KEY>` matching the `bindings.json` `key`. After override, `Connection.element_instance_id` (for `sdk.connections.metadata()` calls) comes from the live IS API response — never write it locally.

**Required outputs — every coded IS agent ships all four:**

| File | Read by | Must contain |
|---|---|---|
| `main.py` | runtime | lazy `UiPath()` (not module-scope), inline `ActivityMetadata` literal, `retrieve(<KEY>)` + `invoke_activity` |
| `bindings.json` | `uip codedagent deploy` | connection resource, `key`, `ConnectionId.defaultValue`=binding key, `UseConnectionService: "True"` |
| `uipath.json` | `uip` pack/deploy | `functions`, `packOptions` |
| `__uipath/uipath.json` | `uipath run` (local) | `runtime.internalArguments.resourceOverwrites["connection.<KEY>"]` = `connectionId` + `folderKey` |

Omitting `__uipath/uipath.json` means the agent cannot run locally — incomplete, not optional. Personal-workspace connections also need `UIPATH_FOLDER_KEY=<KEY>` (`FolderKey` from `uip is connections list`) in the environment at local run.

## Error Handling

SDK does NO preflight schema validation — it routes the keys it recognises (per `parameter_location_info`), drops `None` and unknown keys, ships the request. All field-shape validation happens server-side. Four outcomes:

| Outcome | When | Surfaces as | Recover |
|---|---|---|---|
| **Misconfigured `ActivityMetadata`** | `content_type` not `*/json` or `*/multipart*` | `ValueError("Unsupported content type: <ct>")` (`_connections_service.py:826`) | Fix the literal; do not retry. |
| **IS schema reject** | Caller omits a `requestFields[].required: true`, sends wrong dataType | `RuntimeError` with IS-validator body (NOT a pre-HTTP `ValueError`) | Re-run describe; add the field / fix the shape. |
| **Vendor reject** | Shape OK by IS, vendor's own validators reject (workflow rules, custom validators, auth) | `RuntimeError` with vendor body | Parse vendor message; per `agent-workflow.md § Error Recovery` retry once with the fix. |
| **Silent rename / typo** | Curated rename (Jira `customfield_10004` → `storyPoints_Customfield10004`) or mistyped key — dropped by `_connections_service.py:753-770` | **No exception. 2xx with field missing.** | Echo-check: re-read created resource; assert the field you sent is present and equal. Mismatch → switch curated⇄raw or fix the key. |

Network / 5xx are retried with exponential backoff by `BaseService.request`; only exhausted retries propagate (as `httpx.HTTPError` subclasses, not `RuntimeError`). For LLM-facing tools return error strings rather than re-raising — keeps the agent loop alive. Cap semantic retries at 2 per `agent-workflow.md § Error Recovery`; never retry the same query unchanged.

## Anti-patterns — silent failures only

These six are the ones the SDK / IS / vendor will NOT tell you about. Positive guidance for everything else lives in the relevant section above; do not pad this list.

1. **Adding `elementInstanceId` to `resourceOverwrites`.** `ConnectionResourceOverwrite` (`_bindings.py:100`) defines only `connectionId` + `folderKey` with `extra="ignore"` — extras are silently dropped. The `element_instance_id` you need for `sdk.connections.metadata()` comes from the live `Connection.element_instance_id` after `retrieve()`, never from local config.
2. **Hand-authoring `object_path` / `method_name` / `body_fields`.** Curated activities rename fields silently between connector versions. Always source from `uip is resources describe` and re-run after upgrades. Sidecar-JSON literals also drift — keep `ActivityMetadata` literals inline in a `.py` file; `pack` bundles them and mypy / pyright catch shape errors at edit time.
3. **Typos and unknown keys in `activity_input`.** Anything not in `parameter_location_info` is silently dropped (`_connections_service.py:753-770`); the request goes out missing the field, vendor returns 2xx, the data is just gone. Echo-check writes by reading back the created object (see Error Handling § "Silent rename / typo").
4. **`invoke_activity` for trigger payloads.** IS-triggered jobs receive `EventArguments` as input — unwrap with `sdk.connections.retrieve_event_payload(event_args)` (`_connections_service.py:421`). Calling `invoke_activity` to "receive" anything is a category error.
5. **Bypassing `invoke_activity` with raw `httpx` to `/elements_/v3/…`.** Loses retry, tracing, S2S auth. Distinct from the supported escape hatch of calling the **vendor's own** API with `retrieve_token` (see Other `sdk.connections` methods) — that is a different URL space.
6. **Instantiating `UiPath()` at module level.** `uip codedagent init` and `pack` import the module to introspect entry points; module-level construction fires HTTP at import time and breaks scaffold / deploy. Always lazy: build inside the function that needs it.

## Limitations of the compact describe

`uip is resources describe --output json` filters `parameters` to `path|query` only — multipart and header params survive only in the raw cache at:

```text
~/.uipath/cache/integrationservice/<TENANT_ID>/<CONNECTOR_KEY>/<CONNECTION_ID>/<OBJECT>.schema.json
```

Example: `uipath-salesforce-slack` (NOT `uipath-slack` — that key does not exist on the catalog; the SDK docstring example is misleading) / `send_files_to_channel` lists `parameters[type=multipart][0].name = "file"` only in the cache. Workaround — hand-populate from `data.metadata.method.<VERB>.parameters[]`: `type=="multipart"` → `multipart_params`, `type=="header"` → `header_params`. When the cache is empty, runtime fallback:

```python
md = sdk.connections.metadata(
    element_instance_id=connection.element_instance_id,
    connector_key="uipath-salesforce-slack",
    tool_path="/send_files_to_channel",
)
```

Pass `parameters={"<KEY>": "<VALUE>"}` only for connectors with cascading JIT custom fields.

**`-f` precondition.** `uip is resources describe ... -f <KEY>=<VALUE>` fails with `No api-type ObjectAction matched for fields [...]` on connectors without a matching api-type ObjectAction, and requires `--connection-id` + `--operation`. Enumerate valid actions on the cached schema before retrying — the path is `.data.metadata.method.<VERB>.design.actions[]` (NOT `.connectorMethodInfo.design.actions[]`, which does not exist in the cache shape):

```bash
jq '.data.metadata.method.<VERB>.design.actions[] | select(.actionType=="api") | .name' <CACHED_DESCRIBE>
```

Replace `<VERB>` with the operation's HTTP method (e.g. `POST` for Create). Full discovery flow lives in `uipath-platform` `resources.md`.

## Reference

- [sdk-services.md](sdk-services.md) § Connections — service surface.
- [../frameworks/langgraph-integration.md](../frameworks/langgraph-integration.md), [llamaindex-integration.md](../frameworks/llamaindex-integration.md), [openai-agents-integration.md](../frameworks/openai-agents-integration.md) — framework wiring.
- [../lifecycle/bindings-reference.md](../lifecycle/bindings-reference.md) § Connection — full `bindings.json` schema.
- `uipath-platform` skill, `references/integration-service/` — `agent-workflow.md` + `resources.md` for the discovery workflow + parent-driven custom fields.
- [../../lowcode/capabilities/integration-service/integration-service.md](../../lowcode/capabilities/integration-service/integration-service.md) — low-code IS tool (different artifact).
