# Client-Side Tool Capability

> **Conversational agents only.** Client-side tools require a surface that implements the UiPath conversation TypeScript SDK protocol. Autonomous agents have no client surface at runtime, so client-side tools cannot execute — do not add them to autonomous agents.

Tools the agent **calls** but the **client executes**. Per the [product documentation](https://docs.uipath.com/agents/automation-cloud/latest/user-guide/tools-client-side), the runtime pauses, delegates the tool call to the client surface, and resumes once the client returns a result.

## When to Use

Per the docs, when the agent needs data or capabilities that only exist on the client:

- **Access client-local data** — host-application state the server cannot see, such as a task board, form fields, or session state.
- **Trigger client-side actions** — navigate to a page, open a dialog, create a record in the local UI.
- **Leverage client-specific capabilities** — clipboard, local storage, geolocation.

## Key Difference from Server-Side Tools

Execution belongs to the surface, not the runtime. The docs state that a surface must support client-side tool handling and **register a handler for each tool — a tool without one returns an error to the agent.**

Pre-built surfaces (Instance Management, iFrame embedding) render a form from the `outputSchema` for the user to fill in. Custom surfaces built on the UiPath TypeScript SDK can run custom handlers.

## Agent-Level Resource Shape

The agent designer has a first-class flow — **Add tool → Client-side tools**, then tool name, description, input schema, and output schema. Prefer it when working in the UI. When editing project files directly, write the resource yourself.

**Path:** `<AgentName>/resources/<ToolName>/resource.json`, mirrored into `<AgentName>/.agent-builder/agent.json` under `resources[]`.

```jsonc
{
  "$resourceType": "tool",
  "id": "<uuid>",                     // stable; generate once
  "referenceKey": null,
  "name": "askApproval",              // per docs: must begin with a letter or underscore;
                                      // letters, digits, spaces, and underscores only
  "type": "clientSide",
  "description": "...",               // per docs: guides the agent's decision to call the tool
  "location": "solution",
  "isEnabled": true,
  "inputSchema":  { "type": "object", "properties": { }, "required": [ ] },
  "outputSchema": { "type": "object", "properties": { }, "required": [ ] },
  "settings": {},
  "guardrail": { "policies": [] },
  "argumentProperties": {},
  "properties": {
    "folderPath": "solution_folder",
    "requireConversationalConfirmation": false
  }
}
```

Field requirements:

| Field | Requirement |
|---|---|
| `type` | Exactly `"clientSide"` — lowercase `c` |
| `referenceKey` | `null`. The schema declares it as null; unlike other tool types it references no cloud resource |
| `location` | `"solution"` |
| `properties.folderPath` | `"solution_folder"`. Validation reports *"solution tools must use folderPath"* otherwise |
| `settings`, `guardrail`, `inputSchema`, `outputSchema` | Declared without `.optional()` — include all four, using an empty `policies` array when no guardrails apply |

Setting `properties.requireConversationalConfirmation` to `true` corresponds to the designer's **Require confirmation** option. Per the docs the agent then pauses before executing and shows the user the proposed **input parameters**, which the user can approve, modify, or reject. Tool-call confirmation is for reviewing the agent's inputs and is distinct from client-side tools, which collect the output.

## Input and Output Schemas

Both are required and both are JSON Schema objects. Quoting the docs, they define the contract between agent and client:

| Schema | Role |
|---|---|
| `inputSchema` | What the **agent sends** to the client when it calls the tool |
| `outputSchema` | What the **client returns** after executing it |

On pre-built surfaces the `outputSchema` is also the UI contract — the form the user fills in is generated from it. Design it accordingly.

From the docs, a tool that reads tasks from a project board:

```json
{
  "type": "object",
  "properties": {
    "boardId": { "type": "string", "description": "The ID of the task board to read from" },
    "status": {
      "type": "string",
      "enum": ["todo", "in-progress", "done"],
      "description": "Filter tasks by status"
    }
  },
  "required": ["boardId"]
}
```

Standard JSON Schema keywords (`title`, `description`, `enum`, `oneOf`, `default`, `format`, `required`, etc.) are supported. Useful when the `outputSchema` will be filled in by a person — e.g. the default form experience in out-of-the-box UiPath chat UIs, including iFrame embedding.

## Walkthrough

```bash
# 1. Scaffold solution + conversational agent per
#    project-lifecycle.md § End-to-End Example (pass --conversational;
#    autonomous agents have no client surface).
#    See ../../project-lifecycle.md#end-to-end-example--new-standalone-agent

# 2. Write <AgentName>/resources/<ToolName>/resource.json
#    using the shape above.

# 3. Reference the tool in the system prompt as @{tools.<ToolName>} with a
#    matching expression contentToken. See ../../prompting/agent-prompting-guide.md.

# 4. Refresh — regenerates entry-points.json and bindings_v2.json.
uip agent refresh "<AgentName>" --output json

# 5. Validate — strict, read-only. Confirm Status: "Valid".
uip agent validate "<AgentName>" --output json
```

## Runtime Sequence

From the docs:

1. The agent decides to use the tool, based on conversation context and the tool description.
2. If confirmations are enabled, the user reviews and approves the proposed input.
3. The runtime sends the tool call — name, input values, and both schemas — to the client surface.
4. The client surface executes its registered handler.
5. The client returns the result.
6. The agent receives the result and continues reasoning.

## Gotchas

- `"ClientSide"` (capital C) is rejected. The Python models spell it that way and tolerate either via a case-insensitive enum, but the zod schemas do not — the solution packager fails with an `invalid_union` / `No matching discriminator` error that names neither the offending value nor the legal set.
- If validation looks unexpectedly clean, check `type` first. An unrecognised discriminator skips the client-side checks entirely, so a badly-typed resource can report *fewer* errors than a nearly-correct one.
- The form generated on pre-built surfaces renders with Apollo components and inherits the host app's theme. It exposes no class, theme, or slot override, so its appearance cannot be customised from the agent side.
- Per the docs, execution depends on the client surface's availability — if the client disconnects mid-execution, the tool call may fail.

## References

- [Client-side tools](https://docs.uipath.com/agents/automation-cloud/latest/user-guide/tools-client-side) — product documentation, source of truth
- [TypeScript SDK — client-side tools](https://uipath.github.io/uipath-typescript/conversational-agent/#client-side-tools) — client surface implementation (registering handlers, executing tool calls)
- [../../prompting/agent-prompting-guide.md](../../prompting/agent-prompting-guide.md) — writing the Tools slot
