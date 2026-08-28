# Analyze Files (`analyze-attachments`)

Built-in tool that uses an LLM to analyze one or more `job-attachment` files. It is the only way for a low-code agent to read attachment contents at runtime. Use it to extract, synthesize, summarize, classify, or answer questions about runtime files.

For the built-in-tools capability overview, see [built-in-tools.md](built-in-tools.md).

## When to Use

- The agent has a `job-attachment` input field or receives attachments inside a tool call and must read their contents.
- The agent must summarize, classify, or extract from runtime PDFs, images, or documents.

## Pairing Pattern

Use one `job-attachment` input field and one `analyze-attachments` tool resource. Reference the input metadata in the user message with `{{input.<field>}}`, then pass the same attachment in `attachments[]` with an `analysisTask`.

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

4. **Refresh** with `uip agent refresh "<AGENT_NAME>" --output json`. Regenerates `entry-points.json` and `bindings_v2.json`.
5. **Validate** with `uip agent validate "<AGENT_NAME>" --output json` (read-only). Confirm `Validated`.
6. **Bundle and upload** with `uip solution bundle` then `uip solution upload --output json` (with user consent).
7. **Test** from Studio Web or via Orchestrator job invocation — `uip` CLI cannot supply attachments at run time.

## Gotchas

- `properties.toolType` MUST be exactly `"analyze-attachments"` (kebab-lowercase). Anything else is silently ignored.
- Put the `definitions.job-attachment` block inside the tool's `inputSchema`, not at the agent root. Each schema (agent input, agent output, tool input) carries its own copy.
- `{{input.<field>}}` only surfaces metadata; without this tool the agent cannot read file contents. See [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) Critical Rule 17.
- Agents can return a `job-attachment` from `outputSchema` (for example, a generated file), but `analyze-attachments` only reads and does not produce attachments.

## References

- [built-in-tools.md](built-in-tools.md) — capability overview
- [../../agent-definition.md](../../agent-definition.md) § File Attachments — `job-attachment` schema
- [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) Critical Rules 17–20