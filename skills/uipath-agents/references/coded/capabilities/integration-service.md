# Integration Service (Coded)

Call Integration Service (IS) connector activities—Slack, Jira, Salesforce, ServiceNow, Web Search, and others—from a coded Python agent with `sdk.connections.invoke_activity()`.

## When to Use

Use this skill when a coded Python agent needs a SaaS/API through IS and a connection exists or the user will create one with `uip is connections create <CONNECTOR_KEY>`.

## When NOT to Use

- Orchestrator processes, queues, or assets → [process-invocation.md](process-invocation.md), `sdk.processes` / `sdk.queues` / `sdk.assets`.
- An LLM-step-bound static IS tool in Studio Web with no Python agent → [../../lowcode/capabilities/integration-service/integration-service.md](../../lowcode/capabilities/integration-service/integration-service.md).
- A vendor’s stable public REST API when IS auth/governance is unnecessary → call the vendor directly with `httpx`.

## Mandatory Discovery

Run the `uipath-platform` skill’s IS discovery workflow before authoring any `invoke_activity` create/update call. Do not infer activity shape from examples. If discovery reads fail, stop and surface the failure; do not improvise.

Authenticate with `uip login` and select a connection before auth-gated `describe`. Authenticate and discover before Build: `body_fields` and `ActivityMetadata` require `describe` output.

Read these files from the `uipath-platform` skill (`references/integration-service/`) even for tenant-free or shape-only authoring:

- Read `agent-workflow.md` **always**; run Steps 1–4: connector → connection → ping → describe.
- Read `reference-resolution.md` before any create/update whose schema has reference or required fields—Jira `project`/`issuetype`/`versions`/`components`, Salesforce lookups, and similar. It defines reference-field resolution and **Validate Required Fields Before Executing**. Flat-body activities with no reference fields, such as Slack `send_message_to_channel_v2`, do not require it.
- Read `resources.md` § Parent-Field-Driven Custom Fields when applicable: Jira project/issuetype, Salesforce SOQL, Dataservice V3.
- Read `connectors.md` for connector disambiguation and option-label format.

Reading `agent-workflow.md` does not replace `reference-resolution.md` when the target has reference or required fields.

Coded-specific rules:

1. **Reuse before discover:** grep the cwd for existing `ActivityMetadata` constants before rerunning `describe`.
2. **Present concrete options, then echo every pick:** at every stop point, ask the user using actual discovery candidates, one candidate per option with a short label and one-line description, following `connectors.md`. Recommend the safest default and let the user choose. Echo the chosen option before continuing. Never ask open-ended questions or infer an ambiguous answer; “other” requires narrowing.
3. Stop points are: connector when `connectors list --filter` returns multiple hits; curated versus raw object; ambiguous operation verb such as `Update` versus `Replace`; parent-field `-f` values; and custom-field-by-name when more than one candidate exists.
4. Do not silently infer selections: wrong connector or wrong form can create incorrect writes.

## Coded vs Low-code IS Tools

| | Coded | Low-code |
|---|---|---|
| Artifact | Inline `ActivityMetadata` literal in Python | `resources/<Tool>/resource.json` |
| Selection | Author code or LLM tool-call routing | Studio Web binds tool to an LLM step |
| Runtime | `sdk.connections.invoke_activity(...)` | Engine dispatches through `properties.toolPath` |
| Bindings | `bindings.json`, `resource: "connection"` | Solution-level `connection/<KEY>/…json` (auto-generated) |

## Build `ActivityMetadata` from `describe`

```python
from uipath.platform.connections import ActivityMetadata, ActivityParameterLocationInfo
```

| `describe` field | `ActivityMetadata` field | Rule |
|---|---|---|
| `operation.path` | `object_path` | Direct |
| `operation.method` | `method_name` | Direct |
| Not surfaced | `content_type` | Use `"application/json"` for non-multipart |
| `parameters[type=query][].name` | `query_params` | Direct |
| `parameters[type=path][].name` | `path_params` | Direct |
| `parameters[type=header][].name` | `header_params` | Compact summary filters these; use raw cache, see Limitations |
| `parameters[type=multipart][].name` | `multipart_params` | Compact summary filters these; use raw cache, see Limitations |
| First segment of deduplicated `requestFields[].name` | `body_fields` | See Body-Field Reframing |
| Not surfaced | `json_body_section` | Multipart only; form-part holding JSON, default `"body"` |

For multipart, override `json_body_section` only when the connector expects another wrapper, such as `"RagRequest"`; it is ignored for non-multipart.

### Body-Field Reframing

Treat dotted `requestFields[].name` values such as `fields.project.key` or `attachment.image_url` as flat encodings of nested schemas, not routing keys. Set `body_fields` to the deduplicated top-level envelope whitelist, match top-level `activity_input.items()` keys, pre-nest the body, and pass it as one input value for the SDK to insert as-is.

For flat activities, use deduplicated top-level request-field names. For Jira curated activities whose fields begin with `fields.`, use `body_fields=["fields"]` and pass `{"fields": {...}}`; never use dotted input keys.

Run GenerateSchema before writing the literal:

```bash
uip is resources describe "uipath-atlassian-jira" "curated_create_issue" \
  --connection-id "<CONNECTION_ID>" --operation Create \
  -f fields.project.key=ENGCE -f fields.issuetype.id=3 \
  --action GenerateSchema --output json
```

Resolve reference fields such as `versions`, `components`, and assignee using `reference-resolution.md`; do not pass a name when the connector requires a reference ID. A Jira-style result is:

```python
JIRA_CREATE_ISSUE = ActivityMetadata(
    object_path="/curated_create_issue",
    method_name="POST",
    content_type="application/json",
    parameter_location_info=ActivityParameterLocationInfo(body_fields=["fields"]),
)
```

Pass nested input, not dotted keys:

```python
activity_input={
    "fields": {
        "project": {"key": "<PROJECT_KEY>"},
        "issuetype": {"id": "<ISSUE_TYPE_ID>"},
        "summary": "<SUMMARY>",
        "description": "<DESCRIPTION>",
    }
}
```

Do not set `body_fields` to dotted keys or pass dotted keys in `activity_input`; the SDK sends them as literal top-level JSON keys and curated activities reject them.

## Runtime Invocation

```python
from uipath.platform import UiPath
from uipath.platform.connections import ActivityMetadata, ActivityParameterLocationInfo

# Define the discovered ActivityMetadata literal inline.

def post_to_service(value: str) -> dict:
    sdk = UiPath()
    connection = sdk.connections.retrieve("<connection_id>")
    return sdk.connections.invoke_activity(
        activity_metadata=ACTIVITY_METADATA,
        connection_id=connection.id,
        activity_input={"<body_field>": value},
    )
```

- Instantiate `UiPath()` lazily inside the function that needs it.
- Get the connection `Id` from `uip is connections list`; use it in `retrieve()` and as `bindings.json` `ConnectionId.defaultValue`. A one-shot may pass it directly to `invoke_activity(connection_id="<connection_id>", ...)`.
- Put query, path, header, multipart, and body values in the single `activity_input` bucket. The SDK routes them by `parameter_location_info`; there are no `query=`, `path=`, or `header=` keyword arguments.
- `invoke_activity` calls `retrieve()` internally (`_connections_service.py:675`). Prefer explicit `retrieve()` because it provides a typed `Connection` for `metadata()` and `retrieve_token()`.
- The return value is `response.json()`, with keys matching `responseFields[].name`; connectors may wrap results in `Data` or `result`. Calls are auto-traced via `@traced`; see [tracing.md](tracing.md).
- `None` values and keys absent from `parameter_location_info` are silently skipped (`_connections_service.py:753-770`). Echo-check writes as described in Error Handling.

### Multipart

Compact `describe` omits `contentType`. For curated file activities such as Outlook `send-mail-v2` and Slack `send_files_to_channel` (sending `content_type="application/json"` to these returns `400 "Unable to parse multipart body"`), read the raw cache and set `content_type="multipart/form-data"`, `multipart_params`, and `json_body_section`:

```python
ActivityMetadata(
    object_path="/send-mail-v2", method_name="POST",
    content_type="multipart/form-data",
    parameter_location_info=ActivityParameterLocationInfo(
        multipart_params=["body", "file"], query_params=["saveAsDraft"]),
    json_body_section="body",
)
```

Each `multipart_params` value (`_connections_service.py:800-815`) may be `(filename, bytes, content_type)` for file uploads (preferred), raw `bytes` (defaulting to the field name and `application/octet-stream`), or a scalar string for a plain form field such as `saveAsDraft="true"`. The JSON body section, default `"body"`, is injected as `(filename="", json.dumps(body), "application/json")`.

### Async

Use the `_async` suffix and `await` with identical arguments inside `async def` framework nodes.

### Other `sdk.connections` Methods

| Method | Use | Cite |
|---|---|---|
| `list(name=, folder_path=, connector_key=, skip=, top=)` | Enumerate/filter connections when the key is unknown; sync and `list_async`; returns `List[Connection]` | `_connections_service.py:152` |
| `retrieve_token(key, token_type=ConnectionTokenType.DIRECT)` | Get a bearer token for the vendor’s own REST API, such as Microsoft Graph; sync and `retrieve_token_async`; returns `ConnectionToken{access_token,...}` | `_connections_service.py:368` |
| `retrieve_event_payload(event_args: EventArguments)` | Unwrap inbound payload for an IS trigger/webhook; sync and `retrieve_event_payload_async` | `_connections_service.py:421` |
| `metadata(element_instance_id, connector_key, tool_path, parameters=, schema_mode=True, max_jit_depth=5)` | Recover compact-describe omissions and JIT-cascaded custom fields; pass `parameters={...}` to auto-walk JIT URLs up to depth 5; sync and `metadata_async` | `_connections_service.py:79` |

Use `retrieve_token` as the supported escape hatch when a curated activity is missing, then call the vendor API. Do not call `/elements_/v3/…` directly.

## Framework Integration

Wrap `invoke_activity_async` in the framework’s tool primitive; only decoration/registration changes.

| Framework | Primitive | Reference |
|---|---|---|
| LangGraph | LLM judgment writes: node via conditional edge; reads: LLM-callable tool; call `invoke_activity_async` inside `async def node(state)` | [../frameworks/langgraph-integration.md](../frameworks/langgraph-integration.md) |
| LlamaIndex | `FunctionTool.from_defaults(fn=<RUNTIME_FN>)` | [../frameworks/llamaindex-integration.md](../frameworks/llamaindex-integration.md) |
| OpenAI Agents | `@function_tool` on `<RUNTIME_FN>` | [../frameworks/openai-agents-integration.md](../frameworks/openai-agents-integration.md) |

## `bindings.json` and Required Outputs

`uip codedagent init` writes `resources: []`; add a connection resource. Use the same connection id in code, `ConnectionId.defaultValue`, and binding `key`:

```jsonc
{
  "version": "2.0",
  "resources": [
    {
      "resource": "connection",
      "key": "<CONNECTION_KEY>",
      "value": { "ConnectionId": { "defaultValue": "<CONNECTION_ID>" } },
      "metadata": { "UseConnectionService": "True", "Connector": "", "BindingsVersion": "2.2" }
    }
  ]
}
```

The binding schema is `{ resource, key, value, metadata }`; use `resource`, never `type`. Set `key` to `<CONNECTION_KEY>` with no `<NAME>.<FOLDER>` suffix. Set `value.ConnectionId.defaultValue` to the connection id; use capital-C `ConnectionId`, not `name`, and do not add `folderPath`. Set `metadata.UseConnectionService: "True"`, `Connector: ""`, and `BindingsVersion: "2.2"`; `BindingsVersion: "2.2"` is independent of top-level `version: "2.0"`.

Read [`../lifecycle/bindings-reference.md`](../lifecycle/bindings-reference.md) § Connection for the full schema. `uip codedagent deploy` repackages this as `content/bindings_v2.json`; never hand-author that path.

Get the id from the `Id` field of `uip is connections list --output json`. Obtain `Connection.element_instance_id`, needed by `sdk.connections.metadata()`, only from the live `Connection` returned by `retrieve()`; never hardcode it.

Every coded IS agent ships:

| File | Must contain |
|---|---|
| `main.py` | Lazy `UiPath()`; inline `ActivityMetadata` literal; `retrieve("<connection_id>")` and `invoke_activity` |
| `bindings.json` | Connection resource; `key` and `ConnectionId.defaultValue` equal the same connection id; `UseConnectionService: "True"` |
| `uipath.json` | `functions`, `packOptions` |

## Error Handling

The SDK performs no preflight schema validation. It routes recognized keys, drops `None` and unknown keys, and sends the request; IS and vendor validation happen server-side.

| Outcome | Surface | Recovery |
|---|---|---|
| Misconfigured `ActivityMetadata`, where `content_type` is not `*/json` or `*/multipart*` | `ValueError("Unsupported content type: <ct>")` from `_connections_service.py:826` | Fix the literal; do not retry |
| IS schema rejection: missing `requestFields[].required: true` or wrong `dataType` | `RuntimeError` containing the IS-validator body, not a pre-HTTP `ValueError` | Rerun `describe`; add/fix the field or shape |
| Vendor rejection after IS accepts the shape | `RuntimeError` containing the vendor body | Parse the message and follow `agent-workflow.md § Error Recovery`; retry once with the fix |
| Silent rename/typo, including curated renames such as `customfield_10004` → `storyPoints_Customfield10004` | No exception; possible 2xx with the field missing | Echo-check by rereading the created resource and assert the sent field is present and equal; mismatch means switch curated↔raw or fix the key |

`BaseService.request` retries network/5xx failures with exponential backoff; exhausted failures propagate as `httpx.HTTPError` subclasses, not `RuntimeError`. For LLM-facing tools, return error strings rather than re-raising to keep the agent loop alive. Cap semantic retries at 2 per `agent-workflow.md § Error Recovery`; never retry the same query unchanged.

## Anti-patterns

1. Never hardcode `element_instance_id`; obtain it from the live `Connection.element_instance_id` after `retrieve()`.
2. Never hand-author `object_path`, `method_name`, or `body_fields`; source them from `uip is resources describe` and rerun after connector upgrades. Keep `ActivityMetadata` literals inline in `.py`; `pack` bundles them and mypy/pyright catch shape errors.
3. Never use typos or unknown `activity_input` keys; `_connections_service.py:753-770` silently drops them. Echo-check writes by reading the created object.
4. Never use `invoke_activity` to receive trigger payloads. IS-triggered jobs receive `EventArguments`; unwrap with `sdk.connections.retrieve_event_payload(event_args)` (`_connections_service.py:421`).
5. Never bypass `invoke_activity` with raw `httpx` to `/elements_/v3/…`; this loses retry, tracing, and S2S auth. Vendor API calls using `retrieve_token` are supported and distinct.
6. Never instantiate `UiPath()` at module scope; `uip codedagent init` and `pack` import modules to inspect entry points, so module-level construction fires HTTP during import. Instantiate lazily inside the needed function.

## Limitations of Compact `describe`

`uip is resources describe --output json` retains only `path|query` parameters. Header and multipart parameters remain in:

```text
~/.uipath/cache/integrationservice/<TENANT_ID>/<CONNECTOR_KEY>/<CONNECTION_ID>/<OBJECT>.schema.json
```

Read `data.metadata.method.<VERB>.parameters[]`; map `type=="multipart"` to `multipart_params` and `type=="header"` to `header_params`. For example, `uipath-salesforce-slack` (not `uipath-slack`, which is not a catalog key) / `send_files_to_channel` exposes `parameters[type=multipart][0].name = "file"` only in the cache.

When the cache is empty, use:

```python
md = sdk.connections.metadata(
    element_instance_id=connection.element_instance_id,
    connector_key="uipath-salesforce-slack",
    tool_path="/send_files_to_channel",
)
```

Pass `parameters={"<KEY>": "<VALUE>"}` only for connectors with cascading JIT custom fields.

### `-f` precondition

`uip is resources describe ... -f <KEY>=<VALUE>` requires `--connection-id` and `--operation`, and fails with `No api-type ObjectAction matched for fields [...]` when no matching api-type ObjectAction exists. Enumerate valid actions in the cached schema before retrying:

```bash
jq '.data.metadata.method.<VERB>.design.actions[] | select(.actionType=="api") | .name' <CACHED_DESCRIBE>
```

Use `.data.metadata.method.<VERB>.design.actions[]`, not `.connectorMethodInfo.design.actions[]`; the latter does not exist in the cache shape. Replace `<VERB>` with the operation’s HTTP method, such as `POST` for Create. The complete discovery flow is in `uipath-platform` `resources.md`.

## Reference

- [sdk-services.md](sdk-services.md) § Connections — service surface.
- [../frameworks/langgraph-integration.md](../frameworks/langgraph-integration.md), [llamaindex-integration.md](../frameworks/llamaindex-integration.md), [openai-agents-integration.md](../frameworks/openai-agents-integration.md) — framework wiring.
- [../lifecycle/bindings-reference.md](../lifecycle/bindings-reference.md) § Connection — full `bindings.json` schema.
- `uipath-platform` skill, `references/integration-service/` — `agent-workflow.md` + `resources.md` for discovery and parent-driven custom fields.
- [../../lowcode/capabilities/integration-service/integration-service.md](../../lowcode/capabilities/integration-service/integration-service.md) — low-code IS tool, a different artifact.