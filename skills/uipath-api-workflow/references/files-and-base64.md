# Files & Base64 in API Workflows

How API workflows represent files, use **File to Base64** / **Base64 to File**, embed file content in requests or Responses, and run file workflows from the CLI.

## 1. Files are references, not bytes

A workflow file is a `JobAttachment` pointing to an Orchestrator blob:

```json
{
  "ID": "6f1c0d2e-8a1b-4c3d-9e0f-123456789abc",
  "FullName": "invoice.pdf",
  "MimeType": "application/pdf",
  "Metadata": { "Size": 48213, "Encoding": "byte-array" }
}
```

| Field | Meaning |
|---|---|
| `ID` | Orchestrator attachment key (GUID) |
| `FullName` | File name with extension |
| `MimeType` | Content type |
| `Metadata.Size` | Byte length, when known |
| `Metadata.Encoding` | `"byte-array"` (binary, default) or `"base64"` (blob content is base64 text); a tag only—reading does not convert content |

A file input declared in `input.schema` with `"$ref": "#/definitions/job-attachment"` and `x-uipath-resource-kind: "JobAttachment"` arrives as this object: `$workflow.input.document.FullName` works, but there is no `.content`. Bytes never enter `$context`, and file reads/writes use Orchestrator blob storage, so a signed-in session is required.

## 2. File activities

Both activities are ordinary `run.script` tasks identified by `metadata.activityType` and their `$helpers.file.*` call. The script must contain exactly one `return` expression. Studio Web parses that call to populate its property panel and rebuilds the script on save; unrecognized content is silently dropped.

Surviving shapes:

- File to Base64: `return { output: await $helpers.file.fileToBase64(<ref>) }` — exactly one argument.
- Base64 to File: `return { output: await $helpers.file.base64ToFile({ base64: <ref or string>, fileName?: <expr>, mimeType?: <expr> }) }` — exactly one object argument and only those keys.

Do not use statements before or after `return`, a second argument, or extra option keys. `uip api-workflow validate` warns about extra statements (`rebuilds the script … and drops the rest, which breaks the workflow`) but reports `Valid` without warning for an extra argument or option key; check those shapes manually. Pre-process values in a preceding JavaScript activity and pass its output as the single argument.

### File to Base64 (`FileToBase64`)

`await $helpers.file.fileToBase64(<file ref>)` returns a **new** reference whose blob is base64 text: `<baseName>.base64`, `text/plain`, `Metadata.Encoding: "base64"`. It is idempotent for an already-base64 reference. A string input is a validation error.

```json
{
  "FileToBase64_1": {
    "run": {
      "script": {
        "code": "return { output: await $helpers.file.fileToBase64($workflow.input.document) }",
        "language": "javascript",
        "arguments": "${{ \"$context\": $context, \"$workflow\": $workflow, \"$input\": $input }}"
      }
    },
    "export": { "as": "{ ...$context, outputs: { ...$context?.outputs, \"FileToBase64_1\": $output } }" },
    "metadata": { "activityType": "FileToBase64", "displayName": "File to Base64", "fullName": "FileToBase64", "icon": "sw:convert-file-to-base64" }
  }
}
```

The downstream value is `$context.outputs.FileToBase64_1.output` (a `JobAttachment`).

### Base64 to File (`Base64ToFile`)

`await $helpers.file.base64ToFile({ base64, fileName?, mimeType? })` returns a **new binary** reference. `base64` may be a base64 file reference from File to Base64 or a raw base64 string from an API response or variable.

For a string input, `fileName` and `mimeType` apply; if omitted, MIME is sniffed, the name is GUID-based, and the extension comes from the MIME type. For a reference input they are ignored: the engine strips `.base64` and sniffs the type. Plain text has no signature, so a `.txt` reference can return extension-less as `application/octet-stream`. A non-base64-tagged binary reference is returned unchanged; chaining Base64 to File on a raw file is a no-op. Omit unset optional keys—`fileName: ` with no value is a syntax error.

```json
{
  "Base64ToFile_1": {
    "run": {
      "script": {
        "code": "return { output: await $helpers.file.base64ToFile({ base64: $context.outputs.HTTP_Request_1.content.data, fileName: 'invoice.pdf', mimeType: 'application/pdf' }) }",
        "language": "javascript",
        "arguments": "${{ \"$context\": $context, \"$workflow\": $workflow, \"$input\": $input }}"
      }
    },
    "export": { "as": "{ ...$context, outputs: { ...$context?.outputs, \"Base64ToFile_1\": $output } }" },
    "metadata": { "activityType": "Base64ToFile", "displayName": "Base64 to File", "fullName": "Base64ToFile", "icon": "sw:convert-base64-to-file" }
  }
}
```

A disabled activity gets `"if": "${false}"` on its task, like any other.

## 3. Put file content in a request or Response

`fileToBase64` returns a file, not a string. To send its base64 text, call `serializeData()` inline in an HTTP body or Response:

```json
"bodyParameters": { "body": "${{ name: $workflow.input.document.FullName, content: $context.outputs.FileToBase64_1.output.serializeData() }}" }
```

```json
"response": "${{ encoded: $context.outputs.FileToBase64_1.output.serializeData() }}"
```

`serializeData()` is synchronous and returns a deferred-read marker (`{ "__uipathFileRead": { "ref": … } }`), which the engine resolves when sending the request or returning the Response. Use it only inline in an HTTP body or Response field. Do not assign it to a variable, return it from a script, or process it; that preserves the marker.

In a nested JSON body, only a base64 reference works. A marker on a binary reference fails at send time with `Raw bytes cannot be embedded in JSON — convert the file with File to Base64 first`; a bare reference fails with `A bare file reference cannot be embedded in a nested field`. Thus `content: $workflow.input.document.serializeData()` is wrong, while `content: $context.outputs.FileToBase64_1.output.serializeData()` is right.

To send binary content as-is, make the bare reference the entire HTTP body; its `MimeType` becomes `Content-Type`, with no `serializeData()`. In a Response, markers resolve anywhere and bare references remain references.

## 4. Complete round trip

[assets/templates/file-base64-roundtrip-example.json](../assets/templates/file-base64-roundtrip-example.json): `document` file input → `FileToBase64_1` → `Base64ToFile_1` → `Response_1` returning both references. The typical production chain is `File to Base64 → HTTP POST (body uses .serializeData()) → Base64 to File (vendor's base64 response string, with fileName/mimeType) → Response`.

## 5. Run a workflow that uses files

<!--skill-flavor:file-inputs-cli:start-->
Run `uip login` once, then run the workflow with a signed-in session. `uip api-workflow run --no-auth` refuses workflows calling `$helpers.file.*` before the engine starts and refuses `--input-file` / `--output-dir`. Rule 21 still applies: ask before running.

```bash
uip login                                  # once
uip api-workflow run ./MyApiProject/Workflow.json \
  --input-file document=./invoice.pdf \    # upload → $workflow.input.document (repeatable)
  --output-dir ./out \                     # download every reference in the output
  --output json
```

- `--input-file <name>=<path>`: upload the local file, infer MIME from its extension, and place the reference under `<name>` in the input—exactly what Studio Web's run panel produces.
- `--output-dir <dir>`: download every output `JobAttachment` into `<dir>`; the printed reference gains `LocalPath`. Same-named blobs receive an `-<Id>` suffix.
- `--folder-key <guid>`: use when the tenant's Attachments API requires a folder.
- The CLI PascalCases printed keys: `ID` → `Id`, `encoded` → `Encoded`.

Example output:

```json
{
  "Result": "Success",
  "Code": "WorkflowRun",
  "Data": {
    "Encoded": { "Id": "…", "FullName": "hello.base64", "MimeType": "text/plain", "Metadata": { "Size": 72, "Encoding": "base64" }, "LocalPath": "/abs/out/hello.base64" },
    "Decoded": { "Id": "…", "FullName": "hello", "MimeType": "application/octet-stream", "Metadata": { "Size": 54, "Encoding": "byte-array" }, "LocalPath": "/abs/out/hello" }
  }
}
```

`uip api-workflow validate` supports these activities offline: it accepts `FileToBase64` / `Base64ToFile` and rejects either activity type when its script does not call the corresponding `$helpers.file.*` function.
<!--skill-flavor:file-inputs-cli:end-->

## 6. Limits and gotchas

- **Size:** references have no practical size cap. A reference with declared `Metadata.Size` above 1 MB, or with no declared size (common for job inputs), streams with bounded memory at any size. Only in-memory inputs are capped at 50 MB per conversion: a raw base64 string or a reference small enough to be buffered.
- **Namespace:** `$helpers.fileToBase64` (without `.file.`) fails with `is not a function` and fails `validate`.
- **Invalid base64:** `data:…;base64,` prefixes and whitespace/line breaks are stripped and tolerated. Rejected with `The provided value is not a valid base64 string: base64ToFile`: URL-safe `-` / `_`, other non-base64 characters, bad padding, and an empty string. The suffix is always the literal helper name `base64ToFile`, never the task key; grep logs for the message text, not `Base64ToFile_1`.
- **Names:** `fileName` / `mimeType` never rename a reference input; a decoded text file loses its extension.
- **Preview:** in Studio Web, both activities require `FE.EnableBase64Activities` and are marked "in preview".

Pitfalls with symptoms and fixes: [troubleshooting.md](troubleshooting.md#file--base64-pitfalls).