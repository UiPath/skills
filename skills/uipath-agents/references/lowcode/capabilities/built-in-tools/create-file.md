# Create File (`create-file`)

Built-in tool that writes a file and returns it as a `job-attachment`. Use it when the agent must produce a file (a report, a CSV, generated code) that another tool consumes or that the agent returns in a `job-attachment` output field.

For the built-in-tools capability overview, see [built-in-tools.md](built-in-tools.md).

## When to Use

- The agent's `outputSchema` declares a `job-attachment` field and the model must fill it with a file it authored. The tool is **required** for that unless another tool on the agent already returns a `job-attachment` (for example a coded-agent tool that generates a file): the model then reuses that tool's reference. Output-file verification at termination only runs when Create File is present.
- A downstream tool takes a `job-attachment` argument that the agent has to create at runtime, and no other tool produces it.
- **Autonomous agents only.** Conversational agents get no output-file enforcement: their output fields are filled by the extraction call after the loop, so a reference a tool returned has no path into them. Do not promise a produced-file output on a conversational agent.

## Pairing Pattern

One `job-attachment` output field on the agent ([../../agent-definition.md](../../agent-definition.md) § File Attachments) + one `create-file` tool resource + a system-prompt instruction naming the file and the output field ("save the summary with Create File as `<FILE_NAME>` and return the created file in `<OUTPUT_FIELD>`"). Guardrails can inspect the produced file at Agent · PostExecution — see [../guardrails/files-guide.md](../guardrails/files-guide.md) § Recipe 3.

## Resource Shape

**Path:** `<AgentName>/resources/CreateFile/resource.json`

```jsonc
{
  "$resourceType": "tool",
  "id": "<FRESH_UUID>",
  "referenceKey": null,
  "name": "Create File",
  "type": "internal",
  "description": "Create a file to pass to another tool or return as output.",
  "isEnabled": true,
  "inputSchema": {
    "type": "object",
    "properties": {
      "fileName": {
        "type": "string",
        "description": "Name of the file to create, including its extension (e.g., 'summary.md' or 'accounts.csv'). The extension sets the file type, so it must match the content."
      },
      "content": { "type": "string", "description": "Text content of the file." },
      // description depends on settings.mode — see the note below the schema
      "filePath": {
        "type": "string",
        "description": "Not available for this agent. Leave this empty and put the file's text in content."
      }
    },
    "required": ["fileName"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "file": { "$ref": "#/definitions/job-attachment", "description": "Reference to the created file" }
    },
    "required": ["file"],
    "definitions": {
      "job-attachment": {
        "type": "object",
        "properties": {
          "ID":       { "type": "string", "description": "Orchestrator attachment key" },
          "FullName": { "type": "string", "description": "File name" },
          "MimeType": { "type": "string", "description": "MIME type, e.g. \"application/pdf\", \"image/png\"" },
          "Metadata": {
            "type": "object",
            "description": "Dictionary<string, string> of metadata",
            "additionalProperties": { "type": "string" }
          }
        },
        "required": ["ID"],
        "x-uipath-resource-kind": "JobAttachment"
      }
    }
  },
  "settings": {},
  "guardrail": { "policies": [] },
  "argumentProperties": {},
  "properties": {
    "toolType": "create-file"
  }
}
```

Schema is canonical — copy verbatim. Only `id` (fresh UUID), optionally `description`, and the `filePath` description should differ. The `filePath` description depends on the agent's `settings.mode`, and Agent Builder swaps it when the mode changes — copy the variant that matches the agent:

| `settings.mode` | `filePath` description |
|---|---|
| `standard` | `Not available for this agent. Leave this empty and put the file's text in content.` |
| `advanced` | `Path of a file existing in your workspace (e.g., '/report.md'). Use this or content, not both.` |

## Walkthrough

1. **Declare the output field** as `$ref: "#/definitions/job-attachment"` in `outputSchema`, with the `job-attachment` definition in `outputSchema.definitions`. Mirror in `entry-points.json`.
2. **Author the tool resource** at `resources/CreateFile/resource.json` using the shape above. Generate a fresh UUID for `id`.
3. **Name the deliverable** in the system prompt: which file to produce (name and extension) and which output field it goes in. The runtime already adds a Files section to the system prompt that names the Create File tool and tells the model never to write a file reference itself, so do not repeat how to call the tool.
4. **Refresh** with `uip agent refresh "<AGENT_NAME>" --output json`, then **validate** with `uip agent validate "<AGENT_NAME>" --output json`.

## Gotchas

- `properties.toolType` MUST be exactly `"create-file"`. Anything else is silently ignored.
- If `uip agent tool list` on an existing agent and the Studio Web tool picker offer no Create File tool, output files are not available on that tenant — return the content as text instead. If the tool is already on the agent and the tenant has it disabled, the run **fails at startup** with `INVALID_TOOL_CONFIG` (`The Create File tool is not supported in this environment. Remove it from the agent to run it.`): remove the `resources/CreateFile` resource, do not just stop adding it.
- The tool writes text content only (`filePath` is reserved for advanced agents with a workspace); binary deliverables are out of scope unless there is no tool that produces that binary output.
- A guardrail that must check the produced file goes at **Agent** scope with `appliesTo: "Files"`, not Llm scope: at Llm scope the file is still the plain-text `content` argument. See [../guardrails/files-guide.md](../guardrails/files-guide.md) § Recipe 3.

## References

- [built-in-tools.md](built-in-tools.md) — capability overview
- [analyze-attachments.md](analyze-attachments.md) — the reading counterpart
- [../../agent-definition.md](../../agent-definition.md) § File Attachments — `job-attachment` schema
- [../guardrails/files-guide.md](../guardrails/files-guide.md) — guardrails on produced files
