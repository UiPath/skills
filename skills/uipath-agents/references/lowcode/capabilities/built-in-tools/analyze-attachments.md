# Analyze Files (`analyze-attachments`)

Built-in tool that analyzes one or more `job-attachment` files with an LLM. Use it to extract, synthesize, or answer queries about file contents — the only way for a low-code agent to read attachment contents at runtime.

For the built-in-tools capability overview, see [built-in-tools.md](built-in-tools.md).

## When to Use

- Agent has a `job-attachment` input field (or receives attachments inside a tool call) and must read contents
- Agent must summarize, classify, or extract from PDFs, images, documents passed at runtime

## Pairing Pattern

Typical low-code shape: one `job-attachment` input field on the agent + one `analyze-attachments` tool resource. The user message references the attachment metadata with `{{input.<field>}}`; the agent calls `analyze-attachments`, passing the same attachment in `attachments[]` along with an `analysisTask`.

## Resource Shape

**Path:** `<AgentName>/resources/AnalyzeFiles/resource.json`

```jsonc
{
  "$resourceType": "tool",
  "id": "<FRESH_UUID>",
  "referenceKey": null,
  "name": "Analyze Files",
  "type": "internal",
  "description": "Analyze one or more files with an LLM to extract, synthesize, or answer queries about their content.",
  "isEnabled": true,
  "inputSchema": {
    "type": "object",
    "properties": {
      "attachments": {
        "type": "array",
        "items": { "$ref": "#/definitions/job-attachment" },
        "description": "Array of files, documents, images, or other attachments to process"
      },
      "analysisTask": {
        "type": "string",
        "description": "The task, question, or instruction for processing the files (e.g., 'summarize this document', 'extract key points', 'what is in this image')"
      }
    },
    "required": ["attachments", "analysisTask"],
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
  "outputSchema": {
    "type": "object",
    "properties": {
      "analysis": {
        "type": "string",
        "description": "Analysis result of the attachments (analysis, summary, extracted information, etc.)"
      }
    },
    "required": ["analysis"]
  },
  "settings": {},
  "guardrail": { "policies": [] },
  "argumentProperties": {},
  "properties": {
    "toolType": "analyze-attachments"
  }
}
```

Schema is canonical — copy verbatim. Only `id` (fresh UUID) and optionally `description` should differ.

## Walkthrough

1. **Add a file input field on the agent.** See [../../agent-definition.md](../../agent-definition.md) § Add a File Input Field. Mirror in `entry-points.json`.
2. **Author the tool resource** at `resources/AnalyzeFiles/resource.json` using the shape above. Generate a fresh UUID for `id`.
3. **Reference the attachment in the user message** so the agent sees its metadata:

   ```jsonc
   {
     "role": "user",
     "content": "Analyze the contents of the provided file and give a summary.\n\n{{input.fileIn}}",
     "contentTokens": [
       { "type": "simpleText", "rawString": "Analyze the contents of the provided file and give a summary.\n\n" },
       { "type": "variable",   "rawString": "input.fileIn" }
     ]
   }
   ```

4. **Validate** with `uip agent validate "<AGENT_NAME>" --output json`. Confirm `MigrationApplied`, `StorageVersion`, `Validated`.
5. **Bundle and upload** with `uip solution bundle` then `uip solution upload --output json` (with user consent).
6. **Test** from Studio Web or via Orchestrator job invocation — `uip` CLI cannot supply attachments at run time.

## Gotchas

- `properties.toolType` MUST be exactly `"analyze-attachments"` (kebab-lowercase). Anything else is silently ignored.
- The `definitions.job-attachment` block belongs inside the tool's `inputSchema`, not at the agent root. Each schema (agent input, agent output, tool input) carries its own copy.
- `{{input.<field>}}` only surfaces metadata; without this tool the agent has no way to read file contents. See [../../critical-rules.md](../../critical-rules.md) Critical Rule 18.
- Agents can return a `job-attachment` from `outputSchema` (e.g. a generated file), but `analyze-attachments` itself only reads — it does not produce attachments.

## References

- [built-in-tools.md](built-in-tools.md) — capability overview
- [../../agent-definition.md](../../agent-definition.md) § File Attachments — `job-attachment` schema
- [../../critical-rules.md](../../critical-rules.md) Critical Rules 18–21
